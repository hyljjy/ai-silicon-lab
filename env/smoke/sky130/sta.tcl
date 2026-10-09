# Multi-corner STA smoke test for ~/smoke/sky130 (mac, 5.0 ns clock, all 16 corners).
source $::env(SKY130_KIT)/corners.tcl
sky130_read_libs all
read_verilog mac_netlist.v
link_design mac
create_clock -name clk -period 5.0 [get_ports clk]
set_input_delay 0.2 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 0.2 -clock clk [all_outputs]
sky130_define_scenes

puts [format "%-6s %-16s %10s %10s" set corner setup_ws hold_ws]
foreach grp {std sweep} {
  foreach c [sky130_corner_list $grp] {
    puts [format "%-6s %-16s %10.3f %10.3f" $grp $c \
      [worst_slack -scene $c -max] [worst_slack -scene $c -min]]
  }
}
report_checks -path_delay max -scene ss_n40C_1v60
