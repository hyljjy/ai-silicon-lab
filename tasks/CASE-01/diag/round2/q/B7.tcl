report_instance [get_cells {_12026_}]
report_pin [get_pins {_12026_/D}]
report_pin [get_pins {_12026_/Q}]

set qnet_12026 [get_nets -of_objects [get_pins {_12026_/Q}]]
report_net -connections -verbose $qnet_12026

set out0net [get_nets -of_objects [get_ports {out_data[0]}]]
report_net -connections -verbose $out0net
