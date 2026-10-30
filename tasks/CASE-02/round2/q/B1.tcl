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
