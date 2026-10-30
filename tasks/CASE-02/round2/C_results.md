### 查询 C1（R1）
你写的查询：
```tcl
report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```
实际执行的命令：
```tcl
report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
No paths found.
```

### 查询 C2（R1）
你写的查询：
```tcl
report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60 -digits 4
```
实际执行的命令：
```tcl
report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60 -digits 4
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60 -digits 4
No paths found.
```

### 查询 C3（R2）
你写的查询：
```tcl
report_checks -from [get_ports {in_a[34]}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```
实际执行的命令：
```tcl
report_checks -from [get_ports {in_a[34]}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: report_checks -from [get_ports {in_a[34]}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
Startpoint: in_a[34] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

Fanout       Cap      Slew     Delay      Time   Description
-------------------------------------------------------------------------------------
                    0.0000    0.0000    0.0000   clock clk (rise edge)
                              0.0000    0.0000   clock network delay (ideal)
                              5.5820    5.5820 ^ input external delay
    17    0.0365    0.3844    0.2730    5.8550 ^ in_a[34] (in)
                    0.3844    0.0000    5.8550 ^ _10564_/A (sky130_fd_sc_hd__and2_0)
     2    0.0050    0.1742    0.4006    6.2556 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
                    0.1742    0.0000    6.2556 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
     2    0.0073    0.1346    1.0188    7.2744 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1346    0.0000    7.2744 v _10985_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0067    0.1357    0.9736    8.2480 v _10985_/X (sky130_fd_sc_hd__xor3_1)
                    0.1357    0.0000    8.2480 v _10986_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0077    0.4310    0.4475    8.6955 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
                    0.4310    0.0000    8.6955 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
     1    0.0023    0.2113    0.4045    9.1000 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
                    0.2113    0.0000    9.1000 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
     2    0.0073    0.2040    0.2403    9.3403 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
                    0.2040    0.0000    9.3403 v _11073_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0055    0.1259    0.9973   10.3376 v _11073_/X (sky130_fd_sc_hd__xor3_1)
                    0.1259    0.0000   10.3376 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
     2    0.0078    0.4964    0.5470   10.8846 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.4964    0.0000   10.8846 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
     2    0.0073    0.1346    0.9809   11.8655 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
                    0.1346    0.0000   11.8655 v _11302_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0073    0.1401    0.9794   12.8449 v _11302_/X (sky130_fd_sc_hd__xor3_1)
                    0.1401    0.0000   12.8449 v _11306_/B (sky130_fd_sc_hd__maj3_1)
     2    0.0073    0.1599    0.9433   13.7882 v _11306_/X (sky130_fd_sc_hd__maj3_1)
                    0.1599    0.0000   13.7882 v _11338_/B (sky130_fd_sc_hd__xor3_1)
     2    0.0061    0.1307    0.9799   14.7681 v _11338_/X (sky130_fd_sc_hd__xor3_1)
                    0.1307    0.0000   14.7681 v _11340_/B (sky130_fd_sc_hd__xor2_1)
     2    0.0065    0.3820    0.4077   15.1758 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
                    0.3820    0.0000   15.1758 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1299    0.2608   15.4366 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1299    0.0000   15.4366 v _11418_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0055    0.1444    0.9285   16.3652 v _11418_/X (sky130_fd_sc_hd__maj3_1)
                    0.1444    0.0000   16.3652 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
     2    0.0063    0.4984    0.5449   16.9101 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.4984    0.0000   16.9101 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0065    0.1750    0.5349   17.4450 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
                    0.1750    0.0000   17.4450 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0067    0.1381    0.1799   17.6249 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1381    0.0000   17.6249 v _11423_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0067    0.1552    0.9453   18.5701 v _11423_/X (sky130_fd_sc_hd__maj3_1)
                    0.1552    0.0000   18.5701 v _11424_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0056    0.1456    0.9406   19.5107 v _11424_/X (sky130_fd_sc_hd__maj3_1)
                    0.1456    0.0000   19.5107 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5098    0.5289   20.0396 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5098    0.0000   20.0396 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
     2    0.0069    0.1331    0.3197   20.3593 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1331    0.0000   20.3593 v _11428_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0069    0.1564    0.9447   21.3040 v _11428_/X (sky130_fd_sc_hd__maj3_1)
                    0.1564    0.0000   21.3040 v _11429_/C (sky130_fd_sc_hd__maj3_1)
     2    0.0061    0.1494    0.9456   22.2496 v _11429_/X (sky130_fd_sc_hd__maj3_1)
                    0.1494    0.0000   22.2496 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
     2    0.0065    0.3918    0.4391   22.6887 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
                    0.3918    0.0000   22.6887 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0050    0.1137    0.2517   22.9404 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1137    0.0000   22.9404 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
     2    0.0065    0.5099    0.5119   23.4524 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.5099    0.0000   23.4524 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
     3    0.0084    0.1479    0.3357   23.7880 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
                    0.1479    0.0000   23.7880 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
     3    0.0088    0.8527    0.8462   24.6343 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
                    0.8527    0.0000   24.6343 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
     3    0.0058    0.1806    0.4326   25.0668 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
                    0.1806    0.0000   25.0668 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
     3    0.0068    1.0230    1.0241   26.0910 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
                    1.0230    0.0000   26.0910 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
     3    0.0042    0.1761    0.4919   26.5829 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
                    0.1761    0.0000   26.5829 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
     2    0.0045    0.7912    0.8376   27.4205 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
                    0.7912    0.0000   27.4205 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
     1    0.0041    0.1315    0.3533   27.7737 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
                    0.1315    0.0000   27.7737 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
     2    0.0037    0.0814    0.2543   28.0280 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
                    0.0814    0.0000   28.0280 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
    31    0.0511    3.2455    2.6362   30.6642 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
                    3.2455    0.0000   30.6642 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
     1    0.0015    0.3761    0.8625   31.5267 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
                    0.3761    0.0000   31.5267 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
                                       31.5267   data arrival time

                    0.0000   27.9100   27.9100   clock clk (rise edge)
                              0.0000   27.9100   clock network delay (ideal)
                              0.0000   27.9100   clock reconvergence pessimism
                                       27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
                             -0.5559   27.3541   library setup time
                                       27.3541   data required time
-------------------------------------------------------------------------------------
                                       27.3541   data required time
                                      -31.5267   data arrival time
-------------------------------------------------------------------------------------
                                       -4.1726   slack (VIOLATED)
```

### 查询 C4（R1）
你写的查询：
```tcl
check_setup
```
实际执行的命令：
```tcl
check_setup
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: check_setup
Warning: There are 64 input ports missing set_input_delay.
0
```

### 查询 C4（R2）
你写的查询：
```tcl
check_setup
```
实际执行的命令：
```tcl
check_setup
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: check_setup
1
```

### 查询 C5（R1）
你写的查询：
```tcl
foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene ss_n40C_1v60 }
```
实际执行的命令：
```tcl
foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene ss_n40C_1v60 }
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene ss_n40C_1v60 }
PORT rst
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_valid
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[63]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[62]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[61]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[60]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[59]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[58]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[57]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[56]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[55]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[54]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[53]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[52]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[51]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[50]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[49]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[48]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[47]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[46]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[45]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[44]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[43]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[42]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[41]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[40]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[39]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[38]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[37]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[36]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[35]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[34]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[33]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[32]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[31]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[30]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[29]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[28]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[27]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[26]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[25]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[24]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[23]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[22]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[21]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[20]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[19]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[18]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[17]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[16]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[15]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[14]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[13]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[12]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[11]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[10]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[9]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[8]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[7]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[6]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[5]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[4]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[3]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[2]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[1]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[0]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[63]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[62]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[61]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[60]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[59]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[58]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[57]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[56]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[55]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[54]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[53]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[52]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[51]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[50]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[49]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[48]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[47]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[46]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[45]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[44]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[43]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[42]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[41]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[40]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[39]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[38]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[37]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[36]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[35]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[34]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[33]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[32]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[31]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[30]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[29]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[28]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[27]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[26]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[25]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[24]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[23]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[22]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[21]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[20]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[19]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[18]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[17]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[16]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[15]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[14]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[13]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[12]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[11]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[10]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[9]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[8]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[7]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[6]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[5]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[4]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[3]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[2]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[1]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[0]
 r 0.00:0.00 f 0.00:0.00
```

### 查询 C5（R2）
你写的查询：
```tcl
foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene ss_n40C_1v60 }
```
实际执行的命令：
```tcl
foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene ss_n40C_1v60 }
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene ss_n40C_1v60 }
PORT rst
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_valid
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[63]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[62]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[61]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[60]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[59]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[58]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[57]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[56]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[55]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[54]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[53]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[52]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[51]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[50]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[49]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[48]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[47]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[46]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[45]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[44]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[43]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[42]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[41]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[40]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[39]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[38]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[37]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[36]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[35]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[34]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[33]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[32]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[31]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[30]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[29]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[28]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[27]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[26]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[25]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[24]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[23]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[22]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[21]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[20]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[19]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[18]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[17]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[16]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[15]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[14]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[13]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[12]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[11]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[10]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[9]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[8]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[7]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[6]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[5]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[4]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[3]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[2]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[1]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[0]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[63]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[62]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[61]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[60]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[59]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[58]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[57]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[56]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[55]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[54]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[53]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[52]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[51]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[50]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[49]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[48]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[47]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[46]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[45]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[44]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[43]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[42]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[41]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[40]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[39]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[38]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[37]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[36]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[35]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[34]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[33]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[32]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[31]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[30]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[29]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[28]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[27]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[26]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[25]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[24]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[23]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[22]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[21]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[20]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[19]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[18]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[17]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[16]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[15]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[14]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[13]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[12]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[11]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[10]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[9]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[8]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[7]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[6]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[5]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[4]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[3]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[2]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[1]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[0]
(clk ^) r 0.00:5.58 f 0.00:5.58
```

### 查询 C6（R1）
你写的查询：
```tcl
foreach p [all_inputs -no_clocks] { set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60]]; set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -unconstrained -scene ss_n40C_1v60]]; set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60]]; set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -unconstrained -scene ss_n40C_1v60]]; puts "[get_full_name $p] max=$n1 max_unc=$n2 min=$n3 min_unc=$n4" }
```
实际执行的命令：
```tcl
foreach p [all_inputs -no_clocks] { set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60]]; set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -unconstrained -scene ss_n40C_1v60]]; set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60]]; set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -unconstrained -scene ss_n40C_1v60]]; puts "[get_full_name $p] max=$n1 max_unc=$n2 min=$n3 min_unc=$n4" }
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: foreach p [all_inputs -no_clocks] { set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60]]; set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -unconstrained -scene ss_n40C_1v60]]; set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60]]; set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -unconstrained -scene ss_n40C_1v60]]; puts "[get_full_name $p] max=$n1 max_unc=$n2 min=$n3 min_unc=$n4" }
rst max=1 max_unc=1 min=1 min_unc=1
in_valid max=1 max_unc=1 min=1 min_unc=1
in_a[63] max=1 max_unc=1 min=1 min_unc=1
in_a[62] max=1 max_unc=1 min=1 min_unc=1
in_a[61] max=1 max_unc=1 min=1 min_unc=1
in_a[60] max=1 max_unc=1 min=1 min_unc=1
in_a[59] max=1 max_unc=1 min=1 min_unc=1
in_a[58] max=1 max_unc=1 min=1 min_unc=1
in_a[57] max=1 max_unc=1 min=1 min_unc=1
in_a[56] max=1 max_unc=1 min=1 min_unc=1
in_a[55] max=1 max_unc=1 min=1 min_unc=1
in_a[54] max=1 max_unc=1 min=1 min_unc=1
in_a[53] max=1 max_unc=1 min=1 min_unc=1
in_a[52] max=1 max_unc=1 min=1 min_unc=1
in_a[51] max=1 max_unc=1 min=1 min_unc=1
in_a[50] max=1 max_unc=1 min=1 min_unc=1
in_a[49] max=1 max_unc=1 min=1 min_unc=1
in_a[48] max=1 max_unc=1 min=1 min_unc=1
in_a[47] max=1 max_unc=1 min=1 min_unc=1
in_a[46] max=1 max_unc=1 min=1 min_unc=1
in_a[45] max=1 max_unc=1 min=1 min_unc=1
in_a[44] max=1 max_unc=1 min=1 min_unc=1
in_a[43] max=1 max_unc=1 min=1 min_unc=1
in_a[42] max=1 max_unc=1 min=1 min_unc=1
in_a[41] max=1 max_unc=1 min=1 min_unc=1
in_a[40] max=1 max_unc=1 min=1 min_unc=1
in_a[39] max=1 max_unc=1 min=1 min_unc=1
in_a[38] max=1 max_unc=1 min=1 min_unc=1
in_a[37] max=1 max_unc=1 min=1 min_unc=1
in_a[36] max=1 max_unc=1 min=1 min_unc=1
in_a[35] max=1 max_unc=1 min=1 min_unc=1
in_a[34] max=1 max_unc=1 min=1 min_unc=1
in_a[33] max=1 max_unc=1 min=1 min_unc=1
in_a[32] max=1 max_unc=1 min=1 min_unc=1
in_a[31] max=1 max_unc=1 min=1 min_unc=1
in_a[30] max=1 max_unc=1 min=1 min_unc=1
in_a[29] max=1 max_unc=1 min=1 min_unc=1
in_a[28] max=1 max_unc=1 min=1 min_unc=1
in_a[27] max=1 max_unc=1 min=1 min_unc=1
in_a[26] max=1 max_unc=1 min=1 min_unc=1
in_a[25] max=1 max_unc=1 min=1 min_unc=1
in_a[24] max=1 max_unc=1 min=1 min_unc=1
in_a[23] max=1 max_unc=1 min=1 min_unc=1
in_a[22] max=1 max_unc=1 min=1 min_unc=1
in_a[21] max=1 max_unc=1 min=1 min_unc=1
in_a[20] max=1 max_unc=1 min=1 min_unc=1
in_a[19] max=1 max_unc=1 min=1 min_unc=1
in_a[18] max=1 max_unc=1 min=1 min_unc=1
in_a[17] max=1 max_unc=1 min=1 min_unc=1
in_a[16] max=1 max_unc=1 min=1 min_unc=1
in_a[15] max=1 max_unc=1 min=1 min_unc=1
in_a[14] max=1 max_unc=1 min=1 min_unc=1
in_a[13] max=1 max_unc=1 min=1 min_unc=1
in_a[12] max=1 max_unc=1 min=1 min_unc=1
in_a[11] max=1 max_unc=1 min=1 min_unc=1
in_a[10] max=1 max_unc=1 min=1 min_unc=1
in_a[9] max=1 max_unc=1 min=1 min_unc=1
in_a[8] max=1 max_unc=1 min=1 min_unc=1
in_a[7] max=1 max_unc=1 min=1 min_unc=1
in_a[6] max=1 max_unc=1 min=1 min_unc=1
in_a[5] max=1 max_unc=1 min=1 min_unc=1
in_a[4] max=1 max_unc=1 min=1 min_unc=1
in_a[3] max=1 max_unc=1 min=1 min_unc=1
in_a[2] max=1 max_unc=1 min=1 min_unc=1
in_a[1] max=1 max_unc=1 min=1 min_unc=1
in_a[0] max=1 max_unc=1 min=1 min_unc=1
in_b[63] max=0 max_unc=1 min=0 min_unc=1
in_b[62] max=0 max_unc=1 min=0 min_unc=1
in_b[61] max=0 max_unc=1 min=0 min_unc=1
in_b[60] max=0 max_unc=1 min=0 min_unc=1
in_b[59] max=0 max_unc=1 min=0 min_unc=1
in_b[58] max=0 max_unc=1 min=0 min_unc=1
in_b[57] max=0 max_unc=1 min=0 min_unc=1
in_b[56] max=0 max_unc=1 min=0 min_unc=1
in_b[55] max=0 max_unc=1 min=0 min_unc=1
in_b[54] max=0 max_unc=1 min=0 min_unc=1
in_b[53] max=0 max_unc=1 min=0 min_unc=1
in_b[52] max=0 max_unc=1 min=0 min_unc=1
in_b[51] max=0 max_unc=1 min=0 min_unc=1
in_b[50] max=0 max_unc=1 min=0 min_unc=1
in_b[49] max=0 max_unc=1 min=0 min_unc=1
in_b[48] max=0 max_unc=1 min=0 min_unc=1
in_b[47] max=0 max_unc=1 min=0 min_unc=1
in_b[46] max=0 max_unc=1 min=0 min_unc=1
in_b[45] max=0 max_unc=1 min=0 min_unc=1
in_b[44] max=0 max_unc=1 min=0 min_unc=1
in_b[43] max=0 max_unc=1 min=0 min_unc=1
in_b[42] max=0 max_unc=1 min=0 min_unc=1
in_b[41] max=0 max_unc=1 min=0 min_unc=1
in_b[40] max=0 max_unc=1 min=0 min_unc=1
in_b[39] max=0 max_unc=1 min=0 min_unc=1
in_b[38] max=0 max_unc=1 min=0 min_unc=1
in_b[37] max=0 max_unc=1 min=0 min_unc=1
in_b[36] max=0 max_unc=1 min=0 min_unc=1
in_b[35] max=0 max_unc=1 min=0 min_unc=1
in_b[34] max=0 max_unc=1 min=0 min_unc=1
in_b[33] max=0 max_unc=1 min=0 min_unc=1
in_b[32] max=0 max_unc=1 min=0 min_unc=1
in_b[31] max=0 max_unc=1 min=0 min_unc=1
in_b[30] max=0 max_unc=1 min=0 min_unc=1
in_b[29] max=0 max_unc=1 min=0 min_unc=1
in_b[28] max=0 max_unc=1 min=0 min_unc=1
in_b[27] max=0 max_unc=1 min=0 min_unc=1
in_b[26] max=0 max_unc=1 min=0 min_unc=1
in_b[25] max=0 max_unc=1 min=0 min_unc=1
in_b[24] max=0 max_unc=1 min=0 min_unc=1
in_b[23] max=0 max_unc=1 min=0 min_unc=1
in_b[22] max=0 max_unc=1 min=0 min_unc=1
in_b[21] max=0 max_unc=1 min=0 min_unc=1
in_b[20] max=0 max_unc=1 min=0 min_unc=1
in_b[19] max=0 max_unc=1 min=0 min_unc=1
in_b[18] max=0 max_unc=1 min=0 min_unc=1
in_b[17] max=0 max_unc=1 min=0 min_unc=1
in_b[16] max=0 max_unc=1 min=0 min_unc=1
in_b[15] max=0 max_unc=1 min=0 min_unc=1
in_b[14] max=0 max_unc=1 min=0 min_unc=1
in_b[13] max=0 max_unc=1 min=0 min_unc=1
in_b[12] max=0 max_unc=1 min=0 min_unc=1
in_b[11] max=0 max_unc=1 min=0 min_unc=1
in_b[10] max=0 max_unc=1 min=0 min_unc=1
in_b[9] max=0 max_unc=1 min=0 min_unc=1
in_b[8] max=0 max_unc=1 min=0 min_unc=1
in_b[7] max=0 max_unc=1 min=0 min_unc=1
in_b[6] max=0 max_unc=1 min=0 min_unc=1
in_b[5] max=0 max_unc=1 min=0 min_unc=1
in_b[4] max=0 max_unc=1 min=0 min_unc=1
in_b[3] max=0 max_unc=1 min=0 min_unc=1
in_b[2] max=0 max_unc=1 min=0 min_unc=1
in_b[1] max=0 max_unc=1 min=0 min_unc=1
in_b[0] max=0 max_unc=1 min=0 min_unc=1
```

### 查询 C6（R2）
你写的查询：
```tcl
foreach p [all_inputs -no_clocks] { set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60]]; set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -unconstrained -scene ss_n40C_1v60]]; set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60]]; set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -unconstrained -scene ss_n40C_1v60]]; puts "[get_full_name $p] max=$n1 max_unc=$n2 min=$n3 min_unc=$n4" }
```
实际执行的命令：
```tcl
foreach p [all_inputs -no_clocks] { set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60]]; set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -unconstrained -scene ss_n40C_1v60]]; set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60]]; set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -unconstrained -scene ss_n40C_1v60]]; puts "[get_full_name $p] max=$n1 max_unc=$n2 min=$n3 min_unc=$n4" }
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: foreach p [all_inputs -no_clocks] { set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60]]; set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay max -unconstrained -scene ss_n40C_1v60]]; set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60]]; set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] -path_delay min -unconstrained -scene ss_n40C_1v60]]; puts "[get_full_name $p] max=$n1 max_unc=$n2 min=$n3 min_unc=$n4" }
rst max=1 max_unc=1 min=1 min_unc=1
in_valid max=1 max_unc=1 min=1 min_unc=1
in_a[63] max=1 max_unc=1 min=1 min_unc=1
in_a[62] max=1 max_unc=1 min=1 min_unc=1
in_a[61] max=1 max_unc=1 min=1 min_unc=1
in_a[60] max=1 max_unc=1 min=1 min_unc=1
in_a[59] max=1 max_unc=1 min=1 min_unc=1
in_a[58] max=1 max_unc=1 min=1 min_unc=1
in_a[57] max=1 max_unc=1 min=1 min_unc=1
in_a[56] max=1 max_unc=1 min=1 min_unc=1
in_a[55] max=1 max_unc=1 min=1 min_unc=1
in_a[54] max=1 max_unc=1 min=1 min_unc=1
in_a[53] max=1 max_unc=1 min=1 min_unc=1
in_a[52] max=1 max_unc=1 min=1 min_unc=1
in_a[51] max=1 max_unc=1 min=1 min_unc=1
in_a[50] max=1 max_unc=1 min=1 min_unc=1
in_a[49] max=1 max_unc=1 min=1 min_unc=1
in_a[48] max=1 max_unc=1 min=1 min_unc=1
in_a[47] max=1 max_unc=1 min=1 min_unc=1
in_a[46] max=1 max_unc=1 min=1 min_unc=1
in_a[45] max=1 max_unc=1 min=1 min_unc=1
in_a[44] max=1 max_unc=1 min=1 min_unc=1
in_a[43] max=1 max_unc=1 min=1 min_unc=1
in_a[42] max=1 max_unc=1 min=1 min_unc=1
in_a[41] max=1 max_unc=1 min=1 min_unc=1
in_a[40] max=1 max_unc=1 min=1 min_unc=1
in_a[39] max=1 max_unc=1 min=1 min_unc=1
in_a[38] max=1 max_unc=1 min=1 min_unc=1
in_a[37] max=1 max_unc=1 min=1 min_unc=1
in_a[36] max=1 max_unc=1 min=1 min_unc=1
in_a[35] max=1 max_unc=1 min=1 min_unc=1
in_a[34] max=1 max_unc=1 min=1 min_unc=1
in_a[33] max=1 max_unc=1 min=1 min_unc=1
in_a[32] max=1 max_unc=1 min=1 min_unc=1
in_a[31] max=1 max_unc=1 min=1 min_unc=1
in_a[30] max=1 max_unc=1 min=1 min_unc=1
in_a[29] max=1 max_unc=1 min=1 min_unc=1
in_a[28] max=1 max_unc=1 min=1 min_unc=1
in_a[27] max=1 max_unc=1 min=1 min_unc=1
in_a[26] max=1 max_unc=1 min=1 min_unc=1
in_a[25] max=1 max_unc=1 min=1 min_unc=1
in_a[24] max=1 max_unc=1 min=1 min_unc=1
in_a[23] max=1 max_unc=1 min=1 min_unc=1
in_a[22] max=1 max_unc=1 min=1 min_unc=1
in_a[21] max=1 max_unc=1 min=1 min_unc=1
in_a[20] max=1 max_unc=1 min=1 min_unc=1
in_a[19] max=1 max_unc=1 min=1 min_unc=1
in_a[18] max=1 max_unc=1 min=1 min_unc=1
in_a[17] max=1 max_unc=1 min=1 min_unc=1
in_a[16] max=1 max_unc=1 min=1 min_unc=1
in_a[15] max=1 max_unc=1 min=1 min_unc=1
in_a[14] max=1 max_unc=1 min=1 min_unc=1
in_a[13] max=1 max_unc=1 min=1 min_unc=1
in_a[12] max=1 max_unc=1 min=1 min_unc=1
in_a[11] max=1 max_unc=1 min=1 min_unc=1
in_a[10] max=1 max_unc=1 min=1 min_unc=1
in_a[9] max=1 max_unc=1 min=1 min_unc=1
in_a[8] max=1 max_unc=1 min=1 min_unc=1
in_a[7] max=1 max_unc=1 min=1 min_unc=1
in_a[6] max=1 max_unc=1 min=1 min_unc=1
in_a[5] max=1 max_unc=1 min=1 min_unc=1
in_a[4] max=1 max_unc=1 min=1 min_unc=1
in_a[3] max=1 max_unc=1 min=1 min_unc=1
in_a[2] max=1 max_unc=1 min=1 min_unc=1
in_a[1] max=1 max_unc=1 min=1 min_unc=1
in_a[0] max=1 max_unc=1 min=1 min_unc=1
in_b[63] max=1 max_unc=1 min=1 min_unc=1
in_b[62] max=1 max_unc=1 min=1 min_unc=1
in_b[61] max=1 max_unc=1 min=1 min_unc=1
in_b[60] max=1 max_unc=1 min=1 min_unc=1
in_b[59] max=1 max_unc=1 min=1 min_unc=1
in_b[58] max=1 max_unc=1 min=1 min_unc=1
in_b[57] max=1 max_unc=1 min=1 min_unc=1
in_b[56] max=1 max_unc=1 min=1 min_unc=1
in_b[55] max=1 max_unc=1 min=1 min_unc=1
in_b[54] max=1 max_unc=1 min=1 min_unc=1
in_b[53] max=1 max_unc=1 min=1 min_unc=1
in_b[52] max=1 max_unc=1 min=1 min_unc=1
in_b[51] max=1 max_unc=1 min=1 min_unc=1
in_b[50] max=1 max_unc=1 min=1 min_unc=1
in_b[49] max=1 max_unc=1 min=1 min_unc=1
in_b[48] max=1 max_unc=1 min=1 min_unc=1
in_b[47] max=1 max_unc=1 min=1 min_unc=1
in_b[46] max=1 max_unc=1 min=1 min_unc=1
in_b[45] max=1 max_unc=1 min=1 min_unc=1
in_b[44] max=1 max_unc=1 min=1 min_unc=1
in_b[43] max=1 max_unc=1 min=1 min_unc=1
in_b[42] max=1 max_unc=1 min=1 min_unc=1
in_b[41] max=1 max_unc=1 min=1 min_unc=1
in_b[40] max=1 max_unc=1 min=1 min_unc=1
in_b[39] max=1 max_unc=1 min=1 min_unc=1
in_b[38] max=1 max_unc=1 min=1 min_unc=1
in_b[37] max=1 max_unc=1 min=1 min_unc=1
in_b[36] max=1 max_unc=1 min=1 min_unc=1
in_b[35] max=1 max_unc=1 min=1 min_unc=1
in_b[34] max=1 max_unc=1 min=1 min_unc=1
in_b[33] max=1 max_unc=1 min=1 min_unc=1
in_b[32] max=1 max_unc=1 min=1 min_unc=1
in_b[31] max=1 max_unc=1 min=1 min_unc=1
in_b[30] max=1 max_unc=1 min=1 min_unc=1
in_b[29] max=1 max_unc=1 min=1 min_unc=1
in_b[28] max=1 max_unc=1 min=1 min_unc=1
in_b[27] max=1 max_unc=1 min=1 min_unc=1
in_b[26] max=1 max_unc=1 min=1 min_unc=1
in_b[25] max=1 max_unc=1 min=1 min_unc=1
in_b[24] max=1 max_unc=1 min=1 min_unc=1
in_b[23] max=1 max_unc=1 min=1 min_unc=1
in_b[22] max=1 max_unc=1 min=1 min_unc=1
in_b[21] max=1 max_unc=1 min=1 min_unc=1
in_b[20] max=1 max_unc=1 min=1 min_unc=1
in_b[19] max=1 max_unc=1 min=1 min_unc=1
in_b[18] max=1 max_unc=1 min=1 min_unc=1
in_b[17] max=1 max_unc=1 min=1 min_unc=1
in_b[16] max=1 max_unc=1 min=1 min_unc=1
in_b[15] max=1 max_unc=1 min=1 min_unc=1
in_b[14] max=1 max_unc=1 min=1 min_unc=1
in_b[13] max=1 max_unc=1 min=1 min_unc=1
in_b[12] max=1 max_unc=1 min=1 min_unc=1
in_b[11] max=1 max_unc=1 min=1 min_unc=1
in_b[10] max=1 max_unc=1 min=1 min_unc=1
in_b[9] max=1 max_unc=1 min=1 min_unc=1
in_b[8] max=1 max_unc=1 min=1 min_unc=1
in_b[7] max=1 max_unc=1 min=1 min_unc=1
in_b[6] max=1 max_unc=1 min=1 min_unc=1
in_b[5] max=1 max_unc=1 min=1 min_unc=1
in_b[4] max=1 max_unc=1 min=1 min_unc=1
in_b[3] max=1 max_unc=1 min=1 min_unc=1
in_b[2] max=1 max_unc=1 min=1 min_unc=1
in_b[1] max=1 max_unc=1 min=1 min_unc=1
in_b[0] max=1 max_unc=1 min=1 min_unc=1
```

### 查询 C7（R1）
你写的查询：
```tcl
report_checks -from [get_ports in_b*] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
```
实际执行的命令：
```tcl
report_checks -from [get_ports in_b*] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: report_checks -from [get_ports in_b*] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
No paths found.
```

### 查询 C8（R1）
你写的查询：
```tcl
report_checks -from [get_ports {in_b[35]}] -to [all_registers -data_pins] -path_delay max -scene tt_025C_1v80 -digits 4
```
实际执行的命令：
```tcl
report_checks -from [get_ports {in_b[35]}] -to [all_registers -data_pins] -path_delay max -scene tt_025C_1v80 -digits 4
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: report_checks -from [get_ports {in_b[35]}] -to [all_registers -data_pins] -path_delay max -scene tt_025C_1v80 -digits 4
No paths found.
```

### 查询 C9（R1）
你写的查询：
```tcl
foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene tt_025C_1v80 }
```
实际执行的命令：
```tcl
foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene tt_025C_1v80 }
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene tt_025C_1v80 }
PORT rst
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_valid
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[63]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[62]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[61]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[60]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[59]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[58]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[57]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[56]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[55]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[54]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[53]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[52]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[51]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[50]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[49]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[48]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[47]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[46]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[45]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[44]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[43]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[42]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[41]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[40]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[39]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[38]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[37]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[36]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[35]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[34]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[33]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[32]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[31]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[30]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[29]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[28]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[27]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[26]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[25]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[24]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[23]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[22]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[21]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[20]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[19]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[18]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[17]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[16]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[15]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[14]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[13]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[12]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[11]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[10]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[9]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[8]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[7]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[6]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[5]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[4]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[3]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[2]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[1]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[0]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[63]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[62]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[61]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[60]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[59]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[58]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[57]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[56]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[55]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[54]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[53]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[52]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[51]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[50]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[49]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[48]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[47]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[46]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[45]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[44]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[43]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[42]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[41]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[40]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[39]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[38]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[37]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[36]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[35]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[34]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[33]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[32]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[31]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[30]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[29]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[28]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[27]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[26]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[25]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[24]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[23]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[22]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[21]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[20]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[19]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[18]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[17]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[16]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[15]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[14]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[13]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[12]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[11]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[10]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[9]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[8]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[7]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[6]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[5]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[4]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[3]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[2]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[1]
 r 0.00:0.00 f 0.00:0.00
PORT in_b[0]
 r 0.00:0.00 f 0.00:0.00
```

### 查询 C9（R2）
你写的查询：
```tcl
foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene tt_025C_1v80 }
```
实际执行的命令：
```tcl
foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene tt_025C_1v80 }
```
机械改写：无
执行类型：原上下文；执行结果：完成；异常：-；归因：-
输出：
```text
CASE02-CMD: foreach p [all_inputs -no_clocks] { puts "PORT [get_full_name $p]"; report_arrival $p -scene tt_025C_1v80 }
PORT rst
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_valid
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[63]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[62]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[61]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[60]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[59]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[58]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[57]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[56]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[55]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[54]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[53]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[52]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[51]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[50]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[49]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[48]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[47]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[46]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[45]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[44]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[43]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[42]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[41]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[40]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[39]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[38]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[37]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[36]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[35]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[34]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[33]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[32]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[31]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[30]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[29]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[28]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[27]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[26]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[25]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[24]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[23]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[22]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[21]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[20]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[19]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[18]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[17]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[16]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[15]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[14]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[13]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[12]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[11]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[10]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[9]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[8]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[7]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[6]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[5]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[4]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[3]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[2]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[1]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_a[0]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[63]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[62]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[61]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[60]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[59]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[58]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[57]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[56]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[55]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[54]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[53]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[52]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[51]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[50]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[49]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[48]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[47]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[46]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[45]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[44]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[43]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[42]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[41]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[40]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[39]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[38]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[37]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[36]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[35]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[34]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[33]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[32]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[31]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[30]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[29]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[28]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[27]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[26]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[25]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[24]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[23]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[22]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[21]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[20]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[19]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[18]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[17]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[16]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[15]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[14]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[13]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[12]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[11]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[10]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[9]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[8]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[7]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[6]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[5]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[4]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[3]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[2]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[1]
(clk ^) r 0.00:5.58 f 0.00:5.58
PORT in_b[0]
(clk ^) r 0.00:5.58 f 0.00:5.58
```

## 预算账单

① 总预算：600000 token（每 token 约 1.91 字节的保守换算；本次已交还合计 27257 token，含本账单）。

② 已交还的实例：
- C1 R1：2 行，未截断
- C2 R1：2 行，未截断
- C3 R2：103 行，未截断
- C4 R1：3 行，未截断
- C4 R2：2 行，未截断
- C5 R1：261 行，未截断
- C5 R2：261 行，未截断
- C6 R1：131 行，未截断
- C6 R2：131 行，未截断
- C7 R1：2 行，未截断
- C8 R1：2 行，未截断
- C9 R1：261 行，未截断
- C9 R2：261 行，未截断

③ 未交还的实例：（无）

④ 以上未交还的结果已完整归档，未交还原因是累计超过公开的总预算，不是查询失败。
