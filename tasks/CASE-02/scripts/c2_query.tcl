# CASE-02 query instance (protocol v0.3 section 6.4). Copied and adapted from tasks/CASE-01/diag/scripts/diag_query.tcl
# (rules/copied_from.tsv, rules/diff/c2_query.tcl.diff). Run by run_query.py as:
#   sta -no_init -no_splash -exit c2_query.tcl
# Env: everything the driver needs (TOP NETLIST T_NS CLOAD_PF SCENESET OUTDIR CASE_DIR SDC_FILE SKY130_KIT), plus
#      DRIVER (scripts/sta_run_case02.tcl), QUERY_FILE, QUERY_MODE (query | whatif), RULES_DIR, CASE02_NONCE,
#      CASE02_QUERY_SECONDS, CASE02_COMMAND_LIMIT, CALL_LOG (per-call record, TSV), STA_LOG (this process's stdout file).
#
# 1) Rebuild the analysis context of the chosen version by sourcing the CASE-02 driver (it reads SDC_FILE).
#    It writes the records to $OUTDIR; run_query.py compares them with the formal run of the same version.
source $::env(DRIVER)

# 2) Read the command lists while file access is still available in this (master) interpreter.
proc c2_words {name} {
  set f [open [file join $::env(RULES_DIR) $name] r]
  set words {}
  foreach line [split [read $f] "\n"] {
    set line [string trim $line]
    if {$line ne "" && ![string match "#*" $line]} { lappend words $line }
  }
  close $f
  return $words
}
set ::c2_allow [c2_words allow_query.txt]
set ::c2_whatif [c2_words allow_whatif.txt]
set ::c2_setup [c2_words setup_commands.txt]
set qf [open $::env(QUERY_FILE) r]
fconfigure $qf -encoding utf-8
set c2_query [read $qf]
close $qf
# Every marker carries a per-run random nonce, so a query cannot forge them with puts.
set ::M "CASE02-$::env(CASE02_NONCE)"
set ::c2_calllog [open $::env(CALL_LOG) a]
fconfigure $::c2_calllog -encoding utf-8
set ::c2_seq 0
set ::c2_top 0

# 3) Per-call wrapper (runs in the master interpreter). Every actual STA call is recorded in CALL_LOG with the byte
#    position of this process's stdout file before and after it (stdout is flushed on both sides, so the
#    positions bound the call's own output), the decision taken for it, and its status. Output redirection is
#    refused. Setup commands are skipped per call; create_clock is skipped only when its actual -period equals T.
proc c2_outpos {} {
  flush stdout
  return [file size $::env(STA_LOG)]
}
proc c2_oneline {s} {
  return [string map {"\t" " " "\n" " | "} $s]
}
proc c2_escape {s} {
  # reversible escaping for TSV fields (R6 M3: full argv and return values are recorded, not a preview)
  return [string map {"\\" "\\\\" "\t" "\\t" "\n" "\\n" "\r" "\\r"} $s]
}
proc c2_scene_of {args} {
  set i [lsearch -exact $args -scene]
  if {$i < 0} { set i [lsearch -exact $args -scenes] }
  if {$i >= 0 && $i + 1 < [llength $args]} { return [lindex $args [expr {$i + 1}]] }
  return "-"
}
proc c2_decide {cmd args} {
  if {$cmd in $::c2_setup} {
    if {$cmd ne "create_clock"} { return skip }
    set i [lsearch -exact $args -period]
    if {$i >= 0 && $i + 1 < [llength $args]} {
      set p [lindex $args [expr {$i + 1}]]
      if {[string is double -strict $p] && $p == $::env(T_NS)} { return skip }
    }
    return whatif
  }
  if {$cmd in $::c2_whatif} { return whatif }
  return run
}
proc c2_call {cmd args} {
  foreach a $args {
    if {[string match ">*" $a]} { return -code error "CASE02: output redirection is disabled" }
  }
  set decision [c2_decide $cmd {*}$args]
  incr ::c2_seq
  set seq $::c2_seq
  set start [c2_outpos]
  set argtext [join $args " "]
  set preview [c2_oneline [string range $argtext 0 79]]
  set crc [format %08x [zlib crc32 [encoding convertto utf-8 $argtext]]]
  puts $::c2_calllog "START\t$seq\t$::c2_top\t$cmd\t$crc\t$preview\t$decision\t[c2_scene_of {*}$args]\t$start"
  set esc {}
  foreach a $args { lappend esc [c2_escape $a] }
  puts $::c2_calllog "ARGS\t$seq\t[join $esc "\t"]"
  flush $::c2_calllog
  if {$decision eq "skip"} {
    puts "$::M-CODE: SETUP_SKIPPED $cmd"
    set end [c2_outpos]
    puts $::c2_calllog "END\t$seq\tskipped\t\t$end"
    flush $::c2_calllog
    return ""
  }
  if {$decision eq "whatif" && $::env(QUERY_MODE) ne "whatif"} {
    set end [c2_outpos]
    puts $::c2_calllog "END\t$seq\terror\tCASE02: $cmd changes the analysis model; this instance runs in query mode\t$end"
    flush $::c2_calllog
    return -code error "CASE02: $cmd changes the analysis model; it runs only in a separate comparison instance"
  }
  # no {*} here: OpenSTA's warning helper parses the calling command line as a Tcl list
  set code [catch {uplevel #0 [linsert $args 0 $cmd]} out opts]
  set end [c2_outpos]
  if {$code} {
    puts $::c2_calllog "END\t$seq\terror\t[c2_oneline $out]\t$end"
  } else {
    # the return value (OpenSTA object handles or text) is recorded too: a query may print it later through puts,
    # outside this call's own stdout range (R6 M3)
    if {[catch {llength $out} n]} { set n -1 }
    set rtype [expr {$n > 1 || ($n == 1 && [string match "_sta_*" [lindex $out 0]]) ? "list" : ($n == 0 ? "empty" : "string")}]
    set rlen [expr {$rtype eq "string" ? [string length $out] : $n}]
    puts $::c2_calllog "RET\t$seq\t$rtype\t$rlen\t[c2_escape [string range $out 0 199]]"
    puts $::c2_calllog "END\t$seq\tok\t\t$end"
  }
  flush $::c2_calllog
  return -options $opts $out
}

# 4) The safe interpreter: no exec/open/file/socket/cd/source/load; it sees only the listed STA commands, all
#    through c2_call. In whatif mode the model-changing commands are aliased too; in query mode they are absent
#    except that setup commands (create_clock among them) are always routed through c2_call for the skip rule.
set q [interp create -safe]
interp share {} stdout $q
set c2_visible $::c2_allow
foreach c $::c2_setup { lappend c2_visible $c }
if {$::env(QUERY_MODE) eq "whatif"} { foreach c $::c2_whatif { lappend c2_visible $c } }
foreach c [lsort -unique $c2_visible] { interp alias $q $c {} c2_call $c }
# limits on the safe interpreter itself (loops written in the query); STA commands run in the master and are
# bounded by run_query.py's wall-clock limit on the whole process
interp limit $q time -seconds [expr {[clock seconds] + $::env(CASE02_QUERY_SECONDS)}]
interp limit $q command -value $::env(CASE02_COMMAND_LIMIT)

# 5) Like commands typed one by one into an STA shell: each complete top-level command runs on its own, and an
#    error in one does not stop the next. "$M-CMD:" echoes the first line of each command before its output.
puts "=== $::M QUERY BEGIN ($::env(QUERY_MODE)) ==="
flush stdout
set errors 0
set cmd ""
foreach line [split $c2_query "\n"] {
  append cmd $line "\n"
  if {![info complete $cmd]} { continue }
  if {[string trim $cmd] ne "" && ![string match "#*" [string trim $cmd]]} {
    incr ::c2_top
    puts "$::M-CMD: [lindex [split [string trim $cmd] "\n"] 0]"
    flush stdout
    if {[catch {interp eval $q $cmd} res]} {
      incr errors
      puts "$::M-ERROR: $res"
      if {[string match "*limit exceeded*" $res]} {
        # a limit stays exceeded for the rest of the run: say so once instead of failing every later command
        puts "$::M-ERROR: remaining commands not run, interpreter $res"
        flush stdout
        set cmd ""
        break
      }
    } elseif {$res ne ""} {
      puts $res
    }
    flush stdout
  }
  set cmd ""
}
if {[string trim $cmd] ne ""} {
  incr errors
  puts "$::M-ERROR: incomplete command at end of query: [string trim $cmd]"
}
puts "=== $::M QUERY END rc=[expr {$errors ? 1 : 0}] ==="
flush stdout
close $::c2_calllog
