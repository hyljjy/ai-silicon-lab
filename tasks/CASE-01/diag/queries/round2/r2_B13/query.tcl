foreach scene [list \
    tt_025C_1v80 \
    tt_100C_1v80 \
    ss_100C_1v60 \
    ss_n40C_1v60 \
    ff_n40C_1v95 \
    ff_100C_1v95] {

  puts "===== $scene setup ====="
  report_checks \
    -path_delay max \
    -scene $scene \
    -sort_by_slack \
    -group_count 20 \
    -endpoint_count 20 \
    -format end \
    -digits 6

  puts "===== $scene hold ====="
  report_checks \
    -path_delay min \
    -scene $scene \
    -sort_by_slack \
    -group_count 20 \
    -endpoint_count 20 \
    -format end \
    -digits 6
}

report_design_area
