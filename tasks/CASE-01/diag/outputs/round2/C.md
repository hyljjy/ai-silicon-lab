## 一、报告事实

- 查询 C1 首先确认：本 OpenSTA 3.1.0 的 `report_checks` 不接受 `-nworst`，报错 `Error 514: '-nworst' is not a known keyword or flag`（查询 C1 输出）。第一轮想用 `-nworst` 枚举多条路径的查询不可用。
- 跨 corner 查询可见部分仍以 `ss_n40C_1v60` 下 `in_b[2] -> _12026_/D` 为最差路径，路径内容与 `path_report.rpt` 一致（查询 C1 输出；path_report.rpt:1-5、87-100）。
- 对照查询：`set_input_delay -clock clk -max 0` 后，同一条路径在 `ss_n40C_1v60` 下组合到达时间为 25.9619，要求时间仍为 27.3541，slack 为 1.3923 MET（查询 C1 输出尾部）。这说明原始到达时间 31.5439 ≈ 5.582 输入外部延迟 + 25.9619 组合延迟。
- 已知汇总：`ss_n40C_1v60` 最差 setup 为 -4.1897，`ss_100C_1v60` 为 -0.6873；tt/ff 角 setup 为正（slack_summary.tsv:11-29、35-36）。
- 原路径中高扇出点 `_11509_/Y`：fanout=31，cap=0.0511，slew=3.2455，delay=2.6362（path_report.rpt:83-85）。
- 查询 C1 的可见部分没有给出多条 `in2reg` 路径排序、`_11509_` 连接/驱动详情，也没有给出 `reg2out`、hold 的详细逐路径报告；这些被截断或因命令语法失败未获得（查询 C1 输出标记为“已截断”；`-nworst` 报错）。
- 题目说明对照查询是“改变冻结模型的查询”，“结果只作对照，不代表冻结模型”（查询 C1 元信息）。

## 二、原因假设

- **H1 需要修正：不能简单说“主因是单周期组合逻辑深度过长”。**  
  对照查询显示：去掉输入延迟后，组合段 25.9619 ns 小于数据要求时间 27.3541 ns，slack 为正 1.3923。因此组合深度很长，但单独并不违例；本路径违例是“组合延迟 + 固定输入 max 延迟 5.582”共同超过要求时间。原 H1 的说法被事实部分推翻或弱化。  
  - 可证伪：若另一条 in2reg 路径在去掉输入延迟后仍为负 slack，则说明某些路径的组合段本身超过一个周期，仍应保留“组合深度单独违例”的判断；但当前最差路径不是这种情况。

- **H2 被确认：固定输入延迟是违例的必要成分。**  
  同一路径仅把输入 max 延迟清 0，slack 从 -4.1897 变为 +1.3923。注意这不是合法修复，只是对照分析，但可确认输入延迟是重要组成部分。  
  - 可证伪：若清 0 后仍为负，则固定输入延迟不是必要成因；事实已推翻这一反证。

- **H3 被确认：最差 setup 在算术数据路径上，终点是 `_12026_/D`。**  
  可见最差路径仍为 `in_b[2] -> _12026_/D`，且 `_12026_` 是 `out_data[0]` 对应的输出寄存器；`slack_summary.tsv` 也显示最差 `in2reg` 起点为 `in_b[2]`。没有看到更差的控制路径。

- **H4 被确认并可以量化：高扇出点 `_11509_/Y` 是局部瓶颈，但单点修复不够。**  
  即使把 `_11509_/Y` 的 2.6362 ns 全部消除，组合段估算约为 25.9619 − 2.6362 = 23.3257 ns；再加输入延迟 5.582 = 28.9077 ns，仍大于要求时间 27.3541，slack 仍约 -1.55。因此它只是次级瓶颈，不能单独转正。

- **H5 维持成立：需要重点修复低速 ss 角。**  
  从汇总和跨角可见部分看，`ss_n40C_1v60` 与 `ss_100C_1v60` 违例，tt/ff 角有正裕量。

## 三、缺失的证据

- 缺少全部 130 条 `in2reg` setup 路径的完整排序，无法确认最差路径是否集中在 `out_data` 若干 bit，还是均匀分布；`-nworst` 不可用后仍需找到替代枚举方式。
- 缺少 `_11509_` 的完整连接/驱动报告（fanout 分布、各负载轨迹、可替换驱动单元）。
- 缺少乘法、求和、饱和三段的时延分割，尤其是从输入端口到乘积寄存器的可行分割点。
- 缺少 `reg2out`、hold 的详细逐路径报告；现有只有汇总，不能判断流水化后输出路径是否恶化。
- 缺少门级网表和综合后面积数据，无法确认 L=2/L=3 增加寄存器的面积是否不超过基线的 1.25 倍。
- 缺少 L=2/L=3 修改后重综合并全 corner STA 的结果。

## 四、下一步查询

第一轮的 `-nworst` 已证实不可用，因此需要先确认本版本可用的多路径枚举选项，再执行后续查询。

```tcl
# 0) 先确认本版本可用选项，不能再使用 -nworst
help report_checks
help find_timing_paths

# 1) 若 report_checks 支持 -slack_threshold，用它枚举 ss_n40C 下输入到寄存器 setup
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -slack_threshold 1.0

# 2) 跨全部 corner 同类最差（仅默认最差也需确认各角）
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scenes {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 3) 高扇出网络单独查询，避免与其他输出混在一起被截断
report_net -connections _11509_
report_driver -net _11509_

# 4) 已知最差路径单条确认
report_checks \
  -from in_b[2] \
  -to _12026_/D \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 5) reg2out 与 hold 详细报告
report_checks \
  -from [all_registers -clock_pins] \
  -to [all_outputs] \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay min \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 6) 确认冻结模型已恢复；若当前环境仍残留对照约束，则重新 source 原始 SDC
# source case01_sdc.tcl（保持 T=27.91、C_load=0.0024 不变）
```

## 五、可能的修改

- **首选仍为 L=2 流水化，新证据进一步支持其必要性。**  
  扣掉 `0.2T` 输入延迟后，输入到第一级寄存器的可用组合时间约为 `27.3541 - 5.582 = 21.7721 ns`；基线组合段 25.9619 ns 虽然单独不超期，但超过这个扣除输入延迟后的预算。因此不能仅靠门级优化轻松吸收，流水化是最直接的路线。  
  - 保持 L=2：在四个乘积 `p0..p3` 后插入一级乘积寄存器，第二拍完成 34 位求和与饱和并打入输出寄存器；`in_valid` 相应延迟一级以使 `out_valid` 对齐。  
  - 输入到乘积寄存器预计明显小于 21.77 ns；乘积寄存器到输出寄存器无输入延迟，可用约 27.35 ns。需综合后全角 STA 确认。

- **L=3 备选：** 若 L=2 后第一级乘法段仍接近或超过 21.77 ns，或将求和再拆一级更稳，则插入乘积寄存器和 34 位和寄存器，形成 L=3；`in_valid` 相应移位两级。仍满足 L ≤ 3，且每周期可接收新一笔交易。

- **门级微调只能作为流水化后的补充，不能替代流水化。**  
  对 `_11509_/Y` 高扇出点插入缓冲/复制驱动可降低局部 slew 和延时，但按现有路径推算，单点优化后仍为负 slack；因此不应把修复重点放在该点。

- **不可采用清输入延迟、增大周期或放宽输出约束作为正式修改。**  
  对照分析只用于理解成因，不能变成实现方案；正式修改必须保持 `case01_sdc.tcl` 中的约束和 `T=27.91` 不变。

- **验证要求：** 修改后必须在六角下重跑 `in2reg`、`reg2reg`、`reg2out` 的 setup/hold，并确认 L ≤ 3、每个时钟周期可接收新交易、接口与 IO 约束不变、面积不超过基线的 1.25 倍。目前面积数据缺失，不能无证据断言 L=2/L=3 一定满足面积限制，需重新综合后确认。
