# 一、观察

1. **网表和环境相同。** 两次记录共用同一网表 sha256、同一工具版本、同一工艺库、同一六点集合和同一组报告命令（context.md:16-17）。所以两组之间任何 slack 差异都不来自电路本身。
2. **结构路径数相同。** TOPO 都是 in2reg 130、reg2reg 0、reg2out 33（summary_R1.tsv:1-3；summary_R2.tsv:1-3）。
3. **差异只出现在 in2reg 的 setup（max）上，六个 scene 都是 R2 更差。**
   - tt_025C_1v80：11.191043 → 11.185458，差 0.005585（summary_R1.tsv:6；summary_R2.tsv:6）
   - tt_100C_1v80：11.321179 → 11.317222，差 0.003957（R1:14；R2:14）
   - ss_100C_1v60：−0.679952 → −0.687278，差 0.007326（R1:22；R2:22）
   - ss_n40C_1v60：−4.172595 → −4.189726，差 0.017131（R1:30；R2:30）
   - ff_n40C_1v95：15.881205 → 15.871506，差 0.009699（R1:38；R2:38）
   - ff_100C_1v95：15.902845 → 15.894229，差 0.008616（R1:46；R2:46）
   - WS max 行同样变化（R1:4,12,20,28,36,44；R2 同行号）。
4. **最差起点在所有 scene 都从 `in_a[*]` 换成了 `in_b[*]`。**
   - R1：tt/ss_100 为 in_a[34]，ff 为 in_a[3]（summary_R1.tsv:6,14,22,30,38,46）。
   - R2：tt/ss_100 为 in_b[35]，ss_n40/ff 为 in_b[2]（summary_R2.tsv:6,14,22,30,38,46）。
   - 终点都是 _12026_/D。
5. **其余各项逐位相同。**
   - 全部 hold（min）WS 和 in2reg min 相同，起点都是 rst→_12058_/D（R1/R2:5,7,13,15,21,23,29,31,37,39,45,47）。
   - reg2out max/min 全部相同（R1/R2:10-11,18-19,26-27,34-35,42-43,50-51）。
6. **两份详细报告的路径不同：** R1 为 in_a[34]→_10564_→…（path_R1.rpt:1,12-13），R2 为 in_b[2]→_10621_→…（path_R2.rpt:1,12-13）。
7. **两份报告的输入端口都显示施加了 input external delay 5.5820**（path_R1.rpt:11；path_R2.rpt:11），等于 intent 的 0.2·T（intent.md:3）。
8. **两个端口都表现出有驱动延迟：**
   - R1 in_a[34]：slew 0.3844，delay 0.2730，fanout 17，cap 0.0365（path_R1.rpt:12）
   - R2 in_b[2]：slew 0.4338，delay 0.3091，fanout 19，cap 0.0415（path_R2.rpt:12）
9. **两条路径在 _11302_/X 之后汇合，之后各级延迟逐项相同**（path_R1.rpt:33-87 与 path_R2.rpt:33-87）。
   - 汇合点到达时间相差 13.8053 − 13.7882 = 0.0171（path_R1.rpt:34；path_R2.rpt:34），等于 slack 差 −4.1726 vs −4.1897（path_R1.rpt:100；path_R2.rpt:100）。
   - required 27.3541 和 setup 0.5559 相同（两份文件 :94-95）。
10. **两者都接近"基线最差 setup slack ≈ −15%·T"**（−0.15 × 27.91 = −4.1865，context.md:24）：R2 为 −4.1897（−15.01%），R1 为 −4.1726（−14.95%）。这是弱线索。

# 二、结论和确定程度

**结论 A（确认）：差异不来自电路变快或变慢。**
- 网表、库、工具、scene 相同（context.md:16），所以差异只能来自两次运行实际生效的约束或分析设置不同。
- R1 的 in2reg setup slack 比 R2 大（数值更乐观），这只是"报告的 slack 变大"，不是"电路变快"。
- 同一条 in_a[34] 路径在两组中应完全相同，所以 R2 并没有让任何路径变慢。区别只在于 R2 里出现了一条比它更差的 in_b 路径。

**结论 B（假设）：R1 对 `in_b[63:0]`（64 个端口，可能是其中一部分）施加的输入约束比 intent 宽松。**
可能的形式，目前无法区分：
- (a) 缺少 `set_driving_cell buf_2`（理想驱动）。去掉端口上 0.3091 的驱动延迟和 0.43 的 slew，in_b[2] 路径到达时间至少提前约 0.3 ns，正好使它不再是最差路径。
- (b) set_input_delay -max 小于 5.582。
- (c) 完全没有 input delay，路径未被约束。

支持这一假设的事实：
- R2 中 in_b[2] 的外部延迟 5.582 和 buf_2 驱动延迟都与 intent 相符（path_R2.rpt:11-12）。
- R1 中 in_a[34] 也与 intent 相符（path_R1.rpt:11-12）。
- 因此"R2 正确、R1 的 in_b 乐观"能同时解释六个 scene 的起点切换和 R2 一致更差。

反向可能（R2 的 in_b 比 intent 更悲观）证据较弱，因为 R2 端口数值看起来与 intent 一致。但只看到 1 个端口、1 个 scene、rise 沿，所以不确定。

**结论 C（条件成立时才确认）：** 在以下两个条件都成立时，R2 是两者中忠实反映 intent 的记录，R1 的 in2reg setup 结果（包括 ss_n40 的 −4.1726）偏乐观：
- 检查请求 2 显示 R1 中 in_b 端口的到达时间缺少驱动延迟或外部延迟偏小；
- R2 中全部 130 个输入的到达时间都与 intent 一致。

**对其他端口：**
- in_valid、rst 的 max 约束，以及全部输入的 min 约束，两组是否一致：不确定。hold 最差点被 rst 主导，会掩盖 in_b 的 min 差异。
- 33 个输出的约束：reg2out 结果两组相同，大概率一致。但是否等于 intent（max 5.582、min 0、C_load 0.0024 pF），目前无法证明（intent.md:5）。

# 三、证据

**支撑：**
- 同网表、同环境：context.md:16-17
- 只有 in2reg max 变化，且全部变差：summary_R1.tsv 与 summary_R2.tsv 的 :4,6,12,14,20,22,28,30,36,38,44,46
- 起点从 in_a 切换到 in_b：同上行号
- min 和 reg2out 不变：两个 summary 的 :5,7,10-11 等
- R2 in_b[2] 的约束值与 intent 一致：path_R2.rpt:11-12；intent.md:3
- 共同尾段相同，差值完全来自汇合前：path_R1.rpt:33-100 与 path_R2.rpt:33-100

**缺失：**
- 两次运行实际生效的约束清单和覆盖检查（context.md:23）。
- R1 中 in_b 任一端口的到达时间和路径报告。
- R2 中 in_a[34] 的路径（用来验证"同一路径两组相同"）。
- in_valid、rst 和 min 约束的逐端口数据。
- 输出端口的 output delay 和负载。

# 四、检查请求

**1. 优先级 1，两组都执行（W01）：未约束的输入/输出和端点**
```
check_setup -verbose -no_input_delay -no_output_delay -unconstrained_endpoints
```

**2. 优先级 1，两组都执行（W02）：逐端口到达时间**
同时含外部延迟和驱动延迟，rise/fall 与 min/max 都有。
```
foreach p [all_inputs -no_clocks] { puts "== [get_full_name $p]"; report_arrival -scene ss_n40C_1v60 $p }
```

**3. 优先级 2，两组都执行（W06）：in_b[2] 的 setup 路径**
```
report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```

**4. 优先级 2，两组都执行（W06）：in_a[34] 的 setup 路径**
```
report_checks -from [get_ports {in_a[34]}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```

**5. 优先级 3，两组都执行（W03）：逐端口路径计数**
```
foreach p [all_inputs -no_clocks] { foreach d {max min} { set c [llength [find_timing_paths -from $p -path_delay $d -scene ss_n40C_1v60 -group_path_count 100000 -endpoint_path_count 1]]; set u [llength [find_timing_paths -from $p -path_delay $d -scene ss_n40C_1v60 -group_path_count 100000 -endpoint_path_count 1 -unconstrained]]; puts "[get_full_name $p] $d constrained=$c with_unconstrained=$u" } }
```

**6. 优先级 3，两组都执行（W06）：in_b[2] 的 hold 路径**
```
report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay min -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```

**7. 优先级 4，两组都执行（W06）：输出端 setup**
核对 output delay 和端口 cap 是否为 0.0024。
```
report_checks -to [get_ports {out_data[0]}] -path_delay max -scene ss_n40C_1v60 -fields {slew cap fanout} -digits 4
```

**8. 优先级 4，两组都执行（W06）：输出端 hold**
```
report_checks -to [get_ports {out_valid}] -path_delay min -scene ss_n40C_1v60 -fields {slew cap fanout} -digits 4
```

**9. 优先级 5，两组都执行（W06）：rst 和 in_valid 的 setup 路径**
```
report_checks -from [get_ports {rst in_valid}] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```

**10. 优先级 5，两组都执行（W08）：六个 scene 的 WNS 和 TNS**
```
foreach s {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { puts "$s" }; foreach d {max min} { puts "$d ws=[worst_slack -$d] tns=[total_negative_slack -$d]" }
```

**11. 优先级 6，只对 R1 执行：改变模型的对照**
只用来支持或反对假设 (a)，不能证实原始模型。
```
set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 -pin X -input_transition_rise 0 -input_transition_fall 0 [get_ports {in_b[*]}]
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4
```

**12. 优先级 7，两组都执行（W07）：检查类型汇总**
```
report_check_types -verbose -scene ss_n40C_1v60
```
注：OpenSTA 3.1.0 的 report_check_types 若不接受 `-scene`，会报错，结果原样交还。
