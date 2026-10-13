### 查询 B2
你写的查询：
```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -slack_max 0.0 \
  -sort_by_slack \
  -group_count 50 \
  -endpoint_count 50 \
  -unique_paths_to_endpoint \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```
实际执行的命令：
```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -slack_max 0.0 \
  -sort_by_slack \
  -group_count 50 \
  -endpoint_count 50 \
  -unique_paths_to_endpoint \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```
机械改写：无
结果代码：已执行
输出：
```text
CASE01-CMD: report_checks \
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
Startpoint: in_b[2] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                              5.5820    5.5820 ^ input external delay
    19    0.0415    0.4338    0.3091    5.8911 ^ in_b[2] (in)
                    0.4338    0.0000    5.8911 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
     2    0.0046    0.1123    0.2453    6.1365 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1123    0.0000    6.1365 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
     2    0.0054    0.1199    0.9804    7.1168 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1199    0.0000    7.1168 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
     3    0.0110    0.6492    0.6267    7.7436 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.6492    0.0000    7.7436 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0063    0.1268    1.0379    8.7814 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1268    0.0000    8.7814 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0060    0.1002    0.2727    9.0542 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.1002    0.0000    9.0542 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
     3    0.0113    0.6618    0.6601    9.7142 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.6618    0.0000    9.7142 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0090    0.1536    1.0917   10.8059 v _11186_/X (sky130_fd_sc_hd__xor3_1)
                    0.1536    0.0000   10.8059 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0061    0.1254    0.9265   11.7324 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1254    0.0000   11.7324 v _11257_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0063    0.3752    0.3997   12.1321 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
                    0.3752    0.0000   12.1321 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
     2    0.0073    0.1401    0.7300   12.8620 v _11302_/X (sky130_fd_sc_hd__xor3_1)
                    0.1401    0.0000   12.8620 v _11306_/B (sky130_fd_sc_hd__maj3_1)
     2    0.0073    0.1599    0.9433   13.8053 v _11306_/X (sky130_fd_sc_hd__maj3_1)
                    0.1599    0.0000   13.8053 v _11338_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0061    0.1307    0.9799   14.7852 v _11338_/X (sky130_fd_sc_hd__xor3_1)
                    0.1307    0.0000   14.7852 v _11340_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0065    0.3820    0.4077   15.1930 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
                    0.3820    0.0000   15.1930 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1299    0.2608   15.4538 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1299    0.0000   15.4538 v _11418_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0055    0.1444    0.9285   16.3823 v _11418_/X (sky130_fd_sc_hd__maj3_1)
                    0.1444    0.0000   16.3823 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
     2    0.0063    0.4984    0.5449   16.9272 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.4984    0.0000   16.9272 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0065    0.1750    0.5349   17.4621 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
                    0.1750    0.0000   17.4621 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1381    0.1799   17.6420 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1381    0.0000   17.6420 v _11423_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0067    0.1552    0.9453   18.5873 v _11423_/X (sky130_fd_sc_hd__maj3_1)
                    0.1552    0.0000   18.5873 v _11424_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0056    0.1456    0.9406   19.5278 v _11424_/X (sky130_fd_sc_hd__maj3_1)
                    0.1456    0.0000   19.5278 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5098    0.5289   20.0567 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5098    0.0000   20.0567 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0069    0.1331    0.3197   20.3764 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1331    0.0000   20.3764 v _11428_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0069    0.1564    0.9447   21.3211 v _11428_/X (sky130_fd_sc_hd__maj3_1)
                    0.1564    0.0000   21.3211 v _11429_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0061    0.1494    0.9456   22.2667 v _11429_/X (sky130_fd_sc_hd__maj3_1)
                    0.1494    0.0000   22.2667 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
     2    0.0065    0.3918    0.4391   22.7059 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
                    0.3918    0.0000   22.7059 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0050    0.1137    0.2517   22.9576 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1137    0.0000   22.9576 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5099    0.5119   23.4695 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5099    0.0000   23.4695 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0084    0.1479    0.3357   23.8052 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1479    0.0000   23.8052 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
     3    0.0088    0.8527    0.8462   24.6514 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
                    0.8527    0.0000   24.6514 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
     3    0.0058    0.1806    0.4326   25.0840 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
                    0.1806    0.0000   25.0840 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
     3    0.0068    1.0230    1.0241   26.1081 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
                    1.0230    0.0000   26.1081 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
     3    0.0042    0.1761    0.4919   26.6000 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
                    0.1761    0.0000   26.6000 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
     2    0.0045    0.7912    0.8376   27.4376 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.7912    0.0000   27.4376 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
     1    0.0041    0.1315    0.3533   27.7908 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1315    0.0000   27.7908 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0037    0.0814    0.2543   28.0452 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0814    0.0000   28.0452 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
    31    0.0511    3.2455    2.6362   30.6814 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
                    3.2455    0.0000   30.6814 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
     1    0.0015    0.3761    0.8625   31.5439 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.3761    0.0000   31.5439 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
                                       31.5439   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                                       27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
                             -0.5559   27.3541   library setup time
                                       27.3541   data required time
-------------------------------------------------------------------------------------
                                       27.3541   data required time
... [已截断：共 5103 行，保留开头 100 行和结尾 100 行] ...
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                              5.5820    5.5820 ^ input external delay
    19    0.0373    0.3922    0.2787    5.8607 ^ in_b[35] (in)
                    0.3922    0.0000    5.8607 ^ _10564_/B (sky130_fd_sc_hd__and2_0)
     2    0.0050    0.1742    0.4031    6.2638 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
                    0.1742    0.0000    6.2638 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
     2    0.0073    0.1346    1.0188    7.2826 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1346    0.0000    7.2826 v _10985_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0067    0.1357    0.9736    8.2562 v _10985_/X (sky130_fd_sc_hd__xor3_1)
                    0.1357    0.0000    8.2562 v _10986_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0077    0.4310    0.4475    8.7037 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
                    0.4310    0.0000    8.7037 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
     1    0.0023    0.2113    0.4045    9.1082 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
                    0.2113    0.0000    9.1082 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
     2    0.0073    0.2040    0.2403    9.3485 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
                    0.2040    0.0000    9.3485 v _11073_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0055    0.1259    0.9973   10.3458 v _11073_/X (sky130_fd_sc_hd__xor3_1)
                    0.1259    0.0000   10.3458 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
     2    0.0078    0.4964    0.5470   10.8928 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.4964    0.0000   10.8928 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0073    0.1346    0.9809   11.8738 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1346    0.0000   11.8738 v _11302_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0073    0.1401    0.9794   12.8531 v _11302_/X (sky130_fd_sc_hd__xor3_1)
                    0.1401    0.0000   12.8531 v _11306_/B (sky130_fd_sc_hd__maj3_1)
     2    0.0073    0.1599    0.9433   13.7964 v _11306_/X (sky130_fd_sc_hd__maj3_1)
                    0.1599    0.0000   13.7964 v _11338_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0061    0.1307    0.9799   14.7763 v _11338_/X (sky130_fd_sc_hd__xor3_1)
                    0.1307    0.0000   14.7763 v _11340_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0065    0.3820    0.4077   15.1841 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
                    0.3820    0.0000   15.1841 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1299    0.2608   15.4449 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1299    0.0000   15.4449 v _11418_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0055    0.1444    0.9285   16.3734 v _11418_/X (sky130_fd_sc_hd__maj3_1)
                    0.1444    0.0000   16.3734 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
     2    0.0063    0.4984    0.5449   16.9183 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.4984    0.0000   16.9183 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0065    0.1750    0.5349   17.4532 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
                    0.1750    0.0000   17.4532 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1381    0.1799   17.6331 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1381    0.0000   17.6331 v _11423_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0067    0.1552    0.9453   18.5783 v _11423_/X (sky130_fd_sc_hd__maj3_1)
                    0.1552    0.0000   18.5783 v _11424_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0056    0.1456    0.9406   19.5189 v _11424_/X (sky130_fd_sc_hd__maj3_1)
                    0.1456    0.0000   19.5189 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5098    0.5289   20.0478 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5098    0.0000   20.0478 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0069    0.1331    0.3197   20.3675 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1331    0.0000   20.3675 v _11428_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0069    0.1564    0.9447   21.3122 v _11428_/X (sky130_fd_sc_hd__maj3_1)
                    0.1564    0.0000   21.3122 v _11429_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0061    0.1494    0.9456   22.2578 v _11429_/X (sky130_fd_sc_hd__maj3_1)
                    0.1494    0.0000   22.2578 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
     2    0.0065    0.3918    0.4391   22.6969 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
                    0.3918    0.0000   22.6969 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0050    0.1137    0.2517   22.9486 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1137    0.0000   22.9486 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5099    0.5119   23.4606 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5099    0.0000   23.4606 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0084    0.1479    0.3357   23.7962 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1479    0.0000   23.7962 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
     3    0.0088    0.8527    0.8462   24.6425 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
                    0.8527    0.0000   24.6425 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
     3    0.0058    0.1806    0.4326   25.0751 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
                    0.1806    0.0000   25.0751 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
     3    0.0068    1.0230    1.0241   26.0992 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
                    1.0230    0.0000   26.0992 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
     3    0.0042    0.1761    0.4919   26.5911 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
                    0.1761    0.0000   26.5911 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
     2    0.0045    0.7912    0.8376   27.4287 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.7912    0.0000   27.4287 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
     1    0.0041    0.1315    0.3533   27.7819 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1315    0.0000   27.7819 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0037    0.0814    0.2543   28.0363 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0814    0.0000   28.0363 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
    31    0.0511    3.2455    2.6362   30.6724 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
                    3.2455    0.0000   30.6724 ^ _11574_/B1 (sky130_fd_sc_hd__o21ai_0)
     1    0.0015    0.3761    0.8625   31.5350 v _11574_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.3761    0.0000   31.5350 v _12052_/D (sky130_fd_sc_hd__dfxtp_1)
                                       31.5350   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                                       27.9100 ^ _12052_/CLK (sky130_fd_sc_hd__dfxtp_1)
                             -0.5559   27.3541   library setup time
                                       27.3541   data required time
-------------------------------------------------------------------------------------
                                       27.3541   data required time
                                      -31.5350   data arrival time
-------------------------------------------------------------------------------------
                                       -4.1808   slack (VIOLATED)
```

### 查询 B3
你写的查询：
```tcl
foreach scene [list \
    tt_025C_1v80 \
    tt_100C_1v80 \
    ss_100C_1v60 \
    ss_n40C_1v60 \
    ff_n40C_1v95 \
    ff_100C_1v95] {

  puts "===== $scene ====="
  report_checks \
    -from [get_ports {in_b[2]}] \
    -to [get_pins {_12026_/D}] \
    -path_delay max \
    -scene $scene \
    -format full_clock_expanded \
    -fields {slew cap input_pins fanout} \
    -digits 4
}
```
实际执行的命令：
```tcl
foreach scene [list \
    tt_025C_1v80 \
    tt_100C_1v80 \
    ss_100C_1v60 \
    ss_n40C_1v60 \
    ff_n40C_1v95 \
    ff_100C_1v95] {

  puts "===== $scene ====="
  report_checks \
    -from [get_ports {in_b[2]}] \
    -to [get_pins {_12026_/D}] \
    -path_delay max \
    -scene $scene \
    -format full_clock_expanded \
    -fields {slew cap input_pins fanout} \
    -digits 4
}
```
机械改写：无
结果代码：已执行
输出：
```text
CASE01-CMD: foreach scene [list \
===== tt_025C_1v80 =====
Startpoint: in_b[2] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: tt_025C_1v80

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                              5.5820    5.5820 ^ input external delay
    19    0.0448    0.2222    0.1554    5.7374 ^ in_b[2] (in)
                    0.2222    0.0000    5.7374 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
     2    0.0050    0.0740    0.0990    5.8364 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
                    0.0740    0.0000    5.8364 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
     2    0.0059    0.0852    0.3830    6.2194 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
                    0.0852    0.0000    6.2194 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
     3    0.0116    0.2982    0.2755    6.4949 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.2982    0.0000    6.4949 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0068    0.0893    0.3964    6.8913 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
                    0.0893    0.0000    6.8913 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0066    0.0730    0.1581    7.0494 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0730    0.0000    7.0494 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
     3    0.0119    0.3029    0.2927    7.3421 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.3029    0.0000    7.3421 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0093    0.1050    0.4194    7.7615 v _11186_/X (sky130_fd_sc_hd__xor3_1)
                    0.1050    0.0000    7.7615 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0064    0.0883    0.3737    8.1352 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
                    0.0883    0.0000    8.1352 v _11257_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0067    0.1870    0.1938    8.3290 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
                    0.1870    0.0000    8.3290 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
     2    0.0075    0.0961    0.2810    8.6099 v _11302_/X (sky130_fd_sc_hd__xor3_1)
                    0.0961    0.0000    8.6099 v _11335_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0063    0.0873    0.3691    8.9790 v _11335_/X (sky130_fd_sc_hd__xnor3_1)
                    0.0873    0.0000    8.9790 v _11337_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0065    0.0872    0.3851    9.3641 v _11337_/X (sky130_fd_sc_hd__maj3_1)
                    0.0872    0.0000    9.3641 v _11340_/A (sky130_fd_sc_hd__xor2_1)
     2    0.0071    0.1936    0.2176    9.5817 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
                    0.1936    0.0000    9.5817 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
     2    0.0073    0.0914    0.1227    9.7043 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0914    0.0000    9.7043 v _11418_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0060    0.0850    0.3830   10.0874 v _11418_/X (sky130_fd_sc_hd__maj3_1)
                    0.0850    0.0000   10.0874 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
     2    0.0067    0.2461    0.2493   10.3367 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.2461    0.0000   10.3367 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0071    0.0915    0.2494   10.5861 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
                    0.0915    0.0000   10.5861 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0071    0.0930    0.0961   10.6822 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0930    0.0000   10.6822 v _11423_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0071    0.0910    0.3913   11.0735 v _11423_/X (sky130_fd_sc_hd__maj3_1)
                    0.0910    0.0000   11.0735 v _11424_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0061    0.0851    0.3833   11.4568 v _11424_/X (sky130_fd_sc_hd__maj3_1)
                    0.0851    0.0000   11.4568 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0071    0.2554    0.2431   11.6999 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.2554    0.0000   11.6999 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0074    0.0929    0.1407   11.8406 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0929    0.0000   11.8406 v _11428_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0074    0.0926    0.3933   12.2340 v _11428_/X (sky130_fd_sc_hd__maj3_1)
                    0.0926    0.0000   12.2340 v _11429_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0064    0.0869    0.3857   12.6197 v _11429_/X (sky130_fd_sc_hd__maj3_1)
                    0.0869    0.0000   12.6197 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
     2    0.0071    0.1857    0.1902   12.8099 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
                    0.1857    0.0000   12.8099 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0054    0.0803    0.1109   12.9208 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0803    0.0000   12.9208 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0071    0.2554    0.2411   13.1619 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.2554    0.0000   13.1619 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0090    0.1018    0.1503   13.3122 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1018    0.0000   13.3122 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
     3    0.0096    0.3856    0.3527   13.6648 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
                    0.3856    0.0000   13.6648 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
     3    0.0061    0.1197    0.1607   13.8255 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
                    0.1197    0.0000   13.8255 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
     3    0.0073    0.4893    0.4489   14.2745 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.4893    0.0000   14.2745 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
     3    0.0045    0.1222    0.1809   14.4554 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
                    0.1222    0.0000   14.4554 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
     2    0.0049    0.3826    0.3681   14.8235 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.3826    0.0000   14.8235 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
     1    0.0045    0.0853    0.1147   14.9381 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
                    0.0853    0.0000   14.9381 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0040    0.0589    0.1413   15.0794 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0589    0.0000   15.0794 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
    31    0.0553    1.5994    1.2298   16.3092 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
                    1.5994    0.0000   16.3092 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
     1    0.0017    0.2287    0.1976   16.5068 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.2287    0.0000   16.5068 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
                                       16.5068   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                                       27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
                             -0.2019   27.7081   library setup time
                                       27.7081   data required time
-------------------------------------------------------------------------------------
                                       27.7081   data required time
                                      -16.5068   data arrival time
... [已截断：共 619 行，保留开头 100 行和结尾 100 行] ...
Path Group: clk
Path Type: max
Corner: ff_100C_1v95

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                              5.5820    5.5820 v input external delay
    19    0.0429    0.0904    0.0759    5.6579 v in_b[2] (in)
                    0.0904    0.0000    5.6579 v _10621_/B (sky130_fd_sc_hd__nand2_1)
     2    0.0057    0.0592    0.0693    5.7272 ^ _10621_/Y (sky130_fd_sc_hd__nand2_1)
                    0.0592    0.0000    5.7272 ^ _10905_/A (sky130_fd_sc_hd__xnor3_1)
     2    0.0062    0.0722    0.2401    5.9673 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
                    0.0722    0.0000    5.9673 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
     3    0.0118    0.1995    0.1681    6.1354 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.1995    0.0000    6.1354 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0070    0.0754    0.2045    6.3399 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
                    0.0754    0.0000    6.3399 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0069    0.0639    0.1096    6.4495 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0639    0.0000    6.4495 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
     3    0.0121    0.1995    0.1774    6.6269 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.1995    0.0000    6.6269 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0095    0.0935    0.2256    6.8525 v _11186_/X (sky130_fd_sc_hd__xor3_1)
                    0.0935    0.0000    6.8525 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0067    0.0741    0.1997    7.0522 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
                    0.0741    0.0000    7.0522 v _11257_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0066    0.0738    0.1084    7.1607 v _11257_/X (sky130_fd_sc_hd__xor2_1)
                    0.0738    0.0000    7.1607 v _11258_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0053    0.0641    0.1910    7.3517 v _11258_/X (sky130_fd_sc_hd__maj3_1)
                    0.0641    0.0000    7.3517 v _11307_/A (sky130_fd_sc_hd__xor3_1)
     2    0.0071    0.0745    0.2651    7.6168 ^ _11307_/X (sky130_fd_sc_hd__xor3_1)
                    0.0745    0.0000    7.6168 ^ _11338_/C (sky130_fd_sc_hd__xor3_1)
     2    0.0066    0.0808    0.1339    7.7506 v _11338_/X (sky130_fd_sc_hd__xor3_1)
                    0.0808    0.0000    7.7506 v _11340_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0073    0.1364    0.1274    7.8780 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
                    0.1364    0.0000    7.8780 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
     2    0.0076    0.0789    0.0808    7.9588 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0789    0.0000    7.9588 v _11418_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0063    0.0685    0.1974    8.1562 v _11418_/X (sky130_fd_sc_hd__maj3_1)
                    0.0685    0.0000    8.1562 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
     2    0.0071    0.1762    0.1587    8.3149 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.1762    0.0000    8.3149 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0072    0.0701    0.1389    8.4538 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
                    0.0701    0.0000    8.4538 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0074    0.0782    0.0697    8.5235 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0782    0.0000    8.5235 v _11423_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0074    0.0732    0.2029    8.7264 v _11423_/X (sky130_fd_sc_hd__maj3_1)
                    0.0732    0.0000    8.7264 v _11424_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0063    0.0684    0.1961    8.9225 v _11424_/X (sky130_fd_sc_hd__maj3_1)
                    0.0684    0.0000    8.9225 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0072    0.1792    0.1546    9.0771 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.1792    0.0000    9.0771 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0077    0.0822    0.0858    9.1629 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0822    0.0000    9.1629 v _11428_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0077    0.0747    0.2056    9.3685 v _11428_/X (sky130_fd_sc_hd__maj3_1)
                    0.0747    0.0000    9.3685 v _11429_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0065    0.0694    0.1976    9.5661 v _11429_/X (sky130_fd_sc_hd__maj3_1)
                    0.0694    0.0000    9.5661 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
     2    0.0072    0.1250    0.1161    9.6822 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
                    0.1250    0.0000    9.6822 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0057    0.0699    0.0709    9.7531 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0699    0.0000    9.7531 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0072    0.1792    0.1550    9.9081 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.1792    0.0000    9.9081 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0093    0.0896    0.0930   10.0011 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.0896    0.0000   10.0011 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
     3    0.0099    0.2510    0.2101   10.2112 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
                    0.2510    0.0000   10.2112 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
     3    0.0063    0.0941    0.0888   10.3000 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
                    0.0941    0.0000   10.3000 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
     3    0.0075    0.3373    0.2758   10.5758 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.3373    0.0000   10.5758 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
     3    0.0048    0.1103    0.0934   10.6692 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
                    0.1103    0.0000   10.6692 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
     2    0.0050    0.2649    0.2294   10.8987 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.2649    0.0000   10.8987 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
     1    0.0046    0.0719    0.0579   10.9565 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
                    0.0719    0.0000   10.9565 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0042    0.0522    0.0963   11.0528 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0522    0.0000   11.0528 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
    31    0.0593    1.1510    0.8249   11.8778 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
                    1.1510    0.0000   11.8778 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
     1    0.0018    0.1829    0.0326   11.9104 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.1829    0.0000   11.9104 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
                                       11.9104   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                                       27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
                             -0.1054   27.8046   library setup time
                                       27.8046   data required time
-------------------------------------------------------------------------------------
                                       27.8046   data required time
                                      -11.9104   data arrival time
-------------------------------------------------------------------------------------
                                       15.8942   slack (MET)
```

### 查询 B4
你写的查询：
```tcl
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
```
实际执行的命令：
```tcl
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
```
机械改写：无
结果代码：已执行
输出：
```text
CASE01-CMD: foreach scene [list \
===== tt_025C_1v80 in2reg =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)

===== tt_025C_1v80 reg2reg =====
No paths found.

===== tt_025C_1v80 reg2out =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
out_data[0] (output)                   22.327999    0.280206   22.047794 (MET)

===== tt_100C_1v80 in2reg =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)

===== tt_100C_1v80 reg2reg =====
No paths found.

===== tt_100C_1v80 reg2out =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
out_data[0] (output)                   22.327999    0.282560   22.045441 (MET)

===== ss_100C_1v60 in2reg =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.474070   28.161348   -0.687278 (VIOLATED)

===== ss_100C_1v60 reg2reg =====
No paths found.

===== ss_100C_1v60 reg2out =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
out_data[0] (output)                   22.327999    0.585913   21.742086 (MET)

===== ss_n40C_1v60 in2reg =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.354149   31.543875   -4.189726 (VIOLATED)

===== ss_n40C_1v60 reg2reg =====
No paths found.

===== ss_n40C_1v60 reg2out =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
out_data[0] (output)                   22.327999    0.635566   21.692432 (MET)

===== ff_n40C_1v95 in2reg =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)

===== ff_n40C_1v95 reg2reg =====
No paths found.

===== ff_n40C_1v95 reg2out =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
out_data[0] (output)                   22.327999    0.173725   22.154276 (MET)

===== ff_100C_1v95 in2reg =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)

===== ff_100C_1v95 reg2reg =====
No paths found.

===== ff_100C_1v95 reg2out =====
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
out_data[0] (output)                   22.327999    0.184922   22.143078 (MET)
```

### 查询 B6
你写的查询：
```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -through [get_pins {_11509_/Y}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -sort_by_slack \
  -group_count 50 \
  -endpoint_count 50 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```
实际执行的命令：
```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -through [get_pins {_11509_/Y}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -sort_by_slack \
  -group_count 50 \
  -endpoint_count 50 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```
机械改写：无
结果代码：已执行
输出：
```text
CASE01-CMD: report_checks \
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
Startpoint: in_b[2] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                              5.5820    5.5820 ^ input external delay
    19    0.0415    0.4338    0.3091    5.8911 ^ in_b[2] (in)
                    0.4338    0.0000    5.8911 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
     2    0.0046    0.1123    0.2453    6.1365 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1123    0.0000    6.1365 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
     2    0.0054    0.1199    0.9804    7.1168 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1199    0.0000    7.1168 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
     3    0.0110    0.6492    0.6267    7.7436 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.6492    0.0000    7.7436 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0063    0.1268    1.0379    8.7814 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1268    0.0000    8.7814 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0060    0.1002    0.2727    9.0542 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.1002    0.0000    9.0542 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
     3    0.0113    0.6618    0.6601    9.7142 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.6618    0.0000    9.7142 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0090    0.1536    1.0917   10.8059 v _11186_/X (sky130_fd_sc_hd__xor3_1)
                    0.1536    0.0000   10.8059 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0061    0.1254    0.9265   11.7324 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1254    0.0000   11.7324 v _11257_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0063    0.3752    0.3997   12.1321 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
                    0.3752    0.0000   12.1321 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
     2    0.0073    0.1401    0.7300   12.8620 v _11302_/X (sky130_fd_sc_hd__xor3_1)
                    0.1401    0.0000   12.8620 v _11306_/B (sky130_fd_sc_hd__maj3_1)
     2    0.0073    0.1599    0.9433   13.8053 v _11306_/X (sky130_fd_sc_hd__maj3_1)
                    0.1599    0.0000   13.8053 v _11338_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0061    0.1307    0.9799   14.7852 v _11338_/X (sky130_fd_sc_hd__xor3_1)
                    0.1307    0.0000   14.7852 v _11340_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0065    0.3820    0.4077   15.1930 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
                    0.3820    0.0000   15.1930 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1299    0.2608   15.4538 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1299    0.0000   15.4538 v _11418_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0055    0.1444    0.9285   16.3823 v _11418_/X (sky130_fd_sc_hd__maj3_1)
                    0.1444    0.0000   16.3823 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
     2    0.0063    0.4984    0.5449   16.9272 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.4984    0.0000   16.9272 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0065    0.1750    0.5349   17.4621 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
                    0.1750    0.0000   17.4621 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1381    0.1799   17.6420 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1381    0.0000   17.6420 v _11423_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0067    0.1552    0.9453   18.5873 v _11423_/X (sky130_fd_sc_hd__maj3_1)
                    0.1552    0.0000   18.5873 v _11424_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0056    0.1456    0.9406   19.5278 v _11424_/X (sky130_fd_sc_hd__maj3_1)
                    0.1456    0.0000   19.5278 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5098    0.5289   20.0567 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5098    0.0000   20.0567 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0069    0.1331    0.3197   20.3764 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1331    0.0000   20.3764 v _11428_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0069    0.1564    0.9447   21.3211 v _11428_/X (sky130_fd_sc_hd__maj3_1)
                    0.1564    0.0000   21.3211 v _11429_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0061    0.1494    0.9456   22.2667 v _11429_/X (sky130_fd_sc_hd__maj3_1)
                    0.1494    0.0000   22.2667 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
     2    0.0065    0.3918    0.4391   22.7059 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
                    0.3918    0.0000   22.7059 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0050    0.1137    0.2517   22.9576 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1137    0.0000   22.9576 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5099    0.5119   23.4695 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5099    0.0000   23.4695 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0084    0.1479    0.3357   23.8052 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1479    0.0000   23.8052 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
     3    0.0088    0.8527    0.8462   24.6514 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
                    0.8527    0.0000   24.6514 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
     3    0.0058    0.1806    0.4326   25.0840 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
                    0.1806    0.0000   25.0840 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
     3    0.0068    1.0230    1.0241   26.1081 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
                    1.0230    0.0000   26.1081 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
     3    0.0042    0.1761    0.4919   26.6000 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
                    0.1761    0.0000   26.6000 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
     2    0.0045    0.7912    0.8376   27.4376 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.7912    0.0000   27.4376 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
     1    0.0041    0.1315    0.3533   27.7908 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1315    0.0000   27.7908 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0037    0.0814    0.2543   28.0452 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0814    0.0000   28.0452 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
    31    0.0511    3.2455    2.6362   30.6814 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
                    3.2455    0.0000   30.6814 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
     1    0.0015    0.3761    0.8625   31.5439 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.3761    0.0000   31.5439 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
                                       31.5439   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                                       27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
                             -0.5559   27.3541   library setup time
                                       27.3541   data required time
-------------------------------------------------------------------------------------
                                       27.3541   data required time
... [已截断：共 5103 行，保留开头 100 行和结尾 100 行] ...
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                              5.5820    5.5820 ^ input external delay
    19    0.0415    0.4338    0.3091    5.8911 ^ in_b[2] (in)
                    0.4338    0.0000    5.8911 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
     2    0.0046    0.1123    0.2453    6.1365 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1123    0.0000    6.1365 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
     2    0.0054    0.1199    0.9804    7.1168 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1199    0.0000    7.1168 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
     3    0.0110    0.6492    0.6267    7.7436 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.6492    0.0000    7.7436 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0063    0.1268    1.0379    8.7814 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1268    0.0000    8.7814 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0065    0.4324    0.4621    9.2435 ^ _11087_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.4324    0.0000    9.2435 ^ _11113_/A (sky130_fd_sc_hd__xnor2_1)
     3    0.0113    0.6618    0.4648    9.7083 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.6618    0.0000    9.7083 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0090    0.1536    1.0917   10.8000 v _11186_/X (sky130_fd_sc_hd__xor3_1)
                    0.1536    0.0000   10.8000 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0061    0.1254    0.9265   11.7265 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1254    0.0000   11.7265 v _11257_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0063    0.3752    0.3997   12.1262 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
                    0.3752    0.0000   12.1262 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
     2    0.0073    0.1401    0.7300   12.8561 v _11302_/X (sky130_fd_sc_hd__xor3_1)
                    0.1401    0.0000   12.8561 v _11306_/B (sky130_fd_sc_hd__maj3_1)
     2    0.0073    0.1599    0.9433   13.7994 v _11306_/X (sky130_fd_sc_hd__maj3_1)
                    0.1599    0.0000   13.7994 v _11338_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0061    0.1307    0.9799   14.7793 v _11338_/X (sky130_fd_sc_hd__xor3_1)
                    0.1307    0.0000   14.7793 v _11340_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0065    0.3820    0.4077   15.1871 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
                    0.3820    0.0000   15.1871 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1299    0.2608   15.4479 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1299    0.0000   15.4479 v _11418_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0055    0.1444    0.9285   16.3764 v _11418_/X (sky130_fd_sc_hd__maj3_1)
                    0.1444    0.0000   16.3764 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
     2    0.0063    0.4984    0.5449   16.9213 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.4984    0.0000   16.9213 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0065    0.1750    0.5349   17.4562 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
                    0.1750    0.0000   17.4562 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1381    0.1799   17.6361 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1381    0.0000   17.6361 v _11423_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0067    0.1552    0.9453   18.5814 v _11423_/X (sky130_fd_sc_hd__maj3_1)
                    0.1552    0.0000   18.5814 v _11424_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0056    0.1456    0.9406   19.5219 v _11424_/X (sky130_fd_sc_hd__maj3_1)
                    0.1456    0.0000   19.5219 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5098    0.5289   20.0508 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5098    0.0000   20.0508 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0069    0.1331    0.3197   20.3705 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1331    0.0000   20.3705 v _11428_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0069    0.1564    0.9447   21.3152 v _11428_/X (sky130_fd_sc_hd__maj3_1)
                    0.1564    0.0000   21.3152 v _11429_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0061    0.1494    0.9456   22.2608 v _11429_/X (sky130_fd_sc_hd__maj3_1)
                    0.1494    0.0000   22.2608 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
     2    0.0065    0.3918    0.4391   22.7000 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
                    0.3918    0.0000   22.7000 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0050    0.1137    0.2517   22.9517 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1137    0.0000   22.9517 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5099    0.5119   23.4636 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5099    0.0000   23.4636 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0084    0.1479    0.3357   23.7993 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1479    0.0000   23.7993 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
     3    0.0088    0.8527    0.8462   24.6455 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
                    0.8527    0.0000   24.6455 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
     3    0.0058    0.1806    0.4326   25.0781 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
                    0.1806    0.0000   25.0781 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
     3    0.0068    1.0230    1.0241   26.1022 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
                    1.0230    0.0000   26.1022 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
     3    0.0042    0.1761    0.4919   26.5941 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
                    0.1761    0.0000   26.5941 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
     2    0.0045    0.7912    0.8376   27.4317 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.7912    0.0000   27.4317 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
     1    0.0041    0.1315    0.3533   27.7849 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1315    0.0000   27.7849 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0037    0.0814    0.2543   28.0393 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0814    0.0000   28.0393 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
    31    0.0511    3.2455    2.6362   30.6755 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
                    3.2455    0.0000   30.6755 ^ _11574_/B1 (sky130_fd_sc_hd__o21ai_0)
     1    0.0015    0.3761    0.8625   31.5380 v _11574_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.3761    0.0000   31.5380 v _12052_/D (sky130_fd_sc_hd__dfxtp_1)
                                       31.5380   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                                       27.9100 ^ _12052_/CLK (sky130_fd_sc_hd__dfxtp_1)
                             -0.5559   27.3541   library setup time
                                       27.3541   data required time
-------------------------------------------------------------------------------------
                                       27.3541   data required time
                                      -31.5380   data arrival time
-------------------------------------------------------------------------------------
                                       -4.1838   slack (VIOLATED)
```

### 查询 B7
你写的查询：
```tcl
report_instance [get_cells {_12026_}]
report_pin [get_pins {_12026_/D}]
report_pin [get_pins {_12026_/Q}]

set qnet_12026 [get_nets -of_objects [get_pins {_12026_/Q}]]
report_net -connections -verbose $qnet_12026

set out0net [get_nets -of_objects [get_ports {out_data[0]}]]
report_net -connections -verbose $out0net
```
实际执行的命令：
```tcl
report_instance [get_cells {_12026_}]
report_pin [get_pins {_12026_/D}]
report_pin [get_pins {_12026_/Q}]

set qnet_12026 [get_nets -of_objects [get_pins {_12026_/Q}]]
report_net -connections -verbose $qnet_12026

set out0net [get_nets -of_objects [get_ports {out_data[0]}]]
report_net -connections -verbose $out0net
```
机械改写：无
结果代码：语法错误
输出：
```text
CASE01-CMD: report_instance [get_cells {_12026_}]
Instance _12026_
 Cell: sky130_fd_sc_hd__dfxtp_1
 Library: sky130_fd_sc_hd__tt_025C_1v80
 Path cells: sky130_fd_sc_hd__dfxtp_1
 Input pins:
  CLK input clk
  D input _00030_
 Output pins:
  Q output out_data[0]
 Other pins:
  VGND ground (unconnected)
  VPWR power (unconnected)
  IQ internal (unconnected)
  IQ_N internal (unconnected)
CASE01-CMD: report_pin [get_pins {_12026_/D}]
CASE01-ERROR: invalid command name "report_pin"
CASE01-CMD: report_pin [get_pins {_12026_/Q}]
CASE01-ERROR: invalid command name "report_pin"
CASE01-CMD: set qnet_12026 [get_nets -of_objects [get_pins {_12026_/Q}]]
_9028c005b1620000_p_Net
CASE01-CMD: report_net -connections -verbose $qnet_12026
CASE01-ERROR: Error 562: diag_query.tcl line 1, report_net -connections is not a known keyword or flag.
CASE01-CMD: set out0net [get_nets -of_objects [get_ports {out_data[0]}]]
CASE01-ERROR: Error 100: diag_query.tcl line 1, unsupported object type Port.
CASE01-CMD: report_net -connections -verbose $out0net
CASE01-ERROR: can't read "out0net": no such variable
```

### 查询 B8
你写的查询：
```tcl
report_instance [get_cells {_11509_}]
report_pin [get_pins {_11509_/Y}]

set net_11509_y [get_nets -of_objects [get_pins {_11509_/Y}]]
report_net -connections -verbose $net_11509_y
```
实际执行的命令：
```tcl
report_instance [get_cells {_11509_}]
report_pin [get_pins {_11509_/Y}]

set net_11509_y [get_nets -of_objects [get_pins {_11509_/Y}]]
report_net -connections -verbose $net_11509_y
```
机械改写：无
结果代码：语法错误
输出：
```text
CASE01-CMD: report_instance [get_cells {_11509_}]
Instance _11509_
 Cell: sky130_fd_sc_hd__o21ai_0
 Library: sky130_fd_sc_hd__tt_025C_1v80
 Path cells: sky130_fd_sc_hd__o21ai_0
 Input pins:
  A1 input _05585_
  A2 input _05586_
  B1 input _05584_
 Output pins:
  Y output _05587_
 Other pins:
  VGND ground (unconnected)
  VPWR power (unconnected)
CASE01-CMD: report_pin [get_pins {_11509_/Y}]
CASE01-ERROR: invalid command name "report_pin"
CASE01-CMD: set net_11509_y [get_nets -of_objects [get_pins {_11509_/Y}]]
_40102beaaa620000_p_Net
CASE01-CMD: report_net -connections -verbose $net_11509_y
CASE01-ERROR: Error 562: diag_query.tcl line 1, report_net -connections is not a known keyword or flag.
```

### 查询 B9
你写的查询：
```tcl
report_checks \
  -from [get_pins {_12026_/CLK}] \
  -to [get_ports {out_data[0]}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```
实际执行的命令：
```tcl
report_checks \
  -from [get_pins {_12026_/CLK}] \
  -to [get_ports {out_data[0]}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```
机械改写：无
结果代码：已执行
输出：
```text
CASE01-CMD: report_checks \
Startpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_data[0] (output port clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                    0.0000    0.0000    0.0000 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
     1    0.0024    0.0761    0.6356    0.6356 ^ _12026_/Q (sky130_fd_sc_hd__dfxtp_1)
                    0.0761    0.0000    0.6356 ^ out_data[0] (out)
                                        0.6356   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                             -5.5820   22.3280   output external delay
                                       22.3280   data required time
-------------------------------------------------------------------------------------
                                       22.3280   data required time
                                       -0.6356   data arrival time
-------------------------------------------------------------------------------------
                                       21.6924   slack (MET)
```

### 查询 B10
你写的查询：
```tcl
set ins [get_ports {in_a[*] in_b[*] in_valid rst}]

set_input_delay -clock clk -max 0 $ins

report_checks \
  -from [get_ports {in_b[2]}] \
  -to [get_pins {_12026_/D}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```
实际执行的命令：
```tcl
set ins [get_ports {in_a[*] in_b[*] in_valid rst}]

set_input_delay -clock clk -max 0 $ins

report_checks \
  -from [get_ports {in_b[2]}] \
  -to [get_pins {_12026_/D}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```
机械改写：无
结果代码：改变冻结模型的查询（已在单独运行中执行）
说明：这条查询改变了分析模型，结果只作对照，不代表冻结模型。
输出：
```text
CASE01-CMD: set ins [get_ports {in_a[*] in_b[*] in_valid rst}]
_50d46cc1d65d0000_p_Port _d0d46cc1d65d0000_p_Port _50d56cc1d65d0000_p_Port _d0d56cc1d65d0000_p_Port _50d66cc1d65d0000_p_Port _d0d66cc1d65d0000_p_Port _50d76cc1d65d0000_p_Port _d0d76cc1d65d0000_p_Port _50d86cc1d65d0000_p_Port _d0d86cc1d65d0000_p_Port _50d96cc1d65d0000_p_Port _d0d96cc1d65d0000_p_Port _50da6cc1d65d0000_p_Port _d0da6cc1d65d0000_p_Port _50db6cc1d65d0000_p_Port _d0db6cc1d65d0000_p_Port _50dc6cc1d65d0000_p_Port _d0dc6cc1d65d0000_p_Port _50dd6cc1d65d0000_p_Port _d0dd6cc1d65d0000_p_Port _50de6cc1d65d0000_p_Port _d0de6cc1d65d0000_p_Port _50df6cc1d65d0000_p_Port _d0df6cc1d65d0000_p_Port _50e06cc1d65d0000_p_Port _d0e06cc1d65d0000_p_Port _50e16cc1d65d0000_p_Port _d0e16cc1d65d0000_p_Port _50e26cc1d65d0000_p_Port _d0e26cc1d65d0000_p_Port _50e36cc1d65d0000_p_Port _d0e36cc1d65d0000_p_Port _50e46cc1d65d0000_p_Port _d0e46cc1d65d0000_p_Port _50e56cc1d65d0000_p_Port _d0e56cc1d65d0000_p_Port _50e66cc1d65d0000_p_Port _d0e66cc1d65d0000_p_Port _50e76cc1d65d0000_p_Port _d0e76cc1d65d0000_p_Port _50e86cc1d65d0000_p_Port _d0e86cc1d65d0000_p_Port _50e96cc1d65d0000_p_Port _d0e96cc1d65d0000_p_Port _50ea6cc1d65d0000_p_Port _d0ea6cc1d65d0000_p_Port _50eb6cc1d65d0000_p_Port _d0eb6cc1d65d0000_p_Port _50ec6cc1d65d0000_p_Port _d0ec6cc1d65d0000_p_Port _50ed6cc1d65d0000_p_Port _d0ed6cc1d65d0000_p_Port _50ee6cc1d65d0000_p_Port _d0ee6cc1d65d0000_p_Port _50ef6cc1d65d0000_p_Port _d0ef6cc1d65d0000_p_Port _50f06cc1d65d0000_p_Port _d0f06cc1d65d0000_p_Port _50f16cc1d65d0000_p_Port _d0f16cc1d65d0000_p_Port _50f26cc1d65d0000_p_Port _d0f26cc1d65d0000_p_Port _50f36cc1d65d0000_p_Port _d0f36cc1d65d0000_p_Port _d0f46cc1d65d0000_p_Port _50f56cc1d65d0000_p_Port _d0f56cc1d65d0000_p_Port _50f66cc1d65d0000_p_Port _d0f66cc1d65d0000_p_Port _50f76cc1d65d0000_p_Port _d0f76cc1d65d0000_p_Port _50f86cc1d65d0000_p_Port _d0f86cc1d65d0000_p_Port _50f96cc1d65d0000_p_Port _d0f96cc1d65d0000_p_Port _50fa6cc1d65d0000_p_Port _d0fa6cc1d65d0000_p_Port _50fb6cc1d65d0000_p_Port _d0fb6cc1d65d0000_p_Port _50fc6cc1d65d0000_p_Port _d0fc6cc1d65d0000_p_Port _50fd6cc1d65d0000_p_Port _d0fd6cc1d65d0000_p_Port _50fe6cc1d65d0000_p_Port _d0fe6cc1d65d0000_p_Port _50ff6cc1d65d0000_p_Port _d0ff6cc1d65d0000_p_Port _50006dc1d65d0000_p_Port _d0006dc1d65d0000_p_Port _50016dc1d65d0000_p_Port _d0016dc1d65d0000_p_Port _50026dc1d65d0000_p_Port _d0026dc1d65d0000_p_Port _50036dc1d65d0000_p_Port _d0036dc1d65d0000_p_Port _50046dc1d65d0000_p_Port _d0046dc1d65d0000_p_Port _50056dc1d65d0000_p_Port _d0056dc1d65d0000_p_Port _50066dc1d65d0000_p_Port _d0066dc1d65d0000_p_Port _50076dc1d65d0000_p_Port _d0076dc1d65d0000_p_Port _50086dc1d65d0000_p_Port _d0086dc1d65d0000_p_Port _50096dc1d65d0000_p_Port _d0096dc1d65d0000_p_Port _500a6dc1d65d0000_p_Port _d00a6dc1d65d0000_p_Port _500b6dc1d65d0000_p_Port _d00b6dc1d65d0000_p_Port _500c6dc1d65d0000_p_Port _d00c6dc1d65d0000_p_Port _500d6dc1d65d0000_p_Port _d00d6dc1d65d0000_p_Port _500e6dc1d65d0000_p_Port _d00e6dc1d65d0000_p_Port _500f6dc1d65d0000_p_Port _d00f6dc1d65d0000_p_Port _50106dc1d65d0000_p_Port _d0106dc1d65d0000_p_Port _50116dc1d65d0000_p_Port _d0116dc1d65d0000_p_Port _50126dc1d65d0000_p_Port _d0126dc1d65d0000_p_Port _50136dc1d65d0000_p_Port _d0136dc1d65d0000_p_Port _50146dc1d65d0000_p_Port _50d36cc1d65d0000_p_Port _d0d26cc1d65d0000_p_Port
CASE01-CMD: set_input_delay -clock clk -max 0 $ins
CASE01-CMD: report_checks \
Startpoint: in_b[2] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                              0.0000    0.0000 ^ input external delay
    19    0.0415    0.4338    0.3091    0.3091 ^ in_b[2] (in)
                    0.4338    0.0000    0.3091 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
     2    0.0046    0.1123    0.2453    0.5545 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1123    0.0000    0.5545 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
     2    0.0054    0.1199    0.9804    1.5348 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1199    0.0000    1.5348 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
     3    0.0110    0.6492    0.6267    2.1616 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.6492    0.0000    2.1616 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0063    0.1268    1.0379    3.1994 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1268    0.0000    3.1994 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0060    0.1002    0.2727    3.4722 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.1002    0.0000    3.4722 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
     3    0.0113    0.6618    0.6601    4.1322 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.6618    0.0000    4.1322 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0090    0.1536    1.0917    5.2239 v _11186_/X (sky130_fd_sc_hd__xor3_1)
                    0.1536    0.0000    5.2239 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0061    0.1254    0.9265    6.1504 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1254    0.0000    6.1504 v _11257_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0063    0.3752    0.3997    6.5501 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
                    0.3752    0.0000    6.5501 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
     2    0.0073    0.1401    0.7300    7.2800 v _11302_/X (sky130_fd_sc_hd__xor3_1)
                    0.1401    0.0000    7.2800 v _11306_/B (sky130_fd_sc_hd__maj3_1)
     2    0.0073    0.1599    0.9433    8.2233 v _11306_/X (sky130_fd_sc_hd__maj3_1)
                    0.1599    0.0000    8.2233 v _11338_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0061    0.1307    0.9799    9.2033 v _11338_/X (sky130_fd_sc_hd__xor3_1)
                    0.1307    0.0000    9.2033 v _11340_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0065    0.3820    0.4077    9.6110 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
                    0.3820    0.0000    9.6110 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1299    0.2608    9.8718 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1299    0.0000    9.8718 v _11418_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0055    0.1444    0.9285   10.8003 v _11418_/X (sky130_fd_sc_hd__maj3_1)
                    0.1444    0.0000   10.8003 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
     2    0.0063    0.4984    0.5449   11.3452 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.4984    0.0000   11.3452 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0065    0.1750    0.5349   11.8801 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
                    0.1750    0.0000   11.8801 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1381    0.1799   12.0600 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1381    0.0000   12.0600 v _11423_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0067    0.1552    0.9453   13.0053 v _11423_/X (sky130_fd_sc_hd__maj3_1)
                    0.1552    0.0000   13.0053 v _11424_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0056    0.1456    0.9406   13.9458 v _11424_/X (sky130_fd_sc_hd__maj3_1)
                    0.1456    0.0000   13.9458 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5098    0.5289   14.4747 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5098    0.0000   14.4747 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0069    0.1331    0.3197   14.7944 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1331    0.0000   14.7944 v _11428_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0069    0.1564    0.9447   15.7391 v _11428_/X (sky130_fd_sc_hd__maj3_1)
                    0.1564    0.0000   15.7391 v _11429_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0061    0.1494    0.9456   16.6847 v _11429_/X (sky130_fd_sc_hd__maj3_1)
                    0.1494    0.0000   16.6847 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
     2    0.0065    0.3918    0.4391   17.1239 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
                    0.3918    0.0000   17.1239 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0050    0.1137    0.2517   17.3756 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1137    0.0000   17.3756 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5099    0.5119   17.8875 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5099    0.0000   17.8875 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0084    0.1479    0.3357   18.2232 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1479    0.0000   18.2232 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
     3    0.0088    0.8527    0.8462   19.0694 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
                    0.8527    0.0000   19.0694 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
     3    0.0058    0.1806    0.4326   19.5020 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
                    0.1806    0.0000   19.5020 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
     3    0.0068    1.0230    1.0241   20.5261 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
                    1.0230    0.0000   20.5261 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
     3    0.0042    0.1761    0.4919   21.0180 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
                    0.1761    0.0000   21.0180 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
     2    0.0045    0.7912    0.8376   21.8556 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.7912    0.0000   21.8556 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
     1    0.0041    0.1315    0.3533   22.2088 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1315    0.0000   22.2088 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0037    0.0814    0.2543   22.4632 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0814    0.0000   22.4632 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
    31    0.0511    3.2455    2.6362   25.0994 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
                    3.2455    0.0000   25.0994 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
     1    0.0015    0.3761    0.8625   25.9619 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.3761    0.0000   25.9619 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
                                       25.9619   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                                       27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
                             -0.5559   27.3541   library setup time
                                       27.3541   data required time
-------------------------------------------------------------------------------------
                                       27.3541   data required time
                                      -25.9619   data arrival time
-------------------------------------------------------------------------------------
                                        1.3923   slack (MET)
```

### 查询 B11
你写的查询：
```tcl
set_input_delay -clock clk -max 5.582 $ins
```
实际执行的命令：
```tcl
set_input_delay -clock clk -max 5.582 $ins
```
机械改写：无
结果代码：改变冻结模型的查询（已在单独运行中执行）；语法错误
说明：这条查询改变了分析模型，结果只作对照，不代表冻结模型。
输出：
```text
CASE01-CMD: set_input_delay -clock clk -max 5.582 $ins
CASE01-ERROR: can't read "ins": no such variable
```

### 查询 B12
你写的查询：
```tcl
report_cell_usage -verbose
report_design_area
```
实际执行的命令：
```tcl
report_cell_usage -verbose
report_design_area
```
机械改写：无
结果代码：语法错误
输出：
```text
CASE01-CMD: report_cell_usage -verbose
CASE01-ERROR: invalid command name "report_cell_usage"
CASE01-CMD: report_design_area
CASE01-ERROR: invalid command name "report_design_area"
```

### 查询 B13
你写的查询：
```tcl
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
```
实际执行的命令：
```tcl
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
```
机械改写：无
结果代码：语法错误
输出：
```text
CASE01-CMD: foreach scene [list \
===== tt_025C_1v80 setup =====
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12027_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12029_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12032_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12033_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12034_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12035_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12036_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12037_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12038_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12039_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12040_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12041_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12042_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12043_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12044_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12045_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12047_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12048_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)
_12049_/D (sky130_fd_sc_hd__dfxtp_1)   27.708145   16.522688   11.185458 (MET)

===== tt_025C_1v80 hold =====
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
min_delay/hold group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.052770    0.040283    0.093054 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.041341    0.089207    0.130547 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.041341    0.102878    0.144219 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.052770    0.114969    0.167740 (MET)
out_data[0] (output)                    0.000000    0.272520    0.272520 (MET)
out_data[10] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[11] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[12] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[13] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[14] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[15] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[16] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[17] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[18] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[19] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[1] (output)                    0.000000    0.272520    0.272520 (MET)
out_data[20] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[21] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[22] (output)                   0.000000    0.272520    0.272520 (MET)
out_data[23] (output)                   0.000000    0.272520    0.272520 (MET)

===== tt_100C_1v80 setup =====
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12027_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12029_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12032_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12033_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12034_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12035_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12036_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12037_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12038_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12039_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12040_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12041_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12042_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12043_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12044_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12045_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12047_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12048_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)
_12049_/D (sky130_fd_sc_hd__dfxtp_1)   27.721409   16.404186   11.317222 (MET)

===== tt_100C_1v80 hold =====
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
min_delay/hold group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.046173    0.043657    0.089830 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.042517    0.086198    0.128715 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.042517    0.102130    0.144647 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.046173    0.115240    0.161414 (MET)
... [已截断：共 351 行，保留开头 100 行和结尾 100 行] ...
_12039_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12040_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12041_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12042_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12043_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12044_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12045_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12047_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12048_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)
_12049_/D (sky130_fd_sc_hd__dfxtp_1)   27.796181   11.924675   15.871506 (MET)

===== ff_n40C_1v95 hold =====
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
min_delay/hold group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.036882    0.026590    0.063473 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.019113    0.061093    0.080206 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.019113    0.068928    0.088041 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.036882    0.073481    0.110364 (MET)
out_data[0] (output)                    0.000000    0.173251    0.173251 (MET)
out_data[10] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[11] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[12] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[13] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[14] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[15] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[16] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[17] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[18] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[19] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[1] (output)                    0.000000    0.173251    0.173251 (MET)
out_data[20] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[21] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[22] (output)                   0.000000    0.173251    0.173251 (MET)
out_data[23] (output)                   0.000000    0.173251    0.173251 (MET)

===== ff_100C_1v95 setup =====
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
max_delay/setup group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12027_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12029_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12032_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12033_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12034_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12035_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12036_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12037_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12038_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12039_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12040_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12041_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12042_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12043_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12044_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12045_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12047_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12048_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)
_12049_/D (sky130_fd_sc_hd__dfxtp_1)   27.804602   11.910374   15.894229 (MET)

===== ff_100C_1v95 hold =====
Warning 502: diag_query.tcl line 1, report_checks -endpoint_count is deprecated. Use -endpoint_path_count instead.
Warning 503: diag_query.tcl line 1, report_checks -group_count is deprecated. Use -group_path_count instead.
min_delay/hold group clk

                                        Required      Actual
Endpoint                                   Delay       Delay       Slack
------------------------------------------------------------------------
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.028147    0.030966    0.059113 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.020691    0.057390    0.078081 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.020691    0.069862    0.090553 (MET)
_12058_/D (sky130_fd_sc_hd__dfxtp_1)   -0.028147    0.074504    0.102651 (MET)
out_data[0] (output)                    0.000000    0.179844    0.179844 (MET)
out_data[10] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[11] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[12] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[13] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[14] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[15] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[16] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[17] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[18] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[19] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[1] (output)                    0.000000    0.179844    0.179844 (MET)
out_data[20] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[21] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[22] (output)                   0.000000    0.179844    0.179844 (MET)
out_data[23] (output)                   0.000000    0.179844    0.179844 (MET)

CASE01-CMD: report_design_area
CASE01-ERROR: invalid command name "report_design_area"
```
