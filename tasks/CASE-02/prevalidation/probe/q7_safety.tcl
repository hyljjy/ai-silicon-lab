# safe interpreter boundaries: things a query must NOT be able to do
exec ls
write_sdc /tmp/x.sdc
sta::port_ext_pin_cap [get_ports {out_valid}] max
report_checks > /tmp/x.txt
source /etc/hostname
open /etc/hostname
set_input_delay -clock clk -max 5.582 [get_ports {in_b[0]}]
read_sdc /tmp/none.sdc
create_clock -name clk -period 27.91 [get_ports clk]
puts "still alive"
