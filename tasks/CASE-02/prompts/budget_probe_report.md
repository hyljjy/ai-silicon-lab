=== CASE01-probe QUERY BEGIN (query) ===
CASE01-probe-CMD: report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60
No paths found.
CASE01-probe-CMD: report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60 -unconstrained
Startpoint: in_b[2] (input port)
Endpoint: _12026_ (rising edge-triggered flip-flop)
Path Group: unconstrained
Path Type: max
Corner: ss_n40C_1v60

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00 ^ input external delay
   0.31    0.31 ^ in_b[2] (in)
   0.25    0.55 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
   0.98    1.53 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.63    2.16 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   1.04    3.20 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.27    3.47 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.66    4.13 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   1.09    5.22 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.93    6.15 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.40    6.55 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.73    7.28 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.94    8.22 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.98    9.20 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.41    9.61 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.26    9.87 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.93   10.80 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.54   11.35 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.53   11.88 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.18   12.06 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.95   13.01 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.94   13.95 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.53   14.47 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.32   14.79 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.94   15.74 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.95   16.68 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.44   17.12 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.25   17.38 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.51   17.89 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.34   18.22 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.85   19.07 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.43   19.50 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   1.02   20.53 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.49   21.02 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.84   21.86 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.35   22.21 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.25   22.46 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   2.64   25.10 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.86   25.96 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.00   25.96 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
          25.96   data arrival time
---------------------------------------------------------
(Path is unconstrained)


CASE01-probe-CMD: report_checks -path_delay min -from [get_ports {in_b[*]}] -scene ss_n40C_1v60
No paths found.
CASE01-probe-CMD: report_checks -path_delay min -from [get_ports {in_b[*]}] -scene ss_n40C_1v60 -unconstrained
Startpoint: in_b[0] (input port)
Endpoint: _12026_ (rising edge-triggered flip-flop)
Path Group: unconstrained
Path Type: min
Corner: ss_n40C_1v60

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00 v input external delay
   0.14    0.14 v in_b[0] (in)
   0.22    0.36 ^ _11376_/Y (sky130_fd_sc_hd__nand2_1)
   0.12    0.48 v _11511_/X (sky130_fd_sc_hd__xor2_1)
   0.24    0.72 ^ _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.00    0.72 ^ _12026_/D (sky130_fd_sc_hd__dfxtp_1)
           0.72   data arrival time
---------------------------------------------------------
(Path is unconstrained)


CASE01-probe-CMD: find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained
_40cd7c9b7b590000_p_PathEnd
CASE01-probe-CMD: puts "COUNT in_b max plain=[llength [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60]] unconstrained=[llength [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained]]"
COUNT in_b max plain=0 unconstrained=1
CASE01-probe-CMD: puts "COUNT in_b min plain=[llength [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay min -scenes ss_n40C_1v60]] unconstrained=[llength [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay min -scenes ss_n40C_1v60 -unconstrained]]"
COUNT in_b min plain=0 unconstrained=1
CASE01-probe-CMD: puts "COUNT in_a max plain=[llength [find_timing_paths -from [get_ports {in_a[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60]] unconstrained=[llength [find_timing_paths -from [get_ports {in_a[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained]]"
COUNT in_a max plain=1 unconstrained=1
CASE01-probe-CMD: foreach pe [find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained] { puts "PE [get_full_name [get_property $pe startpoint]] -> [get_full_name [get_property $pe endpoint]] slack=[get_property $pe slack]" }
PE in_b[2] -> _12026_/D slack=INF
CASE01-probe-CMD: foreach pe [find_timing_paths -from [get_ports {in_a[*]}] -to [all_registers -data_pins] -path_delay max -scenes ss_n40C_1v60 -unconstrained] { puts "PE in_a [get_full_name [get_property $pe startpoint]] -> [get_full_name [get_property $pe endpoint]] slack=[get_property $pe slack]" }
PE in_a in_a[34] -> _12026_/D slack=-4.172595
CASE01-probe-CMD: report_checks -path_delay max -from [get_ports {in_a[*]}] -scene ss_n40C_1v60 -unconstrained -format summary
Startpoint                           Endpoint                               Slack
--------------------------------------------------------------------------------
in_a[34] (input)                     _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.17

CASE01-probe-CMD: report_checks -path_delay max -scene ss_n40C_1v60 -unconstrained -format summary
Startpoint                           Endpoint                               Slack
--------------------------------------------------------------------------------
in_a[34] (input)                     _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.17

CASE01-probe-CMD: report_checks -path_delay max -from [get_ports {in_a[34] in_b[2]}] -scene ss_n40C_1v60 -unconstrained -format summary
Startpoint                           Endpoint                               Slack
--------------------------------------------------------------------------------
in_a[34] (input)                     _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.17

CASE01-probe-CMD: report_checks -path_delay max -from [get_ports {in_a[34] in_b[2]}] -scene ss_n40C_1v60 -unconstrained -group_path_count 4 -format summary
Startpoint                           Endpoint                               Slack
--------------------------------------------------------------------------------
in_a[34] (input)                     _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.17
in_a[34] (input)                     _12027_/D (sky130_fd_sc_hd__dfxtp_1)   -4.17
in_a[34] (input)                     _12029_/D (sky130_fd_sc_hd__dfxtp_1)   -4.17
in_a[34] (input)                     _12032_/D (sky130_fd_sc_hd__dfxtp_1)   -4.17

CASE01-probe-CMD: report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60 -unconstrained -group_path_count 200 -endpoint_path_count 200 -format summary
Startpoint                           Endpoint                               Slack
--------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   25.96
in_b[2] (input)                      _12027_/D (sky130_fd_sc_hd__dfxtp_1)   25.96
in_b[2] (input)                      _12029_/D (sky130_fd_sc_hd__d

以上是一段时序报告。请只回复两个字母 OK，不要输出其他内容。
