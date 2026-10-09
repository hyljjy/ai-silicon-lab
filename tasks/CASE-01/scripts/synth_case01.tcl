# CASE-01 synthesis recipe (spec 4.2). Used for CASE-01 only; env/sky130hd_kit/synth.tcl is unchanged.
# Derived from env/sky130hd_kit/synth.tcl (sha256 70a59e36...). The recipe is defined by this file's full command
# list and its sha256, not as a single-variable change. Compared with the kit flow it
#   - skips synth's built-in generic ABC call (`synth -noabc`), and
#   - replaces the whole optimization sequence of the Liberty ABC call with
#       strash; dc2; &get -n; &dch -f; &nf; &put
#     instead of the default  strash; &get -n; &fraig -x; &put; scorr; dc2; dretime; strash; &get -n; &dch -f; &nf; &put
#     (so no explicit &fraig or scorr, and the other omitted steps and representation changes are gone too).
# Why: with the kit flow ~99% of a 70-76 min synthesis of the N=16 baseline was spent in the ABC calls; &fraig
# (combinational SAT sweeping) is the main bottleneck candidate, but per-subcommand ABC time was not recorded.
# This recipe: seconds, area +0.7%. Evidence: tasks/CASE-01/evidence/F0_v1.1_synth_recipe.md, TOOL_ISSUES TOOL-013.
# Usage:
#   TOP=dot4sat RTL="rtl/dot4sat.v" OUT=netlist.v yosys -c scripts/synth_case01.tcl -l yosys.log
yosys -import

if {[info exists ::env(SYNTH_LIB)]} { error "SYNTH_LIB must not be set (CASE-01 spec 4.2)" }
set hd $::env(SKY130_HD)
set lib $hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

set excl $::env(PDK_ROOT)/$::env(PDK)/libs.tech/librelane/sky130_fd_sc_hd/synth_excluded.cells
set dont_use {}
set fh [open $excl]
foreach line [split [read $fh] "\n"] {
  set line [string trim $line]
  if {$line ne "" && [string index $line 0] ne "#"} { lappend dont_use -dont_use $line }
}
close $fh

foreach f $::env(RTL) { read_verilog $f }
synth -top $::env(TOP) -noabc
dfflibmap -liberty $lib {*}$dont_use
abc -script {+strash;dc2;&get -n;&dch -f;&nf;&put} -liberty $lib {*}$dont_use
setundef -zero
opt_clean -purge
hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
stat -liberty $lib
write_verilog -noattr -noexpr $::env(OUT)
