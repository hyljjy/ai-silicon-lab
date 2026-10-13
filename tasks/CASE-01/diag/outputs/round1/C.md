## 一、报告事实

- 模块 `dot4sat` 是单时钟同步设计，`rst` 高有效同步复位；功能为 4 路 16 位有符号乘法求和后饱和到 32 位；基线实现只在输出端寄存，延迟 L=1（context.md:3-18；dot4sat.v:4-12、23-41）。
- 基线组合部分包含：4 个 16×16 有符号乘法、34 位和、饱和比较/选择；`out_valid` 受复位清零，`out_data` 不复位且无使能（dot4sat.v:23-41）。
- 拓扑上存在 130 条输入到寄存器路径，0 条寄存器到寄存器路径，33 条寄存器到输出路径（slack_summary.tsv:8-10）。
- 时钟为理想时钟；周期 `T = 27.91 ns`，`C_load = 0.0024 pF`（values.txt:1-2）。输入延迟 max 为 `0.2T = 5.582 ns`、min 为 0；输出延迟 max 为 `0.2T`、min 为 0（case01_sdc.tcl:4-18）。
- 六个 PVT 角；`ss_n40C_1v60` 的 setup 最差 slack 为 -4.189726，约占 T 的 -15.0%；`ss_100C_1v60` 也违例，为 -0.687278；tt 与 ff 角 setup 为正（slack_summary.tsv:11-29、35-36；context.md:28）。
- `path_report.rpt` 展示了 `ss_n40C_1v60` 下输入到寄存器 setup 最差路径：起点 `in_b[2]`，终点 `_12026_/D`（path_report.rpt:1-5）。
- 该路径数据到达时间为 31.5439，数据要求时间为 27.3541，slack 为 -4.1897（path_report.rpt:87-100）。其中输入外部延迟 5.5820，库 setup time 为 0.5559（path_report.rpt:11、94）。
- `_12026_` 是与 `out_data[0]` 对应的输出寄存器，因为有 `reg2out` 项显示 `_12026_/Q -> out_data[0]`（slack_summary.tsv:17）。
- 路径中大量出现 `xnor/xor/maj/a21oi/o21ai` 等单元；其中 `_11509_/Y` 扇出为 31、电容 0.0511、slew 3.2455、延时 2.6362，是相当明显的局部高扇出点（path_report.rpt:83-85）。
- hold（min）在所有角均为正值，未显示 hold 违例（slack_summary.tsv:11-58 中 min 栏）。

## 二、原因假设

- **H1：主因是单周期组合逻辑深度过长。** 基线 L=1 把乘法、求和、饱和全部压在输入端口到输出寄存器的一级组合路径中；该路径从 `in_b[2]` 到 `_12026_/D` 有很长的单元级串联，组合段约 25.65 ns（到 D 的 31.5439 减去 5.582 输入延迟；另从端口时间 5.8911 到 D 约 25.65 ns）。  
  - 可证伪：若重新综合为插入中间寄存器的流水结构后，`ss_n40C_1v60` 下输入到寄存器 setup 仍不改善，或完整路径报告显示总延时主要来自少数高扇出/异常 slew 单点而非逐级累加，则本假设被削弱或推翻。

- **H2：固定输入延迟是“触发”本次违例的必要外部成分，但它是约束的一部分，不能通过放宽来修复。** 数据到达 31.5439 = 5.582 输入外部延迟 + 25.9619 组合段；数据要求 27.3541。若只做对照分析、临时把输入 max delay 清为 0，到达时间约 25.96，会小于要求时间 27.354，slack 转正。  
  - 可证伪：若在仅作对照的运行中把 `set_input_delay -max 0` 后，`ss_n40C_1v60` 仍为负 slack，则说明组合逻辑本身单独已经超期，输入延迟不是必要成因。

- **H3：违例在算术数据路径上，表现为 `in_b[2]` 到 `out_data[0]`。** 该路径经过大量全加器/选择类单元，并且终点是 `out_data[0]` 的寄存器。  
  - 可证伪：若报告所有输入到所有寄存器的完整 setup 路径后，发现更差路径来自 `rst`、`in_valid` 等控制路径，或最差终点不是 `_12026_/D`，而是其他控制/数据寄存器，则本假设被推翻。

- **H4：高扇出网络 `_11509_/Y` 对末端延时贡献较大，但很可能只是局部瓶颈而非唯一原因。** 该点在路径末端贡献 2.6362 ns，且 slew 达 3.2455。  
  - 可证伪：若用缓冲/复制驱动降低该点扇出和 slew 后，整条路径 slack 转正，则它是关键瓶颈；若 slack 改善很小、仍为负，说明它并非主因，主因仍在更长的组合深度。

- **H5：需要重点修复的是低速角 `ss_n40C_1v60`（以及次级 `ss_100C_1v60`），tt/ff 角不是主要问题。**  
  - 可证伪：若跨角报告显示 tt/ff 角也出现接近或超过 0 的输入 setup 违例，则“只需针对 ss 角修复”的判断不成立。

## 三、缺失的证据

- 门级网表本体没有被提供（context.md:25），无法确认 `_12026_`、`_11509_` 等内部节点与 RTL 位的精确映射，也无法定位乘法、求和、饱和各段的逻辑边界。
- 缺少全部 corner、全部 130 条 `in2reg` setup 路径的报告；目前只有 `ss_n40C_1v60` 下最差一条 `in_b[2] -> _12026_/D`。
- 缺少各段时延占比：需要知道乘法、34 位求和、饱和选择分别消耗多少，才能判断在哪一级插流水最有效。
- 缺少 `reg2out` 和 hold 的逐路径详细报告；目前只有汇总 slack。
- 缺少基线与修改后网表的面积数据，无法定量判断修改是否满足面积不超过基线 1.25 倍。
- 若考虑门级结构修改，还需要 `_11509_/Y` 的完整扇出/负载列表，以及所用 Sky130 HD 库中可利用的缓冲/驱动单元及其面积。

## 四、下一步查询

以下均按 OpenSTA 3.1.0 的 `-scenes`/`-scene` 用法给出：

```tcl
# 1) ss_n40C 下输入到寄存器 setup，列出前 20 条，而不只看缺省最差一条
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 20

# 2) 跨全部 corner 看同类最差路径
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scenes {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 3) 只看终点 _12026_/D 的所有输入起点，判断是否为 _12026_ 集中收敛
report_checks \
  -from [all_inputs -no_clocks] \
  -to _12026_/D \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 50

# 4) 已知最差路径的完整单条报告
report_checks \
  -from in_b[2] \
  -to _12026_/D \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 5) 经过高扇出点 _11509_/Y 的路径，以及该网络连接/驱动信息
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -through _11509_/Y \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 10

report_net -connections _11509_
report_driver -net _11509_

# 6) 确认 reg2reg、reg2out 与 hold 情况
report_checks \
  -from [all_registers -clock_pins] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

report_checks \
  -from [all_registers -clock_pins] \
  -to [all_outputs] \
  -path_delay max \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 10

report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay min \
  -scenes ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4 \
  -nworst 10

# 7) 仅作对照：临时把输入 max 延迟清 0，验证 H2；之后必须恢复原始 SDC
set_input_delay -clock clk -max 0 [get_ports {in_a[*] in_b[*] in_valid rst}]
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -fields {slew cap input_pins fanout} \
  -digits 4

# 然后恢复原始约束：重新 source case01_sdc.tcl（保持 T、C_load 等不变）
```

若 OpenSTA 版本不支持 `-nworst`，可改用 `-nworst` 之外的等价选项，或分多次降低 `-slack_threshold` 来枚举多条路径；这一条属于工具选项差异，需在环境里确认。

## 五、可能的修改

- **首选：L=2 流水化，插入乘积寄存器。** 在四个 32 位乘积 `p0/p1/p2/p3` 之后插入流水寄存器，第二拍再计算 34 位和、饱和并打入现有输出寄存器；同时给 `in_valid` 增加 1 级延迟寄存，使 `out_valid` 与数据对齐。  
  - 延迟 L=2，满足 L ≤ 3；各寄存器每拍都无条件推进，因此每个时钟周期都能接收新交易，不改变接口和 IO 约束，也不改变 T。  
  - 预计新增面积主要是 128 个乘积寄存位 + 1 个 valid 寄存位；是否在 1.25 倍面积内需用综合后面积数据确认。  
  - 这一级把乘法与“求和+饱和”拆开。若乘法本身仍过大，则改用 L=3。

- **备选：L=3 流水化，再插入和寄存器。** 依次为：乘积寄存（`p0_r`…`p3_r`）→ 34 位和寄存（`sum_r`）→ 饱和并输出寄存。将乘法、求和、饱和分到三级组合段。  
  - L=3，刚好不超过限制；吞吐仍为每周期一笔记交易；`in_valid` 用两级移位寄存器对齐。  
  - 面积增加更多：128 个乘积位 + 34 个和位 + 额外的 valid 移位位；必须在综合后检查不超过基线 1.25 倍。

- **简要 RTL 示意（L=2）：**
  ```verilog
  reg signed [31:0] p0_r, p1_r, p2_r, p3_r;
  reg valid_r;

  always @(posedge clk) begin
    if (rst) begin
      valid_r   <= 1'b0;
      out_valid <= 1'b0;
    end else begin
      valid_r   <= in_valid;
      out_valid <= valid_r;   // L=2 的 valid 对齐
    end
    p0_r <= p0;
    p1_r <= p1;
    p2_r <= p2;
    p3_r <= p3;
  end

  wire signed [33:0] sum_p = p0_r + p1_r + p2_r + p3_r; // 注意 34 位有符号扩展语义
  wire [31:0] sat_p = (sum_p > SMAX) ? 32'h7FFF_FFFF :
                      (sum_p < SMIN) ? 32'h8000_0000 : sum_p[31:0];

  always @(posedge clk)
    out_data <= sat_p; // 使用旧的 p*_r，形成 L=2
  ```
  L=3 则在此基础上再插入一级 `sum_r <= p0_r + p1_r + p2_r + p3_r`，输出为 `out_data <= sat(sum_r)`，并让 valid 移位两级。

- **门级结构微调（不改变 RTL 功能与接口）：** 对 `_11509_/Y` 这类 fanout=31、slew=3.2455 的高扇出网络插入缓冲或复制驱动，降低末端 slew 和局部延时。  
  - 这可以改善局部瓶颈，但根据当前路径数据，仅去掉该段的 2.6362 ns 后组合时间仍可能接近或超过要求，单靠它未必能把 `ss_n40C_1v60` 转正；需用查询 5 和综合后报告确认。

- **验证要求：** 任何修改都必须用同一约束集合、同一 T 和 SDC 在全部六个 PVT 角重跑 `in2reg` setup、`reg2out`、hold 检查；同时确认 L ≤ 3、每周期可接收新交易、面积不超过基线 1.25 倍。面积当前没有数据，不能在此武断判断 L=2 或 L=3 是否超限，需要在取得综合面积后确认。
