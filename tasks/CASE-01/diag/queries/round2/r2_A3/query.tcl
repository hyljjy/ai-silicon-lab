report_instance _11509_
report_net -digits 4 [get_nets -of_objects [get_pins _11509_/Y]]
report_checks -through [get_pins _11509_/Y] -path_delay max -scene ss_n40C_1v60 \
  -group_path_count 40 -endpoint_path_count 1 -format end -digits 4
