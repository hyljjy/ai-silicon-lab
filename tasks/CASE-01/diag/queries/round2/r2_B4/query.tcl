foreach scene [list \
    tt_025C_1v80 \
    tt_100C_1v80 \
    ss_100C_1v60 \
    ss_n40C_1v60 \
    ff_n40C_1v95 \
    ff_100C_1v95] {

  puts "===== $scene in2reg ====="
  report_checks \
    -from [all_inputs -no_clocks] \
    -to [all_registers -data_pins] \
    -path_delay max \
    -scene $scene \
    -format end \
    -digits 6

  puts "===== $scene reg2reg ====="
  report_checks \
    -from [all_registers -clock_pins] \
    -to [all_registers -data_pins] \
    -path_delay max \
    -scene $scene \
    -format end \
    -digits 6

  puts "===== $scene reg2out ====="
  report_checks \
    -from [all_registers -clock_pins] \
    -to [all_outputs] \
    -path_delay max \
    -scene $scene \
    -format end \
    -digits 6
}
