### 查询 B1（R1）
你写的查询：
```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
实际执行的命令：
```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
机械改写：无
执行类型：原上下文；执行结果：语法错误；异常：-；归因：请求本身的问题
输出：
```text
CASE02-CMD: foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
PORT _906ecdedfb640000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_a[34] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2730    5.8550 ^ in_a[34] (in)
   0.0000    5.8550 ^ _10564_/A (sky130_fd_sc_hd__and2_0)
   0.4006    6.2556 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
   0.0000    6.2556 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
   1.0188    7.2744 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.2744 v _10985_/B (sky130_fd_sc_hd__xor3_1)
   0.9736    8.2480 v _10985_/X (sky130_fd_sc_hd__xor3_1)
   0.0000    8.2480 v _10986_/B (sky130_fd_sc_hd__xor2_1)
   0.4475    8.6955 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    8.6955 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
   0.4045    9.1000 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    9.1000 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
   0.2403    9.3403 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
   0.0000    9.3403 v _11073_/B (sky130_fd_sc_hd__xor3_1)
   0.9973   10.3376 v _11073_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.3376 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
   0.5470   10.8846 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   10.8846 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
   0.9809   11.8655 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.8655 v _11302_/B (sky130_fd_sc_hd__xor3_1)
   0.9794   12.8449 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8449 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7882 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7882 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7681 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7681 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1758 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1758 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4366 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4366 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3652 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3652 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.9101 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.9101 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4450 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4450 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.6249 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.6249 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5701 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5701 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5107 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.5107 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0396 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0396 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3593 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3593 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.3040 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.3040 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2496 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2496 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6887 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6887 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9404 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9404 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4524 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4524 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7880 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7880 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.6343 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.6343 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0668 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0668 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0910 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0910 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5829 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5829 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.4205 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.4205 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7737 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7737 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   28.0280 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   28.0280 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6642 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6642 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.5267 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.5267 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.5267   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.5267   data arrival time
-------------------------------------------------------------
            -4.1726   slack (VIOLATED)


PORT _109fcdedfb640000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
No paths found.
PORT _107ecdedfb640000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_a[3] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2813    5.8633 ^ in_a[3] (in)
   0.0000    5.8633 ^ _10760_/A (sky130_fd_sc_hd__nand2_1)
   0.2805    6.1438 v _10760_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000    6.1438 v _10905_/B (sky130_fd_sc_hd__xnor3_1)
   0.9196    7.0634 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.0634 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
   0.6267    7.6902 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    7.6902 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
   1.0379    8.7280 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    8.7280 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
   0.2727    9.0008 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.0008 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
   0.6601    9.6608 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.6608 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
   1.0917   10.7525 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.7525 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
   0.9265   11.6790 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.6790 v _11257_/B (sky130_fd_sc_hd__xor2_1)
   0.3997   12.0787 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   12.0787 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
   0.7300   12.8086 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8086 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7519 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7519 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7319 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7319 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1396 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1396 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4004 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4004 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3289 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3289 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.8738 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.8738 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4087 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4087 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.5886 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.5886 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5339 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5339 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.4744 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.4744 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0033 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0033 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3230 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3230 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.2677 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.2677 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2133 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2133 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6525 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6525 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9042 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9042 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4161 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4161 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7518 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7518 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.5980 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.5980 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0306 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0306 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0547 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0547 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5466 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5466 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.3842 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.3842 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7374 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7374 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   27.9918 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   27.9918 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6280 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6280 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.4905 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.4905 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.4905   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.4905   data arrival time
-------------------------------------------------------------
            -4.1363   slack (VIOLATED)


PORT _908ecdedfb640000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
No paths found.
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: foreach p [all_inputs -no_clocks] {
_f00696edfb640000_p_Port max 1 1 min 1 1
_c0987aedfb640000_p_Port max 1 1 min 1 1
_90ce95edfb640000_p_Port max 1 1 min 1 1
_9060cdedfb640000_p_Port max 1 1 min 1 1
_1061cdedfb640000_p_Port max 1 1 min 1 1
_9061cdedfb640000_p_Port max 1 1 min 1 1
_1062cdedfb640000_p_Port max 1 1 min 1 1
_9062cdedfb640000_p_Port max 1 1 min 1 1
_1063cdedfb640000_p_Port max 1 1 min 1 1
_9063cdedfb640000_p_Port max 1 1 min 1 1
_1064cdedfb640000_p_Port max 1 1 min 1 1
_9064cdedfb640000_p_Port max 1 1 min 1 1
_1065cdedfb640000_p_Port max 1 1 min 1 1
_9065cdedfb640000_p_Port max 1 1 min 1 1
_1066cdedfb640000_p_Port max 1 1 min 1 1
_9066cdedfb640000_p_Port max 1 1 min 1 1
_1067cdedfb640000_p_Port max 1 1 min 1 1
_9067cdedfb640000_p_Port max 1 1 min 1 1
_1068cdedfb640000_p_Port max 1 1 min 1 1
_9068cdedfb640000_p_Port max 1 1 min 1 1
_1069cdedfb640000_p_Port max 1 1 min 1 1
_9069cdedfb640000_p_Port max 1 1 min 1 1
_106acdedfb640000_p_Port max 1 1 min 1 1
_906acdedfb640000_p_Port max 1 1 min 1 1
_106bcdedfb640000_p_Port max 1 1 min 1 1
_906bcdedfb640000_p_Port max 1 1 min 1 1
_106ccdedfb640000_p_Port max 1 1 min 1 1
_906ccdedfb640000_p_Port max 1 1 min 1 1
_106dcdedfb640000_p_Port max 1 1 min 1 1
_906dcdedfb640000_p_Port max 1 1 min 1 1
_106ecdedfb640000_p_Port max 1 1 min 1 1
_906ecdedfb640000_p_Port max 1 1 min 1 1
_106fcdedfb640000_p_Port max 1 1 min 1 1
_906fcdedfb640000_p_Port max 1 1 min 1 1
_1070cdedfb640000_p_Port max 1 1 min 1 1
_9070cdedfb640000_p_Port max 1 1 min 1 1
_1071cdedfb640000_p_Port max 1 1 min 1 1
_9071cdedfb640000_p_Port max 1 1 min 1 1
_1072cdedfb640000_p_Port max 1 1 min 1 1
_9072cdedfb640000_p_Port max 1 1 min 1 1
_1073cdedfb640000_p_Port max 1 1 min 1 1
_9073cdedfb640000_p_Port max 1 1 min 1 1
_1074cdedfb640000_p_Port max 1 1 min 1 1
_9074cdedfb640000_p_Port max 1 1 min 1 1
_1075cdedfb640000_p_Port max 1 1 min 1 1
_9075cdedfb640000_p_Port max 1 1 min 1 1
_1076cdedfb640000_p_Port max 1 1 min 1 1
_9076cdedfb640000_p_Port max 1 1 min 1 1
_1077cdedfb640000_p_Port max 1 1 min 1 1
_9077cdedfb640000_p_Port max 1 1 min 1 1
_1078cdedfb640000_p_Port max 1 1 min 1 1
_9078cdedfb640000_p_Port max 1 1 min 1 1
_1079cdedfb640000_p_Port max 1 1 min 1 1
_9079cdedfb640000_p_Port max 1 1 min 1 1
_107acdedfb640000_p_Port max 1 1 min 1 1
_907acdedfb640000_p_Port max 1 1 min 1 1
_107bcdedfb640000_p_Port max 1 1 min 1 1
_907bcdedfb640000_p_Port max 1 1 min 1 1
_107ccdedfb640000_p_Port max 1 1 min 1 1
_907ccdedfb640000_p_Port max 1 1 min 1 1
_107dcdedfb640000_p_Port max 1 1 min 1 1
_907dcdedfb640000_p_Port max 1 1 min 1 1
_107ecdedfb640000_p_Port max 1 1 min 1 1
_907ecdedfb640000_p_Port max 1 1 min 1 1
_107fcdedfb640000_p_Port max 1 1 min 1 1
_907fcdedfb640000_p_Port max 1 1 min 1 1
_9080cdedfb640000_p_Port max 0 1 min 0 1
_1081cdedfb640000_p_Port max 0 1 min 0 1
_9081cdedfb640000_p_Port max 0 1 min 0 1
_1082cdedfb640000_p_Port max 0 1 min 0 1
_9082cdedfb640000_p_Port max 0 1 min 0 1
_1083cdedfb640000_p_Port max 0 1 min 0 1
_9083cdedfb640000_p_Port max 0 1 min 0 1
_1084cdedfb640000_p_Port max 0 1 min 0 1
_9084cdedfb640000_p_Port max 0 1 min 0 1
_1085cdedfb640000_p_Port max 0 1 min 0 1
_9085cdedfb640000_p_Port max 0 1 min 0 1
_1086cdedfb640000_p_Port max 0 1 min 0 1
_9086cdedfb640000_p_Port max 0 1 min 0 1
_1087cdedfb640000_p_Port max 0 1 min 0 1
_9087cdedfb640000_p_Port max 0 1 min 0 1
_1088cdedfb640000_p_Port max 0 1 min 0 1
_9088cdedfb640000_p_Port max 0 1 min 0 1
_1089cdedfb640000_p_Port max 0 1 min 0 1
_9089cdedfb640000_p_Port max 0 1 min 0 1
_108acdedfb640000_p_Port max 0 1 min 0 1
_908acdedfb640000_p_Port max 0 1 min 0 1
_108bcdedfb640000_p_Port max 0 1 min 0 1
_908bcdedfb640000_p_Port max 0 1 min 0 1
_108ccdedfb640000_p_Port max 0 1 min 0 1
_908ccdedfb640000_p_Port max 0 1 min 0 1
_108dcdedfb640000_p_Port max 0 1 min 0 1
_908dcdedfb640000_p_Port max 0 1 min 0 1
_108ecdedfb640000_p_Port max 0 1 min 0 1
_908ecdedfb640000_p_Port max 0 1 min 0 1
_108fcdedfb640000_p_Port max 0 1 min 0 1
_908fcdedfb640000_p_Port max 0 1 min 0 1
_1090cdedfb640000_p_Port max 0 1 min 0 1
_9090cdedfb640000_p_Port max 0 1 min 0 1
_1091cdedfb640000_p_Port max 0 1 min 0 1
_9091cdedfb640000_p_Port max 0 1 min 0 1
_1092cdedfb640000_p_Port max 0 1 min 0 1
_9092cdedfb640000_p_Port max 0 1 min 0 1
_1093cdedfb640000_p_Port max 0 1 min 0 1
_9093cdedfb640000_p_Port max 0 1 min 0 1
_1094cdedfb640000_p_Port max 0 1 min 0 1
_9094cdedfb640000_p_Port max 0 1 min 0 1
_1095cdedfb640000_p_Port max 0 1 min 0 1
_9095cdedfb640000_p_Port max 0 1 min 0 1
_1096cdedfb640000_p_Port max 0 1 min 0 1
_9096cdedfb640000_p_Port max 0 1 min 0 1
_1097cdedfb640000_p_Port max 0 1 min 0 1
_9097cdedfb640000_p_Port max 0 1 min 0 1
_1098cdedfb640000_p_Port max 0 1 min 0 1
_9098cdedfb640000_p_Port max 0 1 min 0 1
_1099cdedfb640000_p_Port max 0 1 min 0 1
_9099cdedfb640000_p_Port max 0 1 min 0 1
_109acdedfb640000_p_Port max 0 1 min 0 1
_909acdedfb640000_p_Port max 0 1 min 0 1
_109bcdedfb640000_p_Port max 0 1 min 0 1
_909bcdedfb640000_p_Port max 0 1 min 0 1
_109ccdedfb640000_p_Port max 0 1 min 0 1
_909ccdedfb640000_p_Port max 0 1 min 0 1
_109dcdedfb640000_p_Port max 0 1 min 0 1
_909dcdedfb640000_p_Port max 0 1 min 0 1
_109ecdedfb640000_p_Port max 0 1 min 0 1
_909ecdedfb640000_p_Port max 0 1 min 0 1
_109fcdedfb640000_p_Port max 0 1 min 0 1
_909fcdedfb640000_p_Port max 0 1 min 0 1
_10a0cdedfb640000_p_Port max 0 1 min 0 1
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: foreach p [all_inputs -no_clocks] {
PORT _f00696edfb640000_p_Port
PORT _c0987aedfb640000_p_Port
PORT _90ce95edfb640000_p_Port
PORT _9060cdedfb640000_p_Port
PORT _1061cdedfb640000_p_Port
PORT _9061cdedfb640000_p_Port
PORT _1062cdedfb640000_p_Port
PORT _9062cdedfb640000_p_Port
PORT _1063cdedfb640000_p_Port
PORT _9063cdedfb640000_p_Port
PORT _1064cdedfb640000_p_Port
PORT _9064cdedfb640000_p_Port
PORT _1065cdedfb640000_p_Port
PORT _9065cdedfb640000_p_Port
PORT _1066cdedfb640000_p_Port
PORT _9066cdedfb640000_p_Port
PORT _1067cdedfb640000_p_Port
PORT _9067cdedfb640000_p_Port
PORT _1068cdedfb640000_p_Port
PORT _9068cdedfb640000_p_Port
PORT _1069cdedfb640000_p_Port
PORT _9069cdedfb640000_p_Port
PORT _106acdedfb640000_p_Port
PORT _906acdedfb640000_p_Port
PORT _106bcdedfb640000_p_Port
PORT _906bcdedfb640000_p_Port
PORT _106ccdedfb640000_p_Port
PORT _906ccdedfb640000_p_Port
PORT _106dcdedfb640000_p_Port
PORT _906dcdedfb640000_p_Port
PORT _106ecdedfb640000_p_Port
PORT _906ecdedfb640000_p_Port
PORT _106fcdedfb640000_p_Port
PORT _906fcdedfb640000_p_Port
PORT _1070cdedfb640000_p_Port
PORT _9070cdedfb640000_p_Port
PORT _1071cdedfb640000_p_Port
PORT _9071cdedfb640000_p_Port
PORT _1072cdedfb640000_p_Port
PORT _9072cdedfb640000_p_Port
PORT _1073cdedfb640000_p_Port
PORT _9073cdedfb640000_p_Port
PORT _1074cdedfb640000_p_Port
PORT _9074cdedfb640000_p_Port
PORT _1075cdedfb640000_p_Port
PORT _9075cdedfb640000_p_Port
PORT _1076cdedfb640000_p_Port
PORT _9076cdedfb640000_p_Port
PORT _1077cdedfb640000_p_Port
PORT _9077cdedfb640000_p_Port
PORT _1078cdedfb640000_p_Port
PORT _9078cdedfb640000_p_Port
PORT _1079cdedfb640000_p_Port
PORT _9079cdedfb640000_p_Port
PORT _107acdedfb640000_p_Port
PORT _907acdedfb640000_p_Port
PORT _107bcdedfb640000_p_Port
PORT _907bcdedfb640000_p_Port
PORT _107ccdedfb640000_p_Port
PORT _907ccdedfb640000_p_Port
PORT _107dcdedfb640000_p_Port
PORT _907dcdedfb640000_p_Port
PORT _107ecdedfb640000_p_Port
PORT _907ecdedfb640000_p_Port
PORT _107fcdedfb640000_p_Port
PORT _907fcdedfb640000_p_Port
PORT _9080cdedfb640000_p_Port
PORT _1081cdedfb640000_p_Port
PORT _9081cdedfb640000_p_Port
PORT _1082cdedfb640000_p_Port
PORT _9082cdedfb640000_p_Port
PORT _1083cdedfb640000_p_Port
PORT _9083cdedfb640000_p_Port
PORT _1084cdedfb640000_p_Port
PORT _9084cdedfb640000_p_Port
PORT _1085cdedfb640000_p_Port
PORT _9085cdedfb640000_p_Port
PORT _1086cdedfb640000_p_Port
PORT _9086cdedfb640000_p_Port
PORT _1087cdedfb640000_p_Port
PORT _9087cdedfb640000_p_Port
PORT _1088cdedfb640000_p_Port
PORT _9088cdedfb640000_p_Port
PORT _1089cdedfb640000_p_Port
PORT _9089cdedfb640000_p_Port
PORT _108acdedfb640000_p_Port
PORT _908acdedfb640000_p_Port
PORT _108bcdedfb640000_p_Port
PORT _908bcdedfb640000_p_Port
PORT _108ccdedfb640000_p_Port
PORT _908ccdedfb640000_p_Port
PORT _108dcdedfb640000_p_Port
PORT _908dcdedfb640000_p_Port
PORT _108ecdedfb640000_p_Port
PORT _908ecdedfb640000_p_Port
PORT _108fcdedfb640000_p_Port
PORT _908fcdedfb640000_p_Port
PORT _1090cdedfb640000_p_Port
PORT _9090cdedfb640000_p_Port
PORT _1091cdedfb640000_p_Port
PORT _9091cdedfb640000_p_Port
PORT _1092cdedfb640000_p_Port
PORT _9092cdedfb640000_p_Port
PORT _1093cdedfb640000_p_Port
PORT _9093cdedfb640000_p_Port
PORT _1094cdedfb640000_p_Port
PORT _9094cdedfb640000_p_Port
PORT _1095cdedfb640000_p_Port
PORT _9095cdedfb640000_p_Port
PORT _1096cdedfb640000_p_Port
PORT _9096cdedfb640000_p_Port
PORT _1097cdedfb640000_p_Port
PORT _9097cdedfb640000_p_Port
PORT _1098cdedfb640000_p_Port
PORT _9098cdedfb640000_p_Port
PORT _1099cdedfb640000_p_Port
PORT _9099cdedfb640000_p_Port
PORT _109acdedfb640000_p_Port
PORT _909acdedfb640000_p_Port
PORT _109bcdedfb640000_p_Port
PORT _909bcdedfb640000_p_Port
PORT _109ccdedfb640000_p_Port
PORT _909ccdedfb640000_p_Port
PORT _109dcdedfb640000_p_Port
PORT _909dcdedfb640000_p_Port
PORT _109ecdedfb640000_p_Port
PORT _909ecdedfb640000_p_Port
PORT _109fcdedfb640000_p_Port
PORT _909fcdedfb640000_p_Port
PORT _10a0cdedfb640000_p_Port
CASE02-CMD: foreach p [all_inputs -no_clocks] {
PORT _f00696edfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _c0987aedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ce95edfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9060cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1061cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9061cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1062cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9062cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1063cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9063cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1064cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9064cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1065cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9065cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1066cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9066cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1067cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9067cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1068cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9068cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1069cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9069cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1070cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9070cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1071cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9071cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1072cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9072cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1073cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9073cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1074cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9074cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1075cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9075cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1076cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9076cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1077cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9077cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1078cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9078cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1079cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9079cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9080cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1081cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9081cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1082cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9082cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1083cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9083cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1084cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9084cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1085cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9085cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1086cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9086cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1087cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9087cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1088cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9088cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1089cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9089cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1090cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9090cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1091cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9091cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1092cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9092cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1093cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9093cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1094cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9094cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1095cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9095cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1096cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9096cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1097cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9097cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1098cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9098cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1099cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9099cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a0cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
CASE02-CMD: foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
tt_025C_1v80 max WS=11.191043075655372 TNS=0.0
tt_025C_1v80 min WS=0.09305387279663745 TNS=0.0
tt_100C_1v80 max WS=11.32117898139033 TNS=0.0
tt_100C_1v80 min WS=0.08983023607005908 TNS=0.0
ss_100C_1v60 max WS=-0.6799521138591476 TNS=-21.004391709342716
ss_100C_1v60 min WS=0.18567888030452087 TNS=0.0
ss_n40C_1v60 max WS=-4.172594832200332 TNS=-129.94064858564798
ss_n40C_1v60 min WS=0.18500412836443383 TNS=0.0
ff_n40C_1v95 max WS=15.881204356648498 TNS=0.0
ff_n40C_1v95 min WS=0.06347266641938298 TNS=0.0
ff_100C_1v95 max WS=15.90284571263497 TNS=0.0
ff_100C_1v95 min WS=0.059112952317363035 TNS=0.0
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: set cn 0; set un 0
0
CASE02-CMD: foreach p [all_inputs -no_clocks] {
CASE02-CMD: puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
constrained_in2reg_max_endpoints=66 unconstrained_only=64
```

### 查询 B1（R2）
你写的查询：
```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
实际执行的命令：
```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
机械改写：无
执行类型：原上下文；执行结果：语法错误；异常：-；归因：请求本身的问题
输出：
```text
CASE02-CMD: foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
PORT _907e8a57db630000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_a[34] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2730    5.8550 ^ in_a[34] (in)
   0.0000    5.8550 ^ _10564_/A (sky130_fd_sc_hd__and2_0)
   0.4006    6.2556 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
   0.0000    6.2556 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
   1.0188    7.2744 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.2744 v _10985_/B (sky130_fd_sc_hd__xor3_1)
   0.9736    8.2480 v _10985_/X (sky130_fd_sc_hd__xor3_1)
   0.0000    8.2480 v _10986_/B (sky130_fd_sc_hd__xor2_1)
   0.4475    8.6955 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    8.6955 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
   0.4045    9.1000 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    9.1000 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
   0.2403    9.3403 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
   0.0000    9.3403 v _11073_/B (sky130_fd_sc_hd__xor3_1)
   0.9973   10.3376 v _11073_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.3376 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
   0.5470   10.8846 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   10.8846 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
   0.9809   11.8655 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.8655 v _11302_/B (sky130_fd_sc_hd__xor3_1)
   0.9794   12.8449 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8449 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7882 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7882 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7681 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7681 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1758 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1758 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4366 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4366 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3652 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3652 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.9101 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.9101 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4450 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4450 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.6249 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.6249 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5701 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5701 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5107 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.5107 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0396 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0396 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3593 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3593 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.3040 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.3040 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2496 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2496 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6887 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6887 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9404 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9404 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4524 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4524 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7880 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7880 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.6343 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.6343 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0668 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0668 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0910 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0910 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5829 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5829 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.4205 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.4205 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7737 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7737 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   28.0280 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   28.0280 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6642 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6642 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.5267 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.5267 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.5267   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.5267   data arrival time
-------------------------------------------------------------
            -4.1726   slack (VIOLATED)


PORT _10af8a57db630000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
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
   0.0000    5.8911 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
   0.2453    6.1365 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000    6.1365 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
   0.9804    7.1168 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.1168 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
   0.6267    7.7436 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    7.7436 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
   1.0379    8.7814 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    8.7814 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
   0.2727    9.0542 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.0542 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
   0.6601    9.7142 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.7142 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
   1.0917   10.8059 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.8059 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
   0.9265   11.7324 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.7324 v _11257_/B (sky130_fd_sc_hd__xor2_1)
   0.3997   12.1321 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   12.1321 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
   0.7300   12.8620 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8620 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.8053 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.8053 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7852 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7852 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1930 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1930 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4538 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4538 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3823 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3823 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.9272 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.9272 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4621 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4621 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.6420 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.6420 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5873 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5873 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5278 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.5278 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0567 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0567 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3764 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3764 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.3211 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.3211 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2667 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2667 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.7059 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.7059 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9576 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9576 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4695 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4695 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.8052 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.8052 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.6514 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.6514 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0840 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0840 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.1081 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.1081 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.6000 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.6000 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.4376 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.4376 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7908 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7908 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   28.0452 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   28.0452 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6814 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6814 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.5439 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.5439 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.5439   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.5439   data arrival time
-------------------------------------------------------------
            -4.1897   slack (VIOLATED)


PORT _108e8a57db630000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_a[3] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2813    5.8633 ^ in_a[3] (in)
   0.0000    5.8633 ^ _10760_/A (sky130_fd_sc_hd__nand2_1)
   0.2805    6.1438 v _10760_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000    6.1438 v _10905_/B (sky130_fd_sc_hd__xnor3_1)
   0.9196    7.0634 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.0634 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
   0.6267    7.6902 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    7.6902 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
   1.0379    8.7280 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    8.7280 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
   0.2727    9.0008 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.0008 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
   0.6601    9.6608 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.6608 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
   1.0917   10.7525 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.7525 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
   0.9265   11.6790 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.6790 v _11257_/B (sky130_fd_sc_hd__xor2_1)
   0.3997   12.0787 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   12.0787 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
   0.7300   12.8086 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8086 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7519 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7519 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7319 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7319 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1396 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1396 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4004 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4004 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3289 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3289 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.8738 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.8738 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4087 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4087 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.5886 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.5886 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5339 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5339 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.4744 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.4744 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0033 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0033 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3230 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3230 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.2677 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.2677 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2133 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2133 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6525 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6525 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9042 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9042 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4161 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4161 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7518 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7518 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.5980 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.5980 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0306 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0306 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0547 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0547 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5466 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5466 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.3842 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.3842 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7374 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7374 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   27.9918 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   27.9918 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6280 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6280 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.4905 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.4905 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.4905   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.4905   data arrival time
-------------------------------------------------------------
            -4.1363   slack (VIOLATED)


PORT _909e8a57db630000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_b[35] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2787    5.8607 ^ in_b[35] (in)
   0.0000    5.8607 ^ _10564_/B (sky130_fd_sc_hd__and2_0)
   0.4031    6.2638 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
   0.0000    6.2638 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
   1.0188    7.2826 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.2826 v _10985_/B (sky130_fd_sc_hd__xor3_1)
   0.9736    8.2562 v _10985_/X (sky130_fd_sc_hd__xor3_1)
   0.0000    8.2562 v _10986_/B (sky130_fd_sc_hd__xor2_1)
   0.4475    8.7037 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    8.7037 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
   0.4045    9.1082 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    9.1082 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
   0.2403    9.3485 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
   0.0000    9.3485 v _11073_/B (sky130_fd_sc_hd__xor3_1)
   0.9973   10.3458 v _11073_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.3458 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
   0.5470   10.8928 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   10.8928 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
   0.9809   11.8738 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.8738 v _11302_/B (sky130_fd_sc_hd__xor3_1)
   0.9794   12.8531 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8531 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7964 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7964 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7763 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7763 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1841 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1841 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4449 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4449 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3734 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3734 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.9183 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.9183 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4532 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4532 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.6331 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.6331 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5783 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5783 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5189 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.5189 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0478 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0478 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3675 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3675 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.3122 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.3122 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2578 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2578 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6969 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6969 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9486 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9486 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4606 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4606 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7962 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7962 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.6425 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.6425 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0751 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0751 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0992 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0992 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5911 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5911 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.4287 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.4287 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7819 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7819 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   28.0363 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   28.0363 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6724 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6724 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.5350 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.5350 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.5350   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.5350   data arrival time
-------------------------------------------------------------
            -4.1808   slack (VIOLATED)


CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: foreach p [all_inputs -no_clocks] {
_f0165357db630000_p_Port max 1 1 min 1 1
_c0a83757db630000_p_Port max 1 1 min 1 1
_90de5257db630000_p_Port max 1 1 min 1 1
_90708a57db630000_p_Port max 1 1 min 1 1
_10718a57db630000_p_Port max 1 1 min 1 1
_90718a57db630000_p_Port max 1 1 min 1 1
_10728a57db630000_p_Port max 1 1 min 1 1
_90728a57db630000_p_Port max 1 1 min 1 1
_10738a57db630000_p_Port max 1 1 min 1 1
_90738a57db630000_p_Port max 1 1 min 1 1
_10748a57db630000_p_Port max 1 1 min 1 1
_90748a57db630000_p_Port max 1 1 min 1 1
_10758a57db630000_p_Port max 1 1 min 1 1
_90758a57db630000_p_Port max 1 1 min 1 1
_10768a57db630000_p_Port max 1 1 min 1 1
_90768a57db630000_p_Port max 1 1 min 1 1
_10778a57db630000_p_Port max 1 1 min 1 1
_90778a57db630000_p_Port max 1 1 min 1 1
_10788a57db630000_p_Port max 1 1 min 1 1
_90788a57db630000_p_Port max 1 1 min 1 1
_10798a57db630000_p_Port max 1 1 min 1 1
_90798a57db630000_p_Port max 1 1 min 1 1
_107a8a57db630000_p_Port max 1 1 min 1 1
_907a8a57db630000_p_Port max 1 1 min 1 1
_107b8a57db630000_p_Port max 1 1 min 1 1
_907b8a57db630000_p_Port max 1 1 min 1 1
_107c8a57db630000_p_Port max 1 1 min 1 1
_907c8a57db630000_p_Port max 1 1 min 1 1
_107d8a57db630000_p_Port max 1 1 min 1 1
_907d8a57db630000_p_Port max 1 1 min 1 1
_107e8a57db630000_p_Port max 1 1 min 1 1
_907e8a57db630000_p_Port max 1 1 min 1 1
_107f8a57db630000_p_Port max 1 1 min 1 1
_907f8a57db630000_p_Port max 1 1 min 1 1
_10808a57db630000_p_Port max 1 1 min 1 1
_90808a57db630000_p_Port max 1 1 min 1 1
_10818a57db630000_p_Port max 1 1 min 1 1
_90818a57db630000_p_Port max 1 1 min 1 1
_10828a57db630000_p_Port max 1 1 min 1 1
_90828a57db630000_p_Port max 1 1 min 1 1
_10838a57db630000_p_Port max 1 1 min 1 1
_90838a57db630000_p_Port max 1 1 min 1 1
_10848a57db630000_p_Port max 1 1 min 1 1
_90848a57db630000_p_Port max 1 1 min 1 1
_10858a57db630000_p_Port max 1 1 min 1 1
_90858a57db630000_p_Port max 1 1 min 1 1
_10868a57db630000_p_Port max 1 1 min 1 1
_90868a57db630000_p_Port max 1 1 min 1 1
_10878a57db630000_p_Port max 1 1 min 1 1
_90878a57db630000_p_Port max 1 1 min 1 1
_10888a57db630000_p_Port max 1 1 min 1 1
_90888a57db630000_p_Port max 1 1 min 1 1
_10898a57db630000_p_Port max 1 1 min 1 1
_90898a57db630000_p_Port max 1 1 min 1 1
_108a8a57db630000_p_Port max 1 1 min 1 1
_908a8a57db630000_p_Port max 1 1 min 1 1
_108b8a57db630000_p_Port max 1 1 min 1 1
_908b8a57db630000_p_Port max 1 1 min 1 1
_108c8a57db630000_p_Port max 1 1 min 1 1
_908c8a57db630000_p_Port max 1 1 min 1 1
_108d8a57db630000_p_Port max 1 1 min 1 1
_908d8a57db630000_p_Port max 1 1 min 1 1
_108e8a57db630000_p_Port max 1 1 min 1 1
_908e8a57db630000_p_Port max 1 1 min 1 1
_108f8a57db630000_p_Port max 1 1 min 1 1
_908f8a57db630000_p_Port max 1 1 min 1 1
_90908a57db630000_p_Port max 1 1 min 1 1
_10918a57db630000_p_Port max 1 1 min 1 1
_90918a57db630000_p_Port max 1 1 min 1 1
_10928a57db630000_p_Port max 1 1 min 1 1
_90928a57db630000_p_Port max 1 1 min 1 1
_10938a57db630000_p_Port max 1 1 min 1 1
_90938a57db630000_p_Port max 1 1 min 1 1
_10948a57db630000_p_Port max 1 1 min 1 1
_90948a57db630000_p_Port max 1 1 min 1 1
_10958a57db630000_p_Port max 1 1 min 1 1
_90958a57db630000_p_Port max 1 1 min 1 1
_10968a57db630000_p_Port max 1 1 min 1 1
_90968a57db630000_p_Port max 1 1 min 1 1
_10978a57db630000_p_Port max 1 1 min 1 1
_90978a57db630000_p_Port max 1 1 min 1 1
_10988a57db630000_p_Port max 1 1 min 1 1
_90988a57db630000_p_Port max 1 1 min 1 1
_10998a57db630000_p_Port max 1 1 min 1 1
_90998a57db630000_p_Port max 1 1 min 1 1
_109a8a57db630000_p_Port max 1 1 min 1 1
_909a8a57db630000_p_Port max 1 1 min 1 1
_109b8a57db630000_p_Port max 1 1 min 1 1
_909b8a57db630000_p_Port max 1 1 min 1 1
_109c8a57db630000_p_Port max 1 1 min 1 1
_909c8a57db630000_p_Port max 1 1 min 1 1
_109d8a57db630000_p_Port max 1 1 min 1 1
_909d8a57db630000_p_Port max 1 1 min 1 1
_109e8a57db630000_p_Port max 1 1 min 1 1
_909e8a57db630000_p_Port max 1 1 min 1 1
_109f8a57db630000_p_Port max 1 1 min 1 1
_909f8a57db630000_p_Port max 1 1 min 1 1
_10a08a57db630000_p_Port max 1 1 min 1 1
_90a08a57db630000_p_Port max 1 1 min 1 1
_10a18a57db630000_p_Port max 1 1 min 1 1
_90a18a57db630000_p_Port max 1 1 min 1 1
_10a28a57db630000_p_Port max 1 1 min 1 1
_90a28a57db630000_p_Port max 1 1 min 1 1
_10a38a57db630000_p_Port max 1 1 min 1 1
_90a38a57db630000_p_Port max 1 1 min 1 1
_10a48a57db630000_p_Port max 1 1 min 1 1
_90a48a57db630000_p_Port max 1 1 min 1 1
_10a58a57db630000_p_Port max 1 1 min 1 1
_90a58a57db630000_p_Port max 1 1 min 1 1
_10a68a57db630000_p_Port max 1 1 min 1 1
_90a68a57db630000_p_Port max 1 1 min 1 1
_10a78a57db630000_p_Port max 1 1 min 1 1
_90a78a57db630000_p_Port max 1 1 min 1 1
_10a88a57db630000_p_Port max 1 1 min 1 1
_90a88a57db630000_p_Port max 1 1 min 1 1
_10a98a57db630000_p_Port max 1 1 min 1 1
_90a98a57db630000_p_Port max 1 1 min 1 1
_10aa8a57db630000_p_Port max 1 1 min 1 1
_90aa8a57db630000_p_Port max 1 1 min 1 1
_10ab8a57db630000_p_Port max 1 1 min 1 1
_90ab8a57db630000_p_Port max 1 1 min 1 1
_10ac8a57db630000_p_Port max 1 1 min 1 1
_90ac8a57db630000_p_Port max 1 1 min 1 1
_10ad8a57db630000_p_Port max 1 1 min 1 1
_90ad8a57db630000_p_Port max 1 1 min 1 1
_10ae8a57db630000_p_Port max 1 1 min 1 1
_90ae8a57db630000_p_Port max 1 1 min 1 1
_10af8a57db630000_p_Port max 1 1 min 1 1
_90af8a57db630000_p_Port max 1 1 min 1 1
_10b08a57db630000_p_Port max 1 1 min 1 1
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: foreach p [all_inputs -no_clocks] {
PORT _f0165357db630000_p_Port
PORT _c0a83757db630000_p_Port
PORT _90de5257db630000_p_Port
PORT _90708a57db630000_p_Port
PORT _10718a57db630000_p_Port
PORT _90718a57db630000_p_Port
PORT _10728a57db630000_p_Port
PORT _90728a57db630000_p_Port
PORT _10738a57db630000_p_Port
PORT _90738a57db630000_p_Port
PORT _10748a57db630000_p_Port
PORT _90748a57db630000_p_Port
PORT _10758a57db630000_p_Port
PORT _90758a57db630000_p_Port
PORT _10768a57db630000_p_Port
PORT _90768a57db630000_p_Port
PORT _10778a57db630000_p_Port
PORT _90778a57db630000_p_Port
PORT _10788a57db630000_p_Port
PORT _90788a57db630000_p_Port
PORT _10798a57db630000_p_Port
PORT _90798a57db630000_p_Port
PORT _107a8a57db630000_p_Port
PORT _907a8a57db630000_p_Port
PORT _107b8a57db630000_p_Port
PORT _907b8a57db630000_p_Port
PORT _107c8a57db630000_p_Port
PORT _907c8a57db630000_p_Port
PORT _107d8a57db630000_p_Port
PORT _907d8a57db630000_p_Port
PORT _107e8a57db630000_p_Port
PORT _907e8a57db630000_p_Port
PORT _107f8a57db630000_p_Port
PORT _907f8a57db630000_p_Port
PORT _10808a57db630000_p_Port
PORT _90808a57db630000_p_Port
PORT _10818a57db630000_p_Port
PORT _90818a57db630000_p_Port
PORT _10828a57db630000_p_Port
PORT _90828a57db630000_p_Port
PORT _10838a57db630000_p_Port
PORT _90838a57db630000_p_Port
PORT _10848a57db630000_p_Port
PORT _90848a57db630000_p_Port
PORT _10858a57db630000_p_Port
PORT _90858a57db630000_p_Port
PORT _10868a57db630000_p_Port
PORT _90868a57db630000_p_Port
PORT _10878a57db630000_p_Port
PORT _90878a57db630000_p_Port
PORT _10888a57db630000_p_Port
PORT _90888a57db630000_p_Port
PORT _10898a57db630000_p_Port
PORT _90898a57db630000_p_Port
PORT _108a8a57db630000_p_Port
PORT _908a8a57db630000_p_Port
PORT _108b8a57db630000_p_Port
PORT _908b8a57db630000_p_Port
PORT _108c8a57db630000_p_Port
PORT _908c8a57db630000_p_Port
PORT _108d8a57db630000_p_Port
PORT _908d8a57db630000_p_Port
PORT _108e8a57db630000_p_Port
PORT _908e8a57db630000_p_Port
PORT _108f8a57db630000_p_Port
PORT _908f8a57db630000_p_Port
PORT _90908a57db630000_p_Port
PORT _10918a57db630000_p_Port
PORT _90918a57db630000_p_Port
PORT _10928a57db630000_p_Port
PORT _90928a57db630000_p_Port
PORT _10938a57db630000_p_Port
PORT _90938a57db630000_p_Port
PORT _10948a57db630000_p_Port
PORT _90948a57db630000_p_Port
PORT _10958a57db630000_p_Port
PORT _90958a57db630000_p_Port
PORT _10968a57db630000_p_Port
PORT _90968a57db630000_p_Port
PORT _10978a57db630000_p_Port
PORT _90978a57db630000_p_Port
PORT _10988a57db630000_p_Port
PORT _90988a57db630000_p_Port
PORT _10998a57db630000_p_Port
PORT _90998a57db630000_p_Port
PORT _109a8a57db630000_p_Port
PORT _909a8a57db630000_p_Port
PORT _109b8a57db630000_p_Port
PORT _909b8a57db630000_p_Port
PORT _109c8a57db630000_p_Port
PORT _909c8a57db630000_p_Port
PORT _109d8a57db630000_p_Port
PORT _909d8a57db630000_p_Port
PORT _109e8a57db630000_p_Port
PORT _909e8a57db630000_p_Port
PORT _109f8a57db630000_p_Port
PORT _909f8a57db630000_p_Port
PORT _10a08a57db630000_p_Port
PORT _90a08a57db630000_p_Port
PORT _10a18a57db630000_p_Port
PORT _90a18a57db630000_p_Port
PORT _10a28a57db630000_p_Port
PORT _90a28a57db630000_p_Port
PORT _10a38a57db630000_p_Port
PORT _90a38a57db630000_p_Port
PORT _10a48a57db630000_p_Port
PORT _90a48a57db630000_p_Port
PORT _10a58a57db630000_p_Port
PORT _90a58a57db630000_p_Port
PORT _10a68a57db630000_p_Port
PORT _90a68a57db630000_p_Port
PORT _10a78a57db630000_p_Port
PORT _90a78a57db630000_p_Port
PORT _10a88a57db630000_p_Port
PORT _90a88a57db630000_p_Port
PORT _10a98a57db630000_p_Port
PORT _90a98a57db630000_p_Port
PORT _10aa8a57db630000_p_Port
PORT _90aa8a57db630000_p_Port
PORT _10ab8a57db630000_p_Port
PORT _90ab8a57db630000_p_Port
PORT _10ac8a57db630000_p_Port
PORT _90ac8a57db630000_p_Port
PORT _10ad8a57db630000_p_Port
PORT _90ad8a57db630000_p_Port
PORT _10ae8a57db630000_p_Port
PORT _90ae8a57db630000_p_Port
PORT _10af8a57db630000_p_Port
PORT _90af8a57db630000_p_Port
PORT _10b08a57db630000_p_Port
CASE02-CMD: foreach p [all_inputs -no_clocks] {
PORT _f0165357db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _c0a83757db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90de5257db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90708a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10718a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90718a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10728a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90728a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10738a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90738a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10748a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90748a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10758a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90758a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10768a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90768a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10778a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90778a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10788a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90788a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10798a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90798a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10808a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90808a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10818a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90818a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10828a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90828a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10838a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90838a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10848a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90848a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10858a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90858a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10868a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90868a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10878a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90878a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10888a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90888a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10898a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90898a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90908a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10918a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90918a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10928a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90928a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10938a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90938a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10948a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90948a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10958a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90958a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10968a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90968a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10978a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90978a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10988a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90988a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10998a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90998a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a08a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a08a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a18a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a18a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a28a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a28a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a38a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a38a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a48a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a48a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a58a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a58a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a68a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a68a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a78a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a78a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a88a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a88a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a98a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a98a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10aa8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90aa8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10ab8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ab8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10ac8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ac8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10ad8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ad8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10ae8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ae8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10af8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90af8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10b08a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
CASE02-CMD: foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
tt_025C_1v80 max WS=11.185458209594348 TNS=0.0
tt_025C_1v80 min WS=0.09305387279663745 TNS=0.0
tt_100C_1v80 max WS=11.317221258240215 TNS=0.0
tt_100C_1v80 min WS=0.08983023607005908 TNS=0.0
ss_100C_1v60 max WS=-0.687277809672019 TNS=-21.231488279541733
ss_100C_1v60 min WS=0.18567888030452087 TNS=0.0
ss_n40C_1v60 max WS=-4.189726018044011 TNS=-130.4888465326457
ss_n40C_1v60 min WS=0.18500412836443383 TNS=0.0
ff_n40C_1v95 max WS=15.871505448031069 TNS=0.0
ff_n40C_1v95 min WS=0.06347266641938298 TNS=0.0
ff_100C_1v95 max WS=15.894228605363333 TNS=0.0
ff_100C_1v95 min WS=0.059112952317363035 TNS=0.0
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: set cn 0; set un 0
0
CASE02-CMD: foreach p [all_inputs -no_clocks] {
CASE02-CMD: puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
constrained_in2reg_max_endpoints=130 unconstrained_only=0
```

## 预算账单

① 总预算：600000 token（每 token 约 1.91 字节的保守换算；本次已交还合计 62141 token，含本账单）。

② 已交还的实例：
- B1 R1：1290 行，未截断
- B1 R2：1492 行，未截断

③ 未交还的实例：（无）

④ 以上未交还的结果已完整归档，未交还原因是累计超过公开的总预算，不是查询失败。
