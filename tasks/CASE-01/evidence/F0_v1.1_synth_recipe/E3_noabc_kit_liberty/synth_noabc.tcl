# Yosys: synthesize RTL to sky130_fd_sc_hd (tt_025C_1v80), honoring LibreLane's synth_excluded.cells.
# Usage:
#   TOP=mac RTL="mac.v other.v" OUT=mac_netlist.v yosys -c $SKY130_KIT/synth.tcl -l yosys.log
# Optional env: SYNTH_LIB (override liberty used for mapping)
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
abc -liberty $lib {*}$dont_use
setundef -zero
opt_clean -purge
hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
stat -liberty $lib
write_verilog -noattr -noexpr $::env(OUT)
