# 全部寄存器与端口的对应：每个寄存器的单元、Q 端和 D 端的线网名，以及 Q 的扇出端点；_12057_ 的最差 setup 路径
# （用于 A-2-001、A-2-021、A-2-025、A-2-069、A-2-071、B-2-019）
set names {}
foreach c [all_registers -cells] { lappend names [get_full_name $c] }
puts "registers: [llength $names]"
foreach n [lsort -dictionary $names] {
  set eps {}
  foreach e [get_fanout -from [get_pins $n/Q] -endpoints_only -flat] { lappend eps [get_full_name $e] }
  puts "reg $n [get_property [get_cells $n] ref_name] Q=[get_full_name [get_nets -of_objects [get_pins $n/Q]]] D=[get_full_name [get_nets -of_objects [get_pins $n/D]]] Q_endpoints=[lsort -dictionary -unique $eps]"
}
report_checks -to [get_pins _12057_/D] -path_delay max -scenes ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 6
