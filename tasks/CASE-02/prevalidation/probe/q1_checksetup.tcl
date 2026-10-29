# 5.4 check_setup candidates. Each top-level command runs alone; a non-empty return value is echoed after its output.
check_setup
check_setup -verbose
check_setup -no_input_delay
check_setup -verbose -no_input_delay
check_setup -verbose -unconstrained_endpoints
check_setup -unconstrained_endpoints
check_setup -verbose -no_output_delay
check_setup -verbose -no_clock
check_setup -verbose -multiple_clock
check_setup -verbose -loops
check_setup -verbose -generated_clocks
check_setup -bogus_option
puts "RET plain=[check_setup] verbose=[check_setup -verbose] noin=[check_setup -verbose -no_input_delay] unend=[check_setup -verbose -unconstrained_endpoints]"
