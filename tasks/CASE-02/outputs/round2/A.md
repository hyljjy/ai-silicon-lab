# 一、观察

**第 1 轮材料中的差异（沿用第 1 轮，压缩）**
1. 两组的网表、工具、库、六个 scene 和报告命令都相同（context.md:16-17）。TOPO 也相同（summary_R1.tsv:1-3；summary_R2.tsv:1-3）。
2. 只有 in2reg 的 max 发生变化，六个 scene 都是 R2 更差。WS max 同步变化（summary_R1.tsv 与 summary_R2.tsv 的 :4,6,12,14,20,22,28,30,36,38,44,46）。其中 ss_n40 从 −4.172595 变为 −4.189726（:30）。
3. 最差起点从 in_a[34]/in_a[3] 换成了 in_b[35]/in_b[2]，终点都是 _12026_/D（同上行号）。
4. hold 和 reg2out 的各项逐位相同（两个 summary 的 :5,7,10-11,13,15,18-19 等）。
5. 两条路径在 _11302_/X 之后逐级相同，差值 0.0171 全部来自汇合之前（path_R1.rpt:34,100；path_R2.rpt:34,100）。

**第 1 轮查询的结果（下文用"A编号 R组"指代）**
6. **A1 R1**：check_setup 报 "64 input ports missing set_input_delay"，名单正好是 in_b[0]–in_b[63]。没有缺 output delay 或未约束端点的警告。
7. **A1 R2**：没有任何警告。返回值是 1，R1 是 0。返回值的具体含义不确定。
8. **A2 R1**（ss_n40）：rst、in_valid、in_a[63:0] 都是 `(clk ^) r 0.00:5.58 f 0.00:5.58`。in_b[63:0] 全部是 ` r 0.00:0.00 f 0.00:0.00`，没有时钟标签。
9. **A2 R2**（ss_n40）：全部 130 个输入都是 `(clk ^) r 0.00:5.58 f 0.00:5.58`。
10. **A5 R1**：in_b[*] 的 max 和 min 都是 constrained=0、with_unconstrained=32。rst、in_valid 为 1/1，in_a[*] 为 32/32。
11. **A5 R2**：全部 130 个端口的 constrained 与 with_unconstrained 相等（in_a、in_b 都是 32）。
12. **A3 / A6**：R1 中 in_b[2] 的 setup 和 hold 都是 "No paths found."。R2 中 in_b[2] 的 setup slack 为 −4.1897（与 path_R2.rpt:100 相同），hold 为 0→_12030_/D，input external delay 0.0000，slack 1.9129（MET）。
13. **A4**：in_a[34] 的路径在 R1 和 R2 中逐行相同，slack 都是 −4.1726。
14. **A7 / A8**：两组相同。out_data[0] 的 output external delay 为 5.5820（max），Q 网 cap 0.0024；out_valid 的 output external delay 为 0.0000（min），cap 0.0024。
15. **修正第 1 轮的一个预期**：report_arrival 在端口上只给出外部延迟 5.58（A2 R2 in_b[2]），而路径报告中端口点是 5.8911（path_R2.rpt:12）。所以 A2 不能用来验证驱动单元。

# 二、结论和确定程度

**结论 1（确认）：差异来自 R1 的约束覆盖缺口，不是电路变化。**
- R1 对 `in_b[63:0]` 这 64 个端口完全没有 set_input_delay，max 和 min 都没有。这 64 个端口出发的 in2reg 路径在 R1 中都是未约束路径，不参与 setup 和 hold 检查。
- 依据：A1 R1、A2 R1、A3 R1、A5 R1、A6 R1。
- 这修正了第 1 轮的假设 B：三种形式中成立的是 (c)"没有 input delay"。(a) 缺驱动单元、(b) 外部延迟偏小都不是差异原因。R1 中 in_b 是否设置了 driving cell 不确定，但在未约束的情况下它不影响报告的 slack。

**结论 2（确认）：R1 的 slack 更大只是"报告的 slack 变大"，不是"电路变快"。**
- 同一条 in_a[34] 路径在两组中逐行相同（A4）。
- R1 只是少检查了 in_b 这一半输入锥，因此 R1 各 scene 的 in2reg setup WNS 偏乐观。在 ss_n40 偏乐观 0.0171 ns，其余 scene 的差值见观察 2。
- R1 的 TNS 和违例端点数也可能偏小，但具体数值不确定（第 1 轮的 TNS 查询未执行）。

**结论 3（确认）：rst、in_valid、in_a[63:0] 在两组中的输入约束一致。**
- 在 ss_n40 下，这 66 个端口的 max 都是 5.58，min 都是 0（A2）。
- R1 中 in_b 缺 min 约束这一点在 hold 汇总里看不出来，因为 R2 的 hold 最差点仍是 rst（summary_R2.tsv:7 等）。也就是说，R2 中 in_b 的 hold slack 在六个 scene 下都不低于该 scene 的 rst 值。

**结论 4（条件成立时才确认）：R2 完整符合 intent.md。** 需要以下条件都成立：
- 其余五个 scene 的 input delay 同样为 max 5.582、min 0；
- 全部 130 个输入的驱动单元都是 buf_2；
- 其余 31 个输出的 output delay（max 5.582、min 0）和负载 0.0024 pF 都与 intent 一致。

目前已经核实的部分：
- ss_n40 下全部 130 个输入的外部延迟；
- out_data[0] 的 max 和 out_valid 的 min；
- in_a[34] 和 in_b[2] 的端口有非零驱动延迟，与有驱动单元相符，但单元类型未经证明。

R2 的 ss_n40 WNS 为 −4.1897，约等于 −15.01%·T，与 T 的校准方式吻合（context.md:24）。这是弱线索，支持 R2 是基线。

**两组的输出约束（确认部分）**：A1 中两组都没有缺 output delay 的警告，两个 summary 的 reg2out 结果也相同，说明两组的输出约束一致。

# 三、证据

**支撑：**
- 缺口的范围是 in_b[63:0]，共 64 个端口：A1 R1 的名单，A2 R1 的无时钟 0.00 到达时间。
- 缺口导致这些路径未被约束：A5 R1（0/32），A3 R1、A6 R1 都是 "No paths found."。
- R2 覆盖了全部 130 个输入：A1 R2 没有警告，A2 R2 全部为 5.58，A5 R2 中 constrained 都等于 with_unconstrained。
- 共同路径不变：A4 的 R1 与 R2 逐行相同。
- 差值的来源：R2 中 in_b[2] 的 −4.1897（A3 R2）与 in_a[34] 的 −4.1726（A4）之差为 0.0171，这条 in_b 路径在 R1 中不被检查。
- 输出端：A7、A8；context.md:17；intent.md:3-4。

**仍然缺少：**
- 两次运行展开后的约束清单（context.md:23）。
- 其余五个 scene 的逐端口到达时间。
- in_b 端口的驱动单元类型（两组都缺）。
- 31 个输出的 output delay 和负载。
- R1 与 R2 的 TNS 和违例端点数。
- check_setup 返回值 0 和 1 分别代表什么。

# 四、检查请求

（第 2 轮的查询只记录、不执行，以下供后续使用。）

**1. 优先级 1，两组都执行（W05）：六个 scene 逐端口到达时间与路径计数**
```
foreach s {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { foreach p [all_inputs -no_clocks] { puts "$s [get_full_name $p]"; report_arrival -scene $s $p } }
```

**2. 优先级 1，两组都执行（W06）：用 buf_2 的延迟核对 in_b[2] 的驱动**
```
report_dcalc -from [get_ports {in_b[2]}] -scene ss_n40C_1v60 -digits 4
```

**3. 优先级 2，两组都执行（W08）：六个 scene 的 WNS 和 TNS**
```
foreach s {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { puts $s }; foreach d {max min} { puts "$d ws=[worst_slack -$d] tns=[total_negative_slack -$d]" }
```

**4. 优先级 2，两组都执行：全部输出端口的 max 和 min**
```
foreach p [all_outputs] { foreach d {max min} { report_checks -to $p -path_delay $d -scene ss_n40C_1v60 -fields {cap} -digits 4 } }
```

**5. 优先级 3，只对 R2 执行：其他 scene 下 in_b[2] 的 setup 路径**
```
report_checks -from [get_ports {in_b[2]}] -to [all_registers -data_pins] -path_delay max -scene ff_n40C_1v95 -fields {slew cap input_pins fanout} -digits 4
```
