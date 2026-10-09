# CASE-01 synthesis recipe (spec 4.2, contract v1.1). Used for CASE-01 only; env/sky130hd_kit/synth.tcl is unchanged.
# Derived from env/sky130hd_kit/synth.tcl (sha256 70a59e36...) with exactly two changes, marked CASE-01:
#   1. `synth -noabc`: skip synth's built-in generic ABC mapping (the liberty mapping below does the real mapping).
#   2. the liberty ABC call uses the default script minus `&fraig -x; &put; scorr`:
#      strash; dc2; &get -n; &dch -f; &nf; &put
# Why: with the default script, both ABC calls spend almost all of their time in &fraig (SAT sweeping) on the
# four 16x16 multipliers: 4572 s and 4230 s for one synthesis (2026-10-08). scorr does nothing here (ABC only
# receives combinational logic; it just prints "The network is combinational"). With this recipe: 4 s, area
# +0.7% (45384 vs 45083 um^2). See tasks/CASE-01/evidence/F0_v1.1_synth_recipe.md and TOOL_ISSUES TOOL-013.
# Usage:
#   TOP=dot4sat RTL="rtl/dot4sat.v" OUT=netlist.v yosys -c scripts/synth_case01.tcl -l yosys.log
# SYNTH_LIB must not be set (spec 4.2; the grader refuses to run if it is).
yosys -import

set hd $::env(SKY130_HD)
set lib $hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
if {[info exists ::env(SYNTH_LIB)]} { set lib $::env(SYNTH_LIB) }

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
