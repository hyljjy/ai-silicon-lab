## 一、观察

1. R1 与 R2 的 TOPO、reg2out、in2reg min 完全一致；只有 in2reg max 最差路径不同（summary_R1.tsv:1-3,7,10-11,15,18-19,23,26-27,31,34-35,39,42-43,47,50-51；summary_R2.tsv:1-3,7,10-11,15,18-19,23,26-27,31,34-35,39,42-43,47,50-51）。
2. in2reg max 的 CAT 起点整体从 R1 的 `in_a` 组系统性地变成 R2 的 `in_b` 组；端点都是 `_12026_/D`（summary_R1.tsv:6,14,22,30,38,46；summary_R2.tsv:6,14,22,30,38,46）。
3. R2 的 in2reg max 最差 slack 比 R1 更负（更差），六个 corner 都如此（summary_R1.tsv:4,12,20,28,36,44；summary_R2.tsv:4,12,20,28,36,44）。
4. B1 查询显示：R1 中 `in_a[34]`、`in_a[3]` 有正常 in2reg max 路径，`in_b[2]`、`in_b[35]` 报 `No paths found`；R2 中这四个端口都有正常 in2reg max 路径（B1 输出，Q1）。
5. B1 查询计数显示：R1 有 66 个非时钟输入端口有正常 in2reg max 路径、64 个端口只有带 `-unconstrained` 才出现的结构路径；R2 全部 130 个端口既有正常路径也有 unconstrained 路径（B1 输出，Q2/Q6）。
6. 同名起点的路径数据在 R1 与 R2 中一致：例如 `in_a[34]` 都是到达 31.5267、slack −4.1726；`in_a[3]` 都是到达 31.4905、slack −4.1363；R2 额外出现的 `in_b[2]` 为到达 31.5439、slack −4.1897（B1 输出，Q1）。
7. 相应 TNS 也变差：R1 的 ss_100C/ss_n40C max TNS 为 −21.0044/−129.9406，R2 为 −21.2315/−130.4888（B1 输出，Q5），与只有 in2reg max 侧变化一致。

## 二、结论和确定程度

结论：R1 与 R2 的差异不是“同一约束下 public 路径变慢/变快”，而是两次运行的**正常 in2reg 时序路径集合不同**。具体地，R1 有 64 个非时钟输入端口只有结构路径、未进入受约束的正常 setup/hold 检查；R2 中这 64 个端口被正常计时。于是 R1 的 in2reg max 始终只反映剩余有正常路径的 `in_a` 侧最差路径，R2 则额外出现了 `in_b` 侧更差的路径，表现为 R2 的报告 slack 更负。**这不能解释为电路变快或变慢**：同一端口、同一公共段在两次记录里到达时间完全相同。

确定程度：

- 确认：R1 与 R2 的正常 in2reg 路径覆盖数量不同，R1 有 64 个端口仅 `-unconstrained` 可见、R2 全部 130 个端口正常可见；这是 B1 查询直接得到的结果。
- 条件成立时才确认：这 64 个端口就是 `in_b[63:0]` 整组。依据是 `in_b[2]`、`in_b[35]` 在 R1 无正常路径、R2 有，且缺失数量 64 与 `in_b` 位宽一致；但 B1 输出没有打印真实端口名，仍需真实端口名映射确认。
- 端口范围（条件成立时）：`in_b[63:0]` 的 64 个端口为受影响组；`in_a[63:0]` 和既有 `in_a` 路径不受影响。

## 三、证据

支持“不是网表/库/公共路径变化”：

- R1/R2 的 TOPO、reg2out、in2reg min 完全一致（summary_R1.tsv:1-3,7,10-11,15,18-19,23,26-27,31,34-35,39,42-43,47,50-51；summary_R2.tsv 对应行）。
- 两条 path 报告的 input external delay 均为 5.5820，required time 均为 27.3541，且自 `_11302_/X` 后公共后缀逐段一致（path_R1.rpt:11,32-98；path_R2.rpt:11,32-98）。
- B1 查询中 R1/R2 对同一端口的 `in_a[34]`、`in_a[3]` 返回相同到达时间和 slack；R2 在 R1 缺失正常路径的 `in_b` 上出现新最差路径。

支持“根因在路径是否被正常计时”：

- B1 查询的 `find_timing_paths` 不带/带 `-unconstrained` 的计数差异（B1 输出，Q2/Q6）。
- B1 查询中 R1 的 `in_b[2]`、`in_b[35]` 正常 `report_checks` 无路径，而 R2 有路径（B1 输出，Q1）。

缺失的证据：

- 这 64 个端口的真实名称映射，确认是否为 `in_b[63:0]`。
- R1、R2 各自实际展开的输入约束清单和覆盖检查结果（context.md:23）；第1轮尝试读取 `input_delay_*` 属性失败，未能用该方式取得。
- 是否有 `set_false_path`、`set_multicycle_path`、`set_disable_timing` 等作用于这些端口；现有材料未提供。

## 四、检查请求

以下为本轮新增查询；按第2轮规则仅记录、不执行：

```tcl
# Q1 优先级1；对 R1 和 R2
# 打印每个非时钟输入端口真实名，及 max 正常/仅 unconstrained 计数
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set name [get_name $p]
  set n [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set u [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  puts "$name constrained=$n unconstrained=$u"
}

# Q2 优先级1；对 R1 和 R2
# 只筛选名字匹配 in_b 的端口，验证是否恰好 64 个在 R1 缺失正常路径
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set name [get_name $p]
  if {[string match "in_b*" $name]} {
    set n [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
           -path_delay max -scene $scene]]
    set u [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
           -path_delay max -scene $scene -unconstrained]]
    puts "$name constrained=$n unconstrained=$u"
  }
}

# Q3 优先级2；对 R1 和 R2
# 关键端口逐一报告，核验 R1 缺失路径、R2 出现的端口
foreach p [get_ports {in_a[34] in_a[3] in_b[2] in_b[35]}] {
  puts "PORT [get_name $p]"
  catch { report_checks -from $p -to [get_pins _12026_/D] \
           -path_delay max -scene ss_n40C_1v60 -fields {delay} -digits 4 }
}

# Q4 优先级3；对 R1 和 R2
# 列出 R1/R2 中“仅 unconstrained”端口的真实名
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set n [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set u [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$n == 0 && $u > 0} { puts "unconstrained_only [get_name $p]"; incr un }
  if {$n > 0} { incr cn }
}
puts "constrained=$cn unconstrained_only=$un"
```
