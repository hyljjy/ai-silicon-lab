# CASE-02 missing-version SDC (protocol v0.2 section 4.2). Derived from the F1 frozen
# tasks/CASE-01/sdc/case01_sdc.tcl (sha256 b8d1aab6...). Expects Tcl variables T (ns) and C_load (pF).
# Must be sourced AFTER sky130_define_scenes (docs/env/TOOL_ISSUES.md TOOL-012), like the original.
# Difference from the original: the 64 ports in_b[63:0] get NO set_input_delay (min or max). They keep their
# driving cell. Everything else is unchanged. The original applies delay and driving cell through one variable
# `ins`; here it is split into ins_drive (130 ports) and ins_delay (66 ports).
create_clock -name clk -period $T -waveform [list 0 [expr {$T / 2.0}]] [get_ports clk]
set_clock_uncertainty -setup 0 [get_clocks clk]
set_clock_uncertainty -hold  0 [get_clocks clk]
set_clock_transition 0 [get_clocks clk]
set_clock_latency -source 0 [get_clocks clk]
set_clock_latency 0 [get_clocks clk]

set ins_drive [get_ports {in_a[*] in_b[*] in_valid rst}]
set ins_delay [get_ports {in_a[*] in_valid rst}]
set outs      [get_ports {out_data[*] out_valid}]
set_input_delay  -clock clk -max [expr {0.2 * $T}] $ins_delay
set_input_delay  -clock clk -min 0 $ins_delay
set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 -from_pin A -pin X \
                 -input_transition_rise 0 -input_transition_fall 0 $ins_drive
set_output_delay -clock clk -max [expr {0.2 * $T}] $outs
set_output_delay -clock clk -min 0 $outs
set_load -pin_load $C_load $outs
