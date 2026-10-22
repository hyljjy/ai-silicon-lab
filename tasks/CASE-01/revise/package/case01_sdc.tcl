# CASE-01 SDC (spec 4.3). Expects Tcl variables T (ns) and C_load (pF) to be set by the caller.
# Must be sourced AFTER sky130_define_scenes: set_load issued before define_scene is silently cleared
# (docs/env/TOOL_ISSUES.md TOOL-012).
create_clock -name clk -period $T -waveform [list 0 [expr {$T / 2.0}]] [get_ports clk]
set_clock_uncertainty -setup 0 [get_clocks clk]
set_clock_uncertainty -hold  0 [get_clocks clk]
set_clock_transition 0 [get_clocks clk]
set_clock_latency -source 0 [get_clocks clk]
set_clock_latency 0 [get_clocks clk]

set ins  [get_ports {in_a[*] in_b[*] in_valid rst}]
set outs [get_ports {out_data[*] out_valid}]
set_input_delay  -clock clk -max [expr {0.2 * $T}] $ins
set_input_delay  -clock clk -min 0 $ins
set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 -from_pin A -pin X \
                 -input_transition_rise 0 -input_transition_fall 0 $ins
set_output_delay -clock clk -max [expr {0.2 * $T}] $outs
set_output_delay -clock clk -min 0 $outs
set_load -pin_load $C_load $outs
