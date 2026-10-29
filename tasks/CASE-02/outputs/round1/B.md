一、观察

1. 两次记录的**结构路径数完全相同**：in2reg=130、reg2reg=0、reg2out=33（summary_R1.tsv:1-3；summary_R2.tsv:1-3）。
2. 两次记录的 **reg2out** 的 WS 值和 CAT 值在六个 corner 下完全一致（summary_R1.tsv:10-11,18-19,26-27,34-35,42-43,50-51；summary_R2.tsv:10-11,18-19,26-27,34-35,42-43,50-51）。
3. 两次记录的 **in2reg min** WS/CAT 完全一致，起点都是 `rst`、终点 `_12058_/D`（summary_R1.tsv:7,15,23,31,39,47；summary_R2.tsv:7,15,23,31,39,47）。
4. 仅 **in2reg max** 的 setup 最差 slack 不同：R2 比 R1 变小（更差）约 0.004–0.017 ns。具体为 tt_025C_1v80 由 11.191043 到 11.185458（R1:4，R2:4）；tt_100C_1v80 由 11.321179 到 11.317221（R1:12，R2:12）；ss_100C_1v60 由 -0.679952 到 -0.687278（R1:20，R2:20）；ss_n40C_1v60 由 -4.172595 到 -4.189726（R1:28，R2:28）；ff_n40C_1v95 由 15.881204 到 15.871505（R1:36，R2:36）；ff_100C_1v95 由 15.902846 到 15.894229（R1:44，R2:44）。
5. 与上一条对应，**in2reg max 的最差路径起点整体换组**：R1 全部在 `in_a` 侧（tt/tt100/ss100/ss_n40 为 `in_a[34]`，ff_n40/ff100 为 `in_a[3]`，见 summary_R1.tsv:6,14,22,30,38,46）；R2 全部在 `in_b` 侧（tt/tt100/ss100 为 `in_b[35]`，ss_n40/ff_n40/ff100 为 `in_b[2]`，见 summary_R2.tsv:6,14,22,30,38,46）；两者终点都是 `_12026_/D`。
6. 两条详细路径报告都来自 `ss_n40C_1v60` 的 in2reg setup 最差路径。R1 起点 `in_a[34]`、到达 31.5267、slack -4.1726（path_R1.rpt:1,88,100）；R2 起点 `in_b[2]`、到达 31.5439、slack -4.1897（path_R2.rpt:1,88,100）。
7. 两条路径报告的 input external delay 同为 5.5820（path_R1.rpt:11；path_R2.rpt:11），data required time 同为 27.3541（path_R1.rpt:94-95；path_R2.rpt:94-95）；且都在 `_11302_/X` 之后进入相同的公共后缀（path_R1.rpt:32 起为 12.8449；path_R2.rpt:32 起为 12.8620，到终点各段 delay 一致）。

二、结论和确定程度

结论：两次记录的差异最可能来自**两次运行实际生效的输入侧约束/路径例外不同**（尤其是 R1 与 R2 对 `in_a` 或 `in_b` 相关输入的 input delay 覆盖/数值或 false/multicycle/disables 不同），而不是网表、库、corner、负载或内部电路速度发生了变化。R2 相对 R1 的“报告 slack”不是变大，而是 **in2reg max setup slack 变小（更差）**；这不是“电路变快”，也不是公共门路径变慢——两条路径的公共尾部相同，只是被报告为最差的输入起点从 `in_a` 侧换到了 `in_b` 侧。

确定程度：**条件成立时才确认**。因为实际生效的约束清单和覆盖检查尚未提供（context.md:23），目前只能说是强假设。确认条件：若检查请求显示 R1 与 R2 在 `in_a`/`in_b` 的 input delay 覆盖不同（R2 对 `in_a` 侧没有 5.582 的 max input delay，或设小/排除，导致 `in_b` 侧成为最差；或在 R1 中 `in_b` 侧未被同等上报），则本结论成立。端口范围重点在 `in_a[63:0]` 与 `in_b[63:0]`。

三、证据

- 支持差异“不是全局网表/库/负载变化”的证据：TOPO、reg2out、in2reg min 完全一致（summary_R1.tsv:1-3,7,10-11,15,18-19,23,26-27,31,34-35,39,42-43,47,50-51；summary_R2.tsv 对应行）。
- 支持差异在“输入侧选径”的证据：六个 corner 的 in2reg max 起点从 R1 的 `in_a` 组系统性地变成 R2 的 `in_b` 组（summary_R1.tsv:6,14,22,30,38,46；summary_R2.tsv:6,14,22,30,38,46），而终点、min 起点保持不变。
- 支持“两条路径只是起点不同、公共段不变”的证据：两条 path 报告的 input external delay 均为 5.5820，required time 均为 27.3541，且自 `_11302_/X` 后逐段 delay 完全一致（path_R1.rpt:11,32-98；path_R2.rpt:11,32-98）。
- 缺失的证据：R1、R2 各自展开后每个非时钟输入端口的 `input_delay_max/min`（或等价报告）、`driving_cell`/transition、是否有 `set_false_path`/`set_multicycle_path`/`set_disable_timing` 作用于 `in_a`/`in_b`，以及 R1/R2 对全部 130 个非时钟输入的覆盖检查结果。

四、检查请求

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
