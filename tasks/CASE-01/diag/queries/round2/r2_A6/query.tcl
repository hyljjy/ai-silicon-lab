foreach s {ss_100C_1v60 ss_n40C_1v60 tt_025C_1v80} {
  report_checks -from [get_ports {in_b[2]}] -through [get_pins _11509_/Y] -to [get_pins _12026_/D] \
    -path_delay max -scene $s -digits 4 -format summary
}
