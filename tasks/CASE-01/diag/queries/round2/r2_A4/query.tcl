foreach p {_11340_/X _11434_/Y _11451_/Y _11507_/Y _11509_/Y} {
  report_checks -through [get_pins $p] -path_delay max -scene ss_n40C_1v60 \
    -fields {slew cap input_pins fanout} -digits 4 -format summary
}
report_net [get_nets -of_objects [get_pins _11421_/X]]   ;# 看进位链单元的扇入扇出
