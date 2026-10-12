# Worst path of every corner, path class and analysis type, 6 digits. Object expressions and class loop as in the
# frozen scripts/sta_run.tcl (lines 36-38 and 66-73). reg2reg prints "No paths found.": the design has no
# register-to-register paths (TOPO reg2reg 0 in sta_results.tsv); that output is expected, not a failure.
# No top-level "set": its value (object addresses) would be printed and make the output differ from run to run.
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  foreach {cat from to} [list in2reg [all_inputs -no_clocks] [all_registers -data_pins] \
                              reg2reg [all_registers -clock_pins] [all_registers -data_pins] \
                              reg2out [all_registers -clock_pins] [all_outputs]] {
    foreach mm {max min} {
      puts "=== B05 $c $cat $mm ==="
      report_checks -from $from -to $to -path_delay $mm -scene $c -fields {slew cap input_pins fanout net} -digits 6
    }
  }
}
