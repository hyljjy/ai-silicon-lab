# CASE-01 diag query (protocol v0.5 sections 7.1 and 8). Run by run_query.py as:
#   sta -no_init -no_splash -exit diag_query.tcl
# Env: everything the frozen sta_run.tcl needs (TOP NETLIST T_NS CLOAD_PF SCENESET OUTDIR CASE_DIR SKY130_KIT),
#      plus QUERY_FILE, QUERY_MODE (query | whatif), RULES_DIR, CASE01_NONCE, CASE01_QUERY_SECONDS.
#
# 1) Rebuild the F1 analysis context by sourcing F1's own frozen sta_run.tcl (CASE_DIR = the F1 run's inputs/).
#    It writes the F1 records to $OUTDIR; run_query.py compares them byte for byte with F1 before using any output.
source [file join $::env(CASE_DIR) scripts sta_run.tcl]

# 2) Read the command lists while file access is still available in this (master) interpreter.
proc case01_words {name} {
  set f [open [file join $::env(RULES_DIR) $name] r]
  set words {}
  foreach line [split [read $f] "\n"] {
    set line [string trim $line]
    if {$line ne "" && ![string match "#*" $line]} { lappend words $line }
  }
  close $f
  return $words
}
set case01_allow [case01_words allow_query.txt]
if {$::env(QUERY_MODE) eq "whatif"} { lappend case01_allow {*}[case01_words allow_whatif.txt] }
set case01_setup [case01_words setup_commands.txt]
set qf [open $::env(QUERY_FILE) r]
fconfigure $qf -encoding utf-8
set case01_query [read $qf]
close $qf
# Every marker carries a per-run random nonce, so a query cannot forge them with puts.
set M "CASE01-$::env(CASE01_NONCE)"

# 3) Run the query in a safe interpreter: it has no exec/open/file/socket/cd/source/load, and it sees only the
#    allow-listed STA commands, through a wrapper that refuses output redirection (> file, >> file).
proc case01_call {cmd args} {
  foreach a $args {
    if {[string match ">*" $a]} { return -code error "CASE01: output redirection is disabled" }
  }
  # no {*} here: OpenSTA's warning helper parses the calling command line as a Tcl list
  return [uplevel #0 [linsert $args 0 $cmd]]
}
proc case01_setup_stub {cmd args} {
  global M
  puts "$M-CODE: SETUP_SKIPPED $cmd"
  return ""
}
set q [interp create -safe]
interp share {} stdout $q
# setup stubs first, then the allow list: in whatif mode an allowed command (create_clock) replaces its stub
foreach c $case01_setup { interp alias $q $c {} case01_setup_stub $c }
foreach c $case01_allow { interp alias $q $c {} case01_call $c }
# limits on the safe interpreter itself (loops written in the query); STA commands run in the master and are
# bounded by run_query.py's wall-clock limit on the whole process
interp limit $q time -seconds [expr {[clock seconds] + $::env(CASE01_QUERY_SECONDS)}]
interp limit $q command -value 1000000

# Like commands typed one by one into an STA shell: each complete top-level command runs on its own, and an error
# in one does not stop the next. "$M-CMD:" echoes the first line of each command before its output.
puts "=== $M QUERY BEGIN ($::env(QUERY_MODE)) ==="
flush stdout
set errors 0
set cmd ""
foreach line [split $case01_query "\n"] {
  append cmd $line "\n"
  if {![info complete $cmd]} { continue }
  if {[string trim $cmd] ne "" && ![string match "#*" [string trim $cmd]]} {
    puts "$M-CMD: [lindex [split [string trim $cmd] "\n"] 0]"
    flush stdout
    if {[catch {interp eval $q $cmd} res]} {
      incr errors
      puts "$M-ERROR: $res"
      if {[string match "*limit exceeded*" $res]} {
        # a limit stays exceeded for the rest of the run: say so once instead of failing every later command
        puts "$M-ERROR: remaining commands not run, interpreter $res"
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
  puts "$M-ERROR: incomplete command at end of query: [string trim $cmd]"
}
puts "=== $M QUERY END rc=[expr {$errors ? 1 : 0}] ==="
flush stdout
