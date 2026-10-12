report_instance [get_cells {_11509_}]
report_pin [get_pins {_11509_/Y}]

set net_11509_y [get_nets -of_objects [get_pins {_11509_/Y}]]
report_net -connections -verbose $net_11509_y
