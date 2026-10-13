# dot4sat 基线综合后 STA 分析（ss_n40C_1v60 下的 in2reg setup 违例）

## 一、报告事实

**约束与周期**

1. T = 27.91 ns，C_load = 0.0024 pF（values.txt:1-2）。
2. 输入延迟 max 为 0.2T（case01_sdc.tcl:13）。0.2 × 27.91 = 5.582，与报告中的 input external delay 5.5820 一致（path_report.rpt:11）。
3. 时钟是理想时钟，latency、uncertainty、transition 都为 0（case01_sdc.tcl:5-9；path_report.rpt:10、91-92）。
4. 输入由 `buf_2` 驱动，输入 transition 为 0（case01_sdc.tcl:15-16；context.md:22）。

**这条最差路径**

1. 起点是 `in_b[2]`，终点是 `_12026_`（`dfxtp_1`）的 D 端，角点为 ss_n40C_1v60（path_report.rpt:1-5、87）。
2. 时间汇总：
   - arrival = 31.5439 ns（path_report.rpt:88）
   - required = 27.3541 ns，其中 setup 时间为 0.5559 ns（path_report.rpt:93-95）
   - slack = −4.1897 ns（path_report.rpt:100）
   - −4.1897 / 27.91 ≈ −15.0%，与"约为周期的 −15%"的校准说法一致（context.md:28）
3. 从输入端口算起的数据路径延迟为 31.5439 − 5.582 = 25.962 ns，其中包括端口驱动的 0.3091 ns（path_report.rpt:12）。路径上共 37 个单元，从 `_10621_` 到 `_11512_`（path_report.rpt:13-87）。
4. 输入端口 `in_b[2]` 的 fanout 为 19，cap 为 0.0415 pF，slew 为 0.4338 ns，延迟为 0.3091 ns（path_report.rpt:12）。

**按单元类型和时间可以把路径粗分为四段（分段是我的解读，不是工具给出的）**

| 段 | 单元类型 | 起止证据 | 时间区间 (ns) | 耗时 (ns) |
|---|---|---|---|---|
| ① | `nand2` 加一串 `xor2/xnor2/xor3/xnor3/maj3`，形态像部分积加全加器压缩树 | path_report.rpt:13-38 | 5.8911 → 15.1930 | ≈ 9.30 |
| ② | `maj3` 与 `a21oi/o21ai/o21bai` 交替，形态像逐位进位链 | path_report.rpt:39-68 | 15.1930 → 23.8052 | ≈ 8.61 |
| ③ | `o31ai/a221oi/o311ai/a311oi/o311ai` 加 `nand2`、`xnor2` | path_report.rpt:69-82 | 23.8052 → 28.0452 | ≈ 4.24 |
| ④ | `_11509_`（`o21ai_0`）后接 `_11512_`（`o21ai_0`） | path_report.rpt:83-87 | 28.0452 → 31.5439 | ≈ 3.50 |

- 单级 `xor3/xnor3/maj3` 在本角点约为 0.73–1.09 ns（例如 path_report.rpt:16、20、26、34、50）。
- 路径上的单元几乎都是最小尺寸（`_0`/`_1`）。
- `o311ai_0`、`o31ai_1`、`o21ai_0` 的输出 slew 在 0.5–1.02 ns 之间（path_report.rpt:44、54、70、74、78）。

**第④段的细节**

1. `_11509_`（`o21ai_0`）的 fanout 为 31，cap 为 0.0511 pF，输出 slew 为 3.2455 ns，单级延迟为 2.6362 ns，是路径上最大的一项（path_report.rpt:84）。
2. 下游 `_11512_` 因输入 slew 很大，延迟为 0.8625 ns（path_report.rpt:86）。
3. D 端 slew 为 0.3761 ns（path_report.rpt:87），对应的 setup 时间为 0.5559 ns（path_report.rpt:94）。

**slack 汇总**

1. 拓扑结构：in2reg 有 130 个起点，reg2reg 有 0 条路径，reg2out 有 33 个起点（slack_summary.tsv:8-10）。130 = 128 + `in_valid` + `rst`，33 = 32 + 1，这是我的推算。
2. 各角点 setup WS：

   | 角点 | WS (ns) | 证据 |
   |---|---|---|
   | tt_025C_1v80 | +11.19 | slack_summary.tsv:11 |
   | tt_100C_1v80 | +11.32 | slack_summary.tsv:19 |
   | ss_100C_1v60 | −0.687 | slack_summary.tsv:27 |
   | ss_n40C_1v60 | −4.19 | slack_summary.tsv:35 |
   | ff_n40C_1v95 | +15.87 | slack_summary.tsv:43 |
   | ff_100C_1v95 | +15.89 | slack_summary.tsv:51 |

   只有两个 ss 角点违例，并且低温比高温更差。
3. 所有角点的最差 in2reg 终点都是 `_12026_/D`：
   - 在 tt 和 ss_100C 下，起点是 `in_b[35]`（slack_summary.tsv:13、21、29）；
   - 在 ss_n40C 和 ff 下，起点是 `in_b[2]`（slack_summary.tsv:37、45、53）。
4. reg2out 的最差路径都是 `_12026_/Q → out_data[0]`，ss_n40C 下 slack 为 +21.69（slack_summary.tsv:41）。由此推测 `_12026_` 很可能就是 `out_data[0]` 寄存器，但这一点不确定。
5. hold 方向：所有角点的 min slack 都为正，最小为 +0.059，路径是 `rst → _12058_/D`（slack_summary.tsv:52-54）。
6. ss_n40C 的 WS 为 −4.189726（slack_summary.tsv:35），与 path_report.rpt:100 一致。

**RTL**

1. 四个有符号 16×16 乘积用一条表达式求和，得到 34 位结果，然后饱和到 32 位，只寄存输出（dot4sat.v:23-29、34-40）。
2. 饱和判断使用两个 34 位比较：`sum > SMAX` 和 `sum < SMIN`（dot4sat.v:34-35）。
3. `out_data` 不复位，也没有使能（dot4sat.v:3、40）。

**分析模型和综合配方的限制**

1. 不计连线寄生（context.md:20），所以布线后路径会更慢。
2. 综合配方没有时钟目标（context.md:24），因此网表中基本是最小尺寸单元，这与报告观察相符。

## 二、原因假设

**H1（主因）：L = 1 时，整条乘加饱和链放在一个周期里，逻辑级数过深。**
- 依据：37 级、约 25.6 ns 的门延迟分散在许多单元上；最大的单级 2.64 ns 也只占约 10%。
- in2reg 的可用预算只有 T − 0.2T − setup ≈ 27.91 − 5.582 − 0.556 = 21.77 ns，而实际需要 25.96 ns。
- 按这条路径反推，最小周期约为 T ≥ (25.962 + 0.556) / 0.8 ≈ 33.15 ns。
- 推翻条件：如果对 `_11509_` 等少数单元做尺寸替换的对照（见四-Q5）后 slack 就转正，说明问题是局部的，不是结构性的，H1 就不再是主因。

**H2：最终进位传播加法器（CPA）是逐位进位（ripple）结构。**
- 依据：第②、③段约 12.8 ns 是 `maj3`/AOI/OAI 交替的串行链（path_report.rpt:39-82）。
- 进一步推测：Yosys 很可能把 4 个乘积和 3 次加法合成成一棵大压缩树，再接一个 34 位 ripple CPA，因为路径上只看到一段进位链。这一推测不确定。
- 推翻条件：
  - 第②段单元的扇入不来自相邻位的 carry/propagate 信号；
  - 或者经过这些单元的路径终点分布不随位序递增；
  - 或者网表中存在前缀（prefix）结构。

**H3：饱和选择信号由弱单元驱动高扇出，造成大约 2.5–3 ns 的额外延迟。**
- 依据：`_11509_` 是 `o21ai_0`，fanout 为 31，slew 为 3.25 ns（path_report.rpt:84）。它很可能就是 `sum > SMAX` / `sum < SMIN` 合成出的溢出选择信号，驱动约 31 个输出位的选择逻辑。这一点不确定。
- 推翻条件：
  - `_11509_/Y` 的负载不是 `out_data[*]` 对应寄存器前的选择单元；
  - 或者把它换成大尺寸单元后，最差 slack 改善不到 1 ns。
- 即使 H3 成立，单靠它也不足以消除 −4.19 ns 的违例，只能部分解释。

**H4：没有时钟目标的综合普遍使用最小尺寸单元，使每一级都偏慢，在 ss 低压角点下更明显。**
- 推翻条件：对整条路径做尺寸替换的对照后，slack 改善很小，比如不到 1 ns。

**H5：角点效应。ss_n40C_1v60 低压低温下出现温度反转，比 ss_100C 慢约 3.5 ns。**
- 这是工艺库的特性，不属于设计缺陷，但它决定了最差角点是哪一个。
- 推翻条件：同一条路径（相同的 `-from`/`-through`/`-to`）在 ss_100C 下的 arrival 不小于 ss_n40C 下的值。

**H6（排除项）：输入端口驱动不是主因。**
- `buf_2` 驱动 19 个负载只耗时 0.309 ns，远小于 4.19 ns 的违例量。
- 推翻条件：其他起点的路径里端口延迟占比显著更大。

**说明：IO 预算占用 0.2T（5.58 ns）。** 即使输入延迟为 0，slack 也只有约 +1.39 ns。但约束不能改，所以这一项只作背景，不作为修改方向。

## 三、缺失的证据

1. `_12026_` 对应 `out_data` 的哪一位。目前只有 reg2out 结果的旁证（slack_summary.tsv:41）。
2. `_11509_/Y` 驱动的 31 个负载分别是什么，`_11509_` 的逻辑功能是不是饱和选择。
3. 违例的终点有多少、违例路径的 slack 分布、TNS，以及各违例终点在 ss_100C 下的情况。目前只有每类路径的最差一条。
4. 第②段单元对应 34 位和的哪些位；CPA 的结构和位宽；乘积与求和是否被合并成一棵树。
5. 关键路径中间节点的到达时间，用来选择流水线切割点。例如压缩树输出、各乘积、34 位和、溢出判断信号。
6. 基线面积：单元数、总面积、触发器面积，以及 `dfxtp_1` 的库面积。这些决定了 1.25 倍面积上限下能加多少寄存器。
7. ss_n40C 下 `dfxtp_1` 的 clk→Q 延迟和 setup 时间，用于计算 reg2reg 预算。
8. 布线后寄生对裕量的影响。本分析不读取寄生参数（context.md:20），所以这一项在本环境下无法获得。

## 四、下一步查询

以下按 OpenSTA 3.1.0 书写。部分选项名称我不能完全确定，已单独标注。

**Q1：确认终点和起点所在的实例**
```tcl
report_instance _12026_
report_net -digits 4 [get_nets -of_objects [get_pins _12026_/Q]]
report_net -digits 4 [get_nets -of_objects [get_pins _12026_/D]]
```

**Q2：统计违例终点的数量和分布（ss_n40C 与 ss_100C）**
```tcl
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
  -scene ss_n40C_1v60 -group_path_count 200 -endpoint_path_count 1 -slack_max 0 -format end -digits 4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max \
  -scene ss_100C_1v60 -group_path_count 200 -endpoint_path_count 1 -slack_max 0 -format end -digits 4
set ps [find_timing_paths -scenes ss_n40C_1v60 -path_delay max -group_path_count 1000 -endpoint_path_count 1 -slack_max 0]
puts [llength $ps]
report_tns -digits 4   ;# 无场景选项，结果对应全部场景（不确定是取最差还是汇总）
```
注：选项名 `-group_path_count`（旧版本为 `-group_count`）在 3.1.0 中的确切写法不确定。

**Q3：分析 `_11509_` 的负载与功能**
```tcl
report_instance _11509_
report_net -digits 4 [get_nets -of_objects [get_pins _11509_/Y]]
report_checks -through [get_pins _11509_/Y] -path_delay max -scene ss_n40C_1v60 \
  -group_path_count 40 -endpoint_path_count 1 -format end -digits 4
```

**Q4：取中间节点的到达时间，用于选择切割点和定位进位链**
```tcl
foreach p {_11340_/X _11434_/Y _11451_/Y _11507_/Y _11509_/Y} {
  report_checks -through [get_pins $p] -path_delay max -scene ss_n40C_1v60 \
    -fields {slew cap input_pins fanout} -digits 4 -format summary
}
report_net [get_nets -of_objects [get_pins _11421_/X]]   ;# 看进位链单元的扇入扇出
```

**Q5：尺寸替换的对照（只作对照，用完恢复）**
```tcl
replace_cell _11509_ sky130_fd_sc_hd__o21ai_4
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
replace_cell _11509_ sky130_fd_sc_hd__o21ai_0
```
如果改善不到 1 ns，H3 就被弱化。还可以把第②段的 `maj3_1` 换成 `maj3_4` 做同样的对照，用来检验 H4。

**Q6：同一路径的角点对照，用于检验 H5**
```tcl
foreach s {ss_100C_1v60 ss_n40C_1v60 tt_025C_1v80} {
  report_checks -from [get_ports {in_b[2]}] -through [get_pins _11509_/Y] -to [get_pins _12026_/D] \
    -path_delay max -scene $s -digits 4 -format summary
}
```

**Q7：约束对照（只作对照，不作为修改）**
```tcl
set_input_delay -clock clk -max 0 [get_ports {in_a[*] in_b[*] in_valid rst}]
report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -digits 4
set_input_delay -clock clk -max [expr {0.2*27.91}] [get_ports {in_a[*] in_b[*] in_valid rst}]
```

**Q8：库数据与面积**
```tcl
report_lib_cell sky130_fd_sc_hd__dfxtp_1   ;# 是否支持此命令不确定
set a 0
foreach c [get_cells *] { set a [expr {$a + [get_property [get_property $c liberty_cell] area]}] }
puts $a
```
注：`liberty_cell` 和 `area` 这两个属性名在 3.1.0 中是否可用不确定。如果不可用，就需要综合端的 Yosys `stat -liberty` 结果，这超出了本材料的范围。

## 五、可能的修改

**时序预算（以 ss_n40C 估算）**
- 一级 in2reg 的组合逻辑可用约 27.91 − 5.582 − setup(0.3–0.56) ≈ 21.8–22.0 ns，含端口驱动。
- 一级 reg2reg 可用约 27.91 − clk→Q − setup，估计约 26.5–27 ns。clk→Q 需要用 Q8 确认。
- 现有总组合逻辑约 26.0 ns，小于一个 reg2reg 周期。所以只要加 1 级内部流水线（L = 2），并把切割点放在路径上大约 4.5–21 ns 之间，就满足关键路径的要求。L = 3 没有必要。
- `out_data` 应保持直接从寄存器输出。reg2out 目前有约 +21.7 ns 的裕量（slack_summary.tsv:41），不需要改动。

**方案 A（推荐，L = 2）：在压缩树输出处切割，寄存进位保留形式**
1. 在 RTL 中显式写出部分积生成和 4 个乘积合并的压缩树，得到两个约 34 位的向量（sum 和 carry），在压缩树末端寄存，约 68 个触发器。
2. 第二级做 CPA 和饱和。
3. 按段①的约 9.3 ns 估算，第一级到达时间约为 15.2 ns，裕量很大；第二级约为 clk→Q + 16.4 ns，也有较大裕量。
4. 增加的面积约为 68 个 `dfxtp_1`，需要用 Q8 核对是否在 1.25 倍以内。
5. 代价：RTL 编写工作量大，而且要用随机测试和边界向量，与原 RTL 做等价验证（例如全 −32768 相乘时的饱和情况）。

**方案 B（L = 2，实现更简单）：寄存两个部分和**
1. 寄存 `s01 = p0 + p1` 和 `s23 = p2 + p3`，每个 33 位，共 66 个触发器。
2. 第二级计算 `s01 + s23` 并饱和。
3. 风险：第一级仍然包含"乘法树加 33 位 ripple 加法"。按现有分段估算，第一级时间可能接近 22 ns 的预算，能否满足不确定，必须用重新综合和 STA 验证（Q4 的中间节点时间可以作为参考）。

**方案 C（L = 2，作为备选）：寄存 4 个乘积**
1. 共 128 个触发器，第一级只有乘法，第二级是加法和饱和。时序最稳。
2. 面积增加最多，可能超出 1.25 倍上限，需要先查清基线面积。

**不建议的做法**
- 只寄存 34 位和、把饱和留到第二级：第一级仍然包含大部分 CPA，到达时间约 27.4–28 ns，仍然违例。
- 只寄存输入：reg2reg 的余量估计只有约 0.5–1 ns，而且需要 128 个以上的触发器。

**所有流水线方案共同的要求**
1. `in_valid` 要跟随同样的级数延迟，每级 valid 都用同步 `rst` 清零，保证 L 固定且每周期都能接收一笔新交易。
2. 数据寄存器可以不复位，与现有规范一致（dot4sat.v:3）。
3. 重新检查 hold。新增 reg2reg 路径之后，理想时钟下 clk→Q 是否大于 hold 时间，需要用 `report_checks -path_delay min` 在 ff 角点确认。

**方案 D（L = 1，辅助手段，单独使用把握不大）**
1. 把饱和判断改写为 `sum[33:31]` 是否全相同，饱和值由 `sum[33]` 决定，代替两个 34 位比较。
2. 把选择信号按位复制，降低单一网络的扇出。
3. 用 RTL 写出前缀进位（Kogge-Stone/Brent-Kung）替代 ripple CPA。

这些改动有可能削减第②–④段的时间（约 16.4 ns 中的一部分），但需要节省超过 4.19 ns 并留出裕量。而且综合配方固定、没有时序目标，ABC 是否保留手写结构、是否会给高扇出网络补缓冲，都不确定。因此只建议作为方案 A/B 的补充，或者在面积不够加寄存器时尝试，必须用重新综合和 STA 验证。
