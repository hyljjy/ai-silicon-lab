### 查询 A1
你写的查询：
```tcl
report_instance _12026_
report_net -digits 4 [get_nets -of_objects [get_pins _12026_/Q]]
report_net -digits 4 [get_nets -of_objects [get_pins _12026_/D]]
```
实际执行的命令：
```tcl
report_instance _12026_
report_net -digits 4 [get_nets -of_objects [get_pins _12026_/Q]]
report_net -digits 4 [get_nets -of_objects [get_pins _12026_/D]]
```
机械改写：无
结果代码：对象不存在
输出：
```text
CASE01-CMD: report_instance _12026_
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
CASE01-CMD: report_net -digits 4 [get_nets -of_objects [get_pins _12026_/Q]]
CASE01-ERROR: Error 232: diag_query.tcl line 1, net _90a868d621610000_p_Net not found.
CASE01-CMD: report_net -digits 4 [get_nets -of_objects [get_pins _12026_/D]]
CASE01-ERROR: Error 232: diag_query.tcl line 1, net _f0fbbad621610000_p_Net not found.
```

### 查询 A2
你写的查询：
```tcl
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
  -scene ss_n40C_1v60 -group_path_count 200 -endpoint_path_count 1 -slack_max 0 -format end -digits 4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
  -scene ss_100C_1v60 -group_path_count 200 -endpoint_path_count 1 -slack_max 0 -format end -digits 4
set ps [find_timing_paths -scenes ss_n40C_1v60 -path_delay max -group_path_count 1000 -endpoint_path_count 1 -slack_max 0]
puts [llength $ps]
report_tns -digits 4   ;# 无场景选项，结果对应全部场景（不确定是取最差还是汇总）
```
实际执行的命令：
```tcl
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
  -scene ss_n40C_1v60 -group_path_count 200 -endpoint_path_count 1 -slack_max 0 -format end -digits 4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
  -scene ss_100C_1v60 -group_path_count 200 -endpoint_path_count 1 -slack_max 0 -format end -digits 4
set ps [find_timing_paths -scenes ss_n40C_1v60 -path_delay max -group_path_count 1000 -endpoint_path_count 1 -slack_max 0]
puts [llength $ps]
report_tns -digits 4   ;# 无场景选项，结果对应全部场景（不确定是取最差还是汇总）
```
机械改写：无
结果代码：已执行
输出：
```text
CASE01-CMD: report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
max_delay/setup group clk

                                      Required    Actual
Endpoint                                 Delay     Delay     Slack
------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12027_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12029_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12032_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12033_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12034_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12035_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12036_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12037_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12038_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12039_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12040_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12041_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12042_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12043_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12044_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12045_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12047_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12048_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12049_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12050_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12051_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12052_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12053_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12054_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12055_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12056_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12028_/D (sky130_fd_sc_hd__dfxtp_1)   27.3794   31.4791   -4.0997 (VIOLATED)
_12030_/D (sky130_fd_sc_hd__dfxtp_1)   27.3794   31.4791   -4.0997 (VIOLATED)
_12031_/D (sky130_fd_sc_hd__dfxtp_1)   27.3794   31.4791   -4.0997 (VIOLATED)
_12046_/D (sky130_fd_sc_hd__dfxtp_1)   27.3794   31.4791   -4.0997 (VIOLATED)
_12057_/D (sky130_fd_sc_hd__dfxtp_1)   27.5277   28.4953   -0.9676 (VIOLATED)

CASE01-CMD: report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
max_delay/setup group clk

                                      Required    Actual
Endpoint                                 Delay     Delay     Slack
------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12027_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12029_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12032_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12033_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12034_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12035_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12036_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12037_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12038_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12039_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12040_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12041_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12042_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12043_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12044_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12045_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12047_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12048_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12049_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12050_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12051_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12052_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12053_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12054_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12055_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12056_/D (sky130_fd_sc_hd__dfxtp_1)   27.4741   28.1613   -0.6873 (VIOLATED)
_12028_/D (sky130_fd_sc_hd__dfxtp_1)   27.4858   28.1545   -0.6687 (VIOLATED)
_12030_/D (sky130_fd_sc_hd__dfxtp_1)   27.4858   28.1545   -0.6687 (VIOLATED)
_12031_/D (sky130_fd_sc_hd__dfxtp_1)   27.4858   28.1545   -0.6687 (VIOLATED)
_12046_/D (sky130_fd_sc_hd__dfxtp_1)   27.4858   28.1545   -0.6687 (VIOLATED)

CASE01-CMD: set ps [find_timing_paths -scenes ss_n40C_1v60 -path_delay max -group_path_count 1000 -endpoint_path_count 1 -slack_max 0]
_d0683eda33610000_p_PathEnd _0063bbd833610000_p_PathEnd _c06241da33610000_p_PathEnd _f097eed833610000_p_PathEnd _00ec35da33610000_p_PathEnd _906041da33610000_p_PathEnd _605d41da33610000_p_PathEnd _d0f68bd233610000_p_PathEnd _c0d7a7d933610000_p_PathEnd _803deed833610000_p_PathEnd _907ae5d833610000_p_PathEnd _7013f4d933610000_p_PathEnd _b01b95d933610000_p_PathEnd _60ae19d933610000_p_PathEnd _e06613d933610000_p_PathEnd _704d09da33610000_p_PathEnd _a0ee1ad933610000_p_PathEnd _f08d02d933610000_p_PathEnd _10cc2bd933610000_p_PathEnd _50b1e0d933610000_p_PathEnd _504f1ad933610000_p_PathEnd _90392cd933610000_p_PathEnd _c05207da33610000_p_PathEnd _d09705da33610000_p_PathEnd _e0d410da33610000_p_PathEnd _d01701da33610000_p_PathEnd _a0ff0bda33610000_p_PathEnd _a06141da33610000_p_PathEnd _206341da33610000_p_PathEnd _d0809ed733610000_p_PathEnd _901a00d933610000_p_PathEnd _30daafd933610000_p_PathEnd
CASE01-CMD: puts [llength $ps]
32
CASE01-CMD: report_tns -digits 4   ;# 无场景选项，结果对应全部场景（不确定是取最差还是汇总）
tns max -130.4888
```

### 查询 A3
你写的查询：
```tcl
report_instance _11509_
report_net -digits 4 [get_nets -of_objects [get_pins _11509_/Y]]
report_checks -through [get_pins _11509_/Y] -path_delay max -scene ss_n40C_1v60 \
  -group_path_count 40 -endpoint_path_count 1 -format end -digits 4
```
实际执行的命令：
```tcl
report_instance _11509_
report_net -digits 4 [get_nets -of_objects [get_pins _11509_/Y]]
report_checks -through [get_pins _11509_/Y] -path_delay max -scene ss_n40C_1v60 \
  -group_path_count 40 -endpoint_path_count 1 -format end -digits 4
```
机械改写：无
结果代码：对象不存在
输出：
```text
CASE01-CMD: report_instance _11509_
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
CASE01-CMD: report_net -digits 4 [get_nets -of_objects [get_pins _11509_/Y]]
CASE01-ERROR: Error 232: diag_query.tcl line 1, net _40b0e0ac57580000_p_Net not found.
CASE01-CMD: report_checks -through [get_pins _11509_/Y] -path_delay max -scene ss_n40C_1v60 \
max_delay/setup group clk

                                      Required    Actual
Endpoint                                 Delay     Delay     Slack
------------------------------------------------------------------
_12026_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12027_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12029_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12032_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12033_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12034_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12035_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12036_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12037_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12038_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12039_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12040_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12041_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12042_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12043_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12044_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12045_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12047_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12048_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12049_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12050_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12051_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12052_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12053_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12054_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12055_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12056_/D (sky130_fd_sc_hd__dfxtp_1)   27.3541   31.5439   -4.1897 (VIOLATED)
_12028_/D (sky130_fd_sc_hd__dfxtp_1)   27.3794   31.4791   -4.0997 (VIOLATED)
_12030_/D (sky130_fd_sc_hd__dfxtp_1)   27.3794   31.4791   -4.0997 (VIOLATED)
_12031_/D (sky130_fd_sc_hd__dfxtp_1)   27.3794   31.4791   -4.0997 (VIOLATED)
_12046_/D (sky130_fd_sc_hd__dfxtp_1)   27.3794   31.4791   -4.0997 (VIOLATED)
```

### 查询 A4
你写的查询：
```tcl
foreach p {_11340_/X _11434_/Y _11451_/Y _11507_/Y _11509_/Y} {
  report_checks -through [get_pins $p] -path_delay max -scene ss_n40C_1v60 \
    -fields {slew cap input_pins fanout} -digits 4 -format summary
}
report_net [get_nets -of_objects [get_pins _11421_/X]]   ;# 看进位链单元的扇入扇出
```
实际执行的命令：
```tcl
foreach p {_11340_/X _11434_/Y _11451_/Y _11507_/Y _11509_/Y} {
  report_checks -through [get_pins $p] -path_delay max -scene ss_n40C_1v60 \
    -fields {slew cap input_pins fanout} -digits 4 -format summary
}
report_net [get_nets -of_objects [get_pins _11421_/X]]   ;# 看进位链单元的扇入扇出
```
机械改写：无
结果代码：对象不存在
输出：
```text
CASE01-CMD: foreach p {_11340_/X _11434_/Y _11451_/Y _11507_/Y _11509_/Y} {
Startpoint                           Endpoint                                 Slack
----------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.1897

Startpoint                           Endpoint                                 Slack
----------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.1897

Startpoint                           Endpoint                                 Slack
----------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.1897

Startpoint                           Endpoint                                 Slack
----------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.1897

Startpoint                           Endpoint                                 Slack
----------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.1897

CASE01-CMD: report_net [get_nets -of_objects [get_pins _11421_/X]]   ;# 看进位链单元的扇入扇出
CASE01-ERROR: Error 232: diag_query.tcl line 1, net _b06b4fc30d5b0000_p_Net not found.
```

### 查询 A5
你写的查询：
```tcl
replace_cell _11509_ sky130_fd_sc_hd__o21ai_4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
replace_cell _11509_ sky130_fd_sc_hd__o21ai_0
```
实际执行的命令：
```tcl
replace_cell _11509_ sky130_fd_sc_hd__o21ai_4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
replace_cell _11509_ sky130_fd_sc_hd__o21ai_0
```
机械改写：无
结果代码：改变冻结模型的查询（已在单独运行中执行）
说明：这条查询改变了分析模型，结果只作对照，不代表冻结模型。
输出：
```text
CASE01-CMD: replace_cell _11509_ sky130_fd_sc_hd__o21ai_4
1
CASE01-CMD: report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
Startpoint: in_b[2] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.3091    5.8911 ^ in_b[2] (in)
   0.2453    6.1365 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
   0.9804    7.1168 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.6267    7.7436 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   1.0379    8.7814 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.2727    9.0542 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.6601    9.7142 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   1.0917   10.8059 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.9265   11.7324 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.3997   12.1321 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.7300   12.8620 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.9433   13.8053 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.9799   14.7852 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.4077   15.1930 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.2608   15.4538 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.9285   16.3823 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.5449   16.9272 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.5349   17.4621 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.1799   17.6420 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.9453   18.5873 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5278 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.5289   20.0567 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.3197   20.3764 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.9447   21.3211 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2667 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.4391   22.7059 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.2517   22.9576 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.5119   23.4695 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.3357   23.8052 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.8462   24.6514 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.4326   25.0840 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   1.0241   26.1081 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.4919   26.6000 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.8376   27.4376 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.4013   27.8389 v _11454_/Y (sky130_fd_sc_hd__a31oi_1)
   0.3550   28.1939 v _11504_/Y (sky130_fd_sc_hd__xnor2_1)
   1.9801   30.1740 ^ _11510_/Y (sky130_fd_sc_hd__a21oi_1)
   0.7812   30.9552 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.9552 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            30.9552   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.4715   27.4385   library setup time
            27.4385   data required time
-------------------------------------------------------------
            27.4385   data required time
           -30.9552   data arrival time
-------------------------------------------------------------
            -3.5167   slack (VIOLATED)


CASE01-CMD: replace_cell _11509_ sky130_fd_sc_hd__o21ai_0
1
```

### 查询 A6
你写的查询：
```tcl
foreach s {ss_100C_1v60 ss_n40C_1v60 tt_025C_1v80} {
  report_checks -from [get_ports {in_b[2]}] -through [get_pins _11509_/Y] -to [get_pins _12026_/D] \
    -path_delay max -scene $s -digits 4 -format summary
}
```
实际执行的命令：
```tcl
foreach s {ss_100C_1v60 ss_n40C_1v60 tt_025C_1v80} {
  report_checks -from [get_ports {in_b[2]}] -through [get_pins _11509_/Y] -to [get_pins _12026_/D] \
    -path_delay max -scene $s -digits 4 -format summary
}
```
机械改写：无
结果代码：已执行
输出：
```text
CASE01-CMD: foreach s {ss_100C_1v60 ss_n40C_1v60 tt_025C_1v80} {
Startpoint                           Endpoint                                 Slack
----------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -0.5003

Startpoint                           Endpoint                                 Slack
----------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   -4.1897

Startpoint                           Endpoint                                 Slack
----------------------------------------------------------------------------------
in_b[2] (input)                      _12026_/D (sky130_fd_sc_hd__dfxtp_1)   11.2014
```

### 查询 A7
你写的查询：
```tcl
set_input_delay -clock clk -max 0 [get_ports {in_a[*] in_b[*] in_valid rst}]
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
set_input_delay -clock clk -max [expr {0.2*27.91}] [get_ports {in_a[*] in_b[*] in_valid rst}]
```
实际执行的命令：
```tcl
set_input_delay -clock clk -max 0 [get_ports {in_a[*] in_b[*] in_valid rst}]
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
set_input_delay -clock clk -max [expr {0.2*27.91}] [get_ports {in_a[*] in_b[*] in_valid rst}]
```
机械改写：无
结果代码：改变冻结模型的查询（已在单独运行中执行）
说明：这条查询改变了分析模型，结果只作对照，不代表冻结模型。
输出：
```text
CASE01-CMD: set_input_delay -clock clk -max 0 [get_ports {in_a[*] in_b[*] in_valid rst}]
CASE01-CMD: report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
Startpoint: in_b[2] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   0.0000    0.0000 ^ input external delay
   0.3091    0.3091 ^ in_b[2] (in)
   0.2453    0.5545 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
   0.9804    1.5348 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.6267    2.1616 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   1.0379    3.1994 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.2727    3.4722 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.6601    4.1322 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   1.0917    5.2239 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.9265    6.1504 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.3997    6.5501 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.7300    7.2800 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.9433    8.2233 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.9799    9.2033 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.4077    9.6110 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.2608    9.8718 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.9285   10.8003 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.5449   11.3452 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.5349   11.8801 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.1799   12.0600 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.9453   13.0053 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.9406   13.9458 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.5289   14.4747 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.3197   14.7944 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.9447   15.7391 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.9456   16.6847 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.4391   17.1239 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.2517   17.3756 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.5119   17.8875 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.3357   18.2232 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.8462   19.0694 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.4326   19.5020 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   1.0241   20.5261 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.4919   21.0180 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.8376   21.8556 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.3533   22.2088 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.2543   22.4632 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   2.6362   25.0994 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.8625   25.9619 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   25.9619 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            25.9619   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -25.9619   data arrival time
-------------------------------------------------------------
             1.3923   slack (MET)


CASE01-CMD: set_input_delay -clock clk -max [expr {0.2*27.91}] [get_ports {in_a[*] in_b[*] in_valid rst}]
```

### 查询 A8
你写的查询：
```tcl
report_lib_cell sky130_fd_sc_hd__dfxtp_1   ;# 是否支持此命令不确定
set a 0
foreach c [get_cells *] { set a [expr {$a + [get_property [get_property $c liberty_cell] area]}] }
puts $a
```
实际执行的命令：
```tcl
report_lib_cell sky130_fd_sc_hd__dfxtp_1   ;# 是否支持此命令不确定
set a 0
foreach c [get_cells *] { set a [expr {$a + [get_property [get_property $c liberty_cell] area]}] }
puts $a
```
机械改写：无
结果代码：已执行
输出：
```text
CASE01-CMD: report_lib_cell sky130_fd_sc_hd__dfxtp_1   ;# 是否支持此命令不确定
Cell sky130_fd_sc_hd__dfxtp_1
Library sky130_fd_sc_hd__tt_025C_1v80
File /home/eda/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
 VGND ground
 VNB well
 VPB well
 VPWR power
 CLK input 0.00-0.00
 D input 0.00-0.00
 Q output function=IQ
 IQ internal
 IQ_N internal

Timing arcs
 CLK -> CLK
  width
  ^ -> v
  v -> ^
 CLK -> D
  setup
  ^ -> ^
  ^ -> v
 CLK -> D
  hold
  ^ -> ^
  ^ -> v
 CLK -> Q
  Reg Clk to Q
  ^ -> ^
  ^ -> v
CASE01-CMD: set a 0
0
CASE01-CMD: foreach c [get_cells *] { set a [expr {$a + [get_property [get_property $c liberty_cell] area]}] }
CASE01-CMD: puts $a
45383.526497997744
```
