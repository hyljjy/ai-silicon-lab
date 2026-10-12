## 一、报告事实

> 说明：原题材料用“文件名:行号”引用；本轮新增的查询结果没有行号，以下用“查询 Bn 输出”定位。

### 1. 已确认的基线结构和约束

- 基线在同一个时钟周期内完成四个有符号 16×16 乘法、34 位精确求和以及 32 位饱和选择，只寄存输出，L=1（`dot4sat.v:23-40`，`context.md:18`）。
- `out_valid` 受同步高有效复位控制；`out_data` 无复位、无使能（`dot4sat.v:37-41`）。
- 时钟周期固定为 27.91 ns，而且这个周期是按“基线最差 setup slack 约为周期的 −15%”校准出来的（`values.txt:1`，`context.md:28`）。因此当前违例不是偶然约束错误，而是该基线在既定校准条件下预期处于违例状态。
- 输入 max delay 为 0.2T，即 5.582 ns；输入 min delay 为 0（`case01_sdc.tcl:13-14`，`path_report.rpt:11`）。
- 分析使用理想时钟、不读寄生参数，连线负载只计引脚电容（`context.md:20`）。

### 2. 最差 setup 路径及时间预算

- 最差路径为 `in_b[2] → _12026_/D`，corner 为 `ss_n40C_1v60`（`path_report.rpt:1-5`）。
- 数据到达时间为 31.5439 ns，要求时间为 27.3541 ns，slack 为 −4.1897 ns（`path_report.rpt:87-100`）。
- 从输入外部延迟之后到触发器 D 的内部路径耗时为：

  `31.5439 − 5.5820 = 25.9619 ns`。

- 扣除输入外部延迟后，该路径可用时间为：

  `27.3541 − 5.5820 = 21.7721 ns`。

  两者差值正好约为当前违例量 4.1898 ns。

### 3. 第 1 轮中的若干判断已被查询确认

- **`_12026_` 的身份已确认。**  
  查询 B7 的 `report_instance` 输出显示：
  - `_12026_` 是 `sky130_fd_sc_hd__dfxtp_1`；
  - 其 Q 输出直接连接到 `out_data[0]`；
  - D 输入连接到内部网络 `_00030_`。  
  因此第 1 轮“`_12026_` 很可能是 `out_data[0]` 触发器”的判断现在可以改为确认事实。

- **基线确实不存在 reg2reg 路径。**  
  查询 B4 在全部 6 个 corner 下均返回 `No paths found.`，与原始拓扑摘要中的 reg2reg 数目为 0 一致（`slack_summary.tsv:9`）。

- **reg2out 不是当前瓶颈。**  
  查询 B4 和 B9 显示，在 `ss_n40C_1v60` 下，`_12026_/CLK → out_data[0]` 的到达时间约为 0.6356 ns，reg2out slack 为 21.6924 ns。原摘要也给出 21.692432 ns 的正 slack（`slack_summary.tsv:41-42`）。

### 4. 各 corner 的 in2reg 最差 setup 结果

查询 B4 给出的紧凑结果与原摘要一致：

| Corner | Actual | Required | Slack |
|---|---:|---:|---:|
| `tt_025C_1v80` | 16.522688 | 27.708145 | +11.185458 |
| `tt_100C_1v80` | 16.404186 | 27.721409 | +11.317222 |
| `ss_100C_1v60` | 28.161348 | 27.474070 | −0.687278 |
| `ss_n40C_1v60` | 31.543875 | 27.354149 | −4.189726 |
| `ff_n40C_1v95` | 11.924675 | 27.796181 | +15.871506 |
| `ff_100C_1v95` | 11.910374 | 27.804602 | +15.894229 |

因此，“只有两个低电压 slow corner 违例”得到确认（另见 `slack_summary.tsv:27-42`）。

但第 1 轮中隐含的“延迟应随 PVT 严格单调变化”判断需要修正：`tt_100C_1v80` 的 actual delay 为 16.404186 ns，反而小于 `tt_025C_1v80` 的 16.522688 ns。可以确认的是**低电压 slow corner 最关键**，不能声称所有相邻 PVT 点之间都单调变化。

### 5. 输入延迟贡献已被对照查询精确确认

查询 B10 在单独会话中把输入 max delay 临时改为 0。结果显示：

- 同一条 `in_b[2] → _12026_/D` 路径的内部逐级延迟不变；
- data arrival time 从 31.5439 ns 变为 25.9619 ns；
- slack 从 −4.1897 ns 变为 **+1.3923 ns**。

变化量正好等于 5.5820 ns 的输入 max delay。因此第 1 轮的“0.2T 输入延迟与 L=1 结构叠加”判断得到确认。

同时也要修正其表述：0.2T 输入延迟不是唯一问题。即使输入外部延迟为 0，整条组合逻辑仍消耗 25.9619 ns，只留下 1.3923 ns 余量，约占可用窗口的 94.9%。

### 6. `_11509_/Y` 是共同结构热点，但其 RTL 功能仍不确定

- `_11509_/Y` 的扇出为 31，单元延迟为 2.6362 ns，输出 slew 为 3.2455 ns；下一级 `_11512_` 又贡献 0.8625 ns（`path_report.rpt:84-86`）。
- 查询 B8 确认 `_11509_` 是 `sky130_fd_sc_hd__o21ai_0`，输出网络名为 `_05587_`，但只给出了网络名，没有给出 RTL 功能归属。
- 查询 B2 可见的最差路径和输出末尾的近最差路径都经过 `_11509_/Y`；两条不同起点的路径还在 `_11302_/X` 后汇合成相同的后缀。
- 查询 B6 加了 `-through _11509_/Y` 后，仍返回与 B2 同量级、同为 5103 行的报告，首尾示例也均经过该网络。

这支持“`_11509_/Y` 覆盖了最差路径集中的大量路径”的判断。不过由于输出被截断，不能精确声称全部 50 条路径都经过它；也不能仅凭 fanout=31 断定它就是饱和选择信号。

### 7. 高扇出热点不是唯一充分原因

在 `_11509_` 的 A1 输入处，数据已经在 28.0452 ns 到达（`path_report.rpt:83`），而 data required time 是 27.3541 ns。

因此，即使假设 `_11509_` 和 `_11512_` 两级延迟完全消失，仍然大约违例：

`28.0452 − 27.3541 = 0.6911 ns`。

所以局部缓冲、复制或饱和选择优化可能很重要，但不能只凭这两级就解释全部 −4.1897 ns 违例。

### 8. 面积证据仍缺失

- 第 1 轮提出的 `report_cell_usage` 和 `report_design_area` 在当前 OpenSTA 环境中都不是有效命令（查询 B12）。
- 因此基线面积、触发器数量之外的单元构成、候选方案是否小于 1.25 倍面积，仍全部不确定。

---

## 二、原因假设

### 假设 1：主要原因是 L=1 基线把完整算术链压在一个周期内——已基本确认

四个乘法器、加法树和饱和选择都位于输入端口与输出寄存器之间（`dot4sat.v:23-40`）。路径报告中大量 XOR/XNOR/MAJ 和复合门也与长算术链一致（`path_report.rpt:13-86`）。

查询 B10 进一步确认：即使把输入外部延迟清零，内部路径仍需 25.9619 ns，距离 27.3541 ns 的要求时间只剩 1.3923 ns。

**仍可推翻的方式：**

- 若完整网表映射证明这条 XOR/MAJ 长链不属于乘法、求和或饱和，而属于其他意外逻辑，则该判断被推翻。
- 若候选 RTL 只做自然流水、但综合后长链并未被切断，也说明第 1 轮对结构边界的理解不正确。

### 假设 2：0.2T 输入延迟是造成违例的直接预算因素，但不是唯一根因——已确认并修正

查询 B10 精确显示，输入 max delay 从 5.5820 ns 改为 0 后，slack 改善完全相同，从 −4.1897 ns 变为 +1.3923 ns。

因此：

- 输入寄存器、让算术链使用完整周期，是很有针对性的候选方案；
- 但原始组合链本身已经接近一个完整周期，插入寄存器后的 clock-to-Q 和重新映射仍可能吃掉这部分余量。

**推翻方式：**

- 如果输入寄存器候选网表中，新增寄存器 clock-to-Q、Q 端负载和重新映射合计吃掉超过约 1.39 ns，则“输入寄存即可可靠收敛”的工程判断被推翻。
- 如果新输入寄存器的 setup/hold 自身违例，也说明该方案不能直接接受。

### 假设 3：`_11509_/Y` 是共同高扇出热点——结构部分得到支持，功能归属仍不确定

- 最差和近最差返回路径均经过 `_11509_/Y`。
- 多条不同起点路径在 `_11302_/X` 后汇合，并共享后续 `_11509_` 后缀。
- fanout=31 和一个公共饱和选择信号驱动多个输出数据 mux 的结构相符，但查询 B8 没有证明这一点。

同时，该热点不是唯一根因：其输入端已经比要求时间晚约 0.6911 ns。

**推翻方式：**

- 若 `_11509_/Y` 的 31 个负载不是输出数据选择/mux，而是其他无关逻辑，则“饱和选择热点”判断被推翻。
- 若完整未截断的前 50 条违例路径中，只有少数经过 `_11509_/Y`，则“共同热点”判断被推翻。
- 若复制或寄存该网络后，重新综合的 slack 没有实质变化，也应推翻其作为主要热点的判断。

### 假设 4：低电压 slow corner 是关键场景——确认；严格 PVT 单调性——修正

确认部分：

- 只有 `ss_100C_1v60` 和 `ss_n40C_1v60` 违例；
- `ss_n40C_1v60` 最差。

修正部分：

- 不能声称延迟随温度或 PVT 严格单调变化，因为查询 B4 中 `tt_100C_1v80` 的 actual delay 小于 `tt_025C_1v80`。
- 更准确的表述是：当前设计的时序裕量主要由低电压 slow corner 决定。

### 假设 5：固定综合流程没有得到时序驱动的驱动强度或缓冲优化——仍不确定

支持点：

- 综合流程没有时钟目标、IO 目标或物理层面的时序修复（`context.md:24`）。
- 最差路径存在 fanout=31、驱动强度为 `_0` 的单元（`path_report.rpt:84`）。

反对或限制点：

- 即便完全消除 `_11509_` 和 `_11512_` 的延迟，仍约有 −0.691 ns 违例。
- 因此不能把全部问题归因于驱动不足或缺少缓冲；算术逻辑深度本身仍然是主要因素。

---

## 三、缺失的证据

1. **`_11509_` 的完整负载与功能归属**
   - 需要 `_11509_/Y` 的全部 31 个负载引脚。
   - 需要确认这些负载是否分别对应 31 个输出数据位的饱和 mux。
   - 查询 B8 只得到内部网络名 `_05587_`，没有功能映射。

2. **完整、未截断的违例路径分布**
   - 查询 B2/B6 返回了 5103 行，但本轮只显示首尾各 100 行。
   - 仍缺少精确的违例终点数、slack 直方图，以及经过 `_11302_/X`、`_11509_/Y` 的路径比例。

3. **自然算术边界的到达时间**
   - 需要知道四个乘积、`p0+p1`、`p2+p3`、最终 `sum`、饱和标志分别何时到达。
   - 没有这些数据，不能判断 L=2 的最佳切分点是输入寄存还是乘积寄存。

4. **门级实例到 RTL 的映射**
   - `_11302_` 后的公共后缀很可能属于求和/饱和，但尚未被证明。
   - `_11512_`、`_11574_`、`_12052_` 等实例和输出位的关系也只部分可见。

5. **新增输入寄存器的实际 clock-to-Q 和负载**
   - 查询 B9 只给出现有输出寄存器在输出负载条件下的 CLK→输出到达时间约 0.6356 ns。
   - 新增内部输入寄存器的 Q 端负载不同，不能直接把这个数当成确定值。

6. **基线和候选方案面积**
   - `report_cell_usage`、`report_design_area` 在当前环境不可用。
   - 需要改用综合侧面积报告或解析 Liberty/网表。

7. **候选流水结构的完整 setup/hold 结果**
   - 新方案会产生 reg2reg 路径。
   - 基线最低 hold slack 只有约 0.059 ns，新增输入寄存器后的 min-delay 路径必须单独验证。

8. **功能等价证据**
   - 所有流水方案都需要验证 `out_valid` 与新延迟严格对齐。
   - 算术重写需要证明乘积、34 位求和和正负饱和边界不变。

---

## 四、下一步查询

### 1. 用非弃用选项重新生成完整的违例终点摘要

```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -slack_max 0.0 \
  -sort_by_slack \
  -group_path_count 1000 \
  -endpoint_path_count 1000 \
  -unique_paths_to_endpoint \
  -format end \
  -digits 6
```

目的：用紧凑格式得到完整的违例终点列表，避免 full 报告再次被截断。

### 2. 得到经过 `_11509_/Y` 的违例终点摘要

```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -through [get_pins {_11509_/Y}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -slack_max 0.0 \
  -sort_by_slack \
  -group_path_count 1000 \
  -endpoint_path_count 1000 \
  -unique_paths_to_endpoint \
  -format end \
  -digits 6
```

与查询 1 的完整端点列表比较，可精确计算共同热点覆盖率。

### 3. 检查 `_11302_/X` 是否也是公共汇合点

```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -through [get_pins {_11302_/X}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -slack_max 0.0 \
  -sort_by_slack \
  -group_path_count 1000 \
  -endpoint_path_count 1000 \
  -unique_paths_to_endpoint \
  -format end \
  -digits 6
```

目的：确认共同瓶颈是否从 `_11302_` 已经开始，而不是仅发生在 `_11509_`。

### 4. 修正后的 `_11509_/Y` 网络和负载查询

第 1 轮中 `report_pin` 和 `report_net -connections` 不可用，应改为：

```tcl
report_instance [get_cells {_11509_}]

set net_11509_y [get_nets -of_objects [get_pins {_11509_/Y}]]
report_net -verbose $net_11509_y

foreach p [get_pins -of_objects $net_11509_y] {
    puts [get_full_name $p]
}
```

目的：列出驱动和全部负载，确认 fanout=31 的准确归属。

### 5. 查看 `_11509_/Y` 的逻辑扇出终点和扇入起点

```tcl
foreach p [all_fanout -from [get_pins {_11509_/Y}] -endpoints_only] {
    puts [get_full_name $p]
}

foreach p [all_fanin -to [get_pins {_11509_/Y}] -startpoints_only] {
    puts [get_full_name $p]
}
```

目的：

- 扇出是否主要终止于 32 个 `out_data` 寄存器；
- 扇入是否覆盖四路输入乘积或饱和比较所需的数据位。

### 6. 用紧凑格式重新查询同一条路径的全部 corner

```tcl
foreach scene [list \
    tt_025C_1v80 \
    tt_100C_1v80 \
    ss_100C_1v60 \
    ss_n40C_1v60 \
    ff_n40C_1v95 \
    ff_100C_1v95] {

    puts "===== $scene ====="
    report_checks \
      -from [get_ports {in_b[2]}] \
      -to [get_pins {_12026_/D}] \
      -path_delay max \
      -scene $scene \
      -format end \
      -digits 6
}
```

目的：避免 full 报告截断，取得同一起终点的完整六 corner 数值。

### 7. 确认其他关键实例的归属

```tcl
report_instance [get_cells {_11512_}]
report_instance [get_cells {_11574_}]
report_instance [get_cells {_12052_}]
```

如果查询 1 得到其他违例终点，也应对其执行：

```tcl
report_instance [get_cells {<endpoint_cell_name>}]
```

### 8. 面积查询

当前 OpenSTA 中没有可用的面积命令，因此只能在 OpenSTA 中先取得单元数量：

```tcl
puts "cell_count = [llength [get_cells *]]"
```

面积必须改用综合侧报告。例如用与综合网表匹配的 Liberty 执行 Yosys 面积统计：

```tcl
yosys -p \
  "read_verilog <mapped_netlist.v>; \
   hierarchy -check -top dot4sat; \
   stat -liberty <sky130_hd_library.lib>"
```

需要分别对基线和每个候选网表执行，并比较是否不超过 1.25 倍。

### 9. 候选网表的完整 setup/hold 回归

对每个候选网表，在原 T、原输入/输出约束和原负载下执行：

```tcl
foreach scene [list \
    tt_025C_1v80 \
    tt_100C_1v80 \
    ss_100C_1v60 \
    ss_n40C_1v60 \
    ff_n40C_1v95 \
    ff_100C_1v95] {

    puts "===== $scene setup ====="
    report_checks \
      -path_delay max \
      -scene $scene \
      -sort_by_slack \
      -group_path_count 50 \
      -endpoint_path_count 50 \
      -format end \
      -digits 6

    puts "===== $scene hold ====="
    report_checks \
      -path_delay min \
      -scene $scene \
      -sort_by_slack \
      -group_path_count 50 \
      -endpoint_path_count 50 \
      -format end \
      -digits 6
}
```

对流水候选还应单独列出三类路径：

```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format end \
  -digits 6

report_checks \
  -from [all_registers -clock_pins] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format end \
  -digits 6

report_checks \
  -from [all_registers -clock_pins] \
  -to [all_outputs] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format end \
  -digits 6
```

---

## 五、可能的修改

### 方案 A：先做无额外延迟的算术优化，但不能期望局部热点优化必然足够

#### A1. 用高三位生成饱和标志

现有 RTL 使用两个 34 位数值比较（`dot4sat.v:31-35`）。可以改写为：

```verilog
wire pos_ovf = ~sum[33] & (|sum[32:31]);
wire neg_ovf =  sum[33] & ~(&sum[32:31]);

wire [31:0] sat = pos_ovf ? 32'h7FFF_FFFF :
                  neg_ovf ? 32'h8000_0000 :
                            sum[31:0];
```

这可能减少比较器和公共选择逻辑的复杂度。若 `_11509_` 最终被证明是饱和选择信号，此方案与热点直接相关。

但新结果表明，即使 `_11509_` 和 `_11512_` 两级延迟全部消失，仍约缺 0.691 ns。因此 A1 只有在同时明显缩短其前级比较/求和逻辑时，才可能单独关闭 4.19 ns 违例。

#### A2. 显式平衡加法树

```verilog
wire signed [32:0] p0e = {p0[31], p0};
wire signed [32:0] p1e = {p1[31], p1};
wire signed [32:0] p2e = {p2[31], p2};
wire signed [32:0] p3e = {p3[31], p3};

wire signed [32:0] s01 = p0e + p1e;
wire signed [32:0] s23 = p2e + p3e;

wire signed [33:0] s01e = {s01[32], s01};
wire signed [33:0] s23e = {s23[32], s23};
wire signed [33:0] sum  = s01e + s23e;
```

若当前综合结果已经把加法树平衡好，此方案收益可能很小；需要用重新综合结果验证。

### 方案 B：输入寄存器，L=2

这是当前证据最直接支持的流水方案：

```verilog
reg [63:0] a_q, b_q;
reg        v_q;

// sat_q 由 a_q、b_q 经乘法、求和、饱和组合逻辑得到

always @(posedge clk) begin
    a_q <= in_a;
    b_q <= in_b;

    if (rst) begin
        v_q       <= 1'b0;
        out_valid <= 1'b0;
    end else begin
        v_q       <= in_valid;
        out_valid <= v_q;
    end

    out_data <= sat_q;
end
```

特点：

- 第 n 个沿寄存输入；
- 第 n+1 个沿写入输出寄存器；
- L=2，仍能每周期接收一笔交易；
- 新增约 129 位寄存器：128 位数据加 1 位 valid 管道。

一阶估计：

- 输入外部延迟清零后的现有路径 slack 为 +1.3923 ns；
- 当前输出触发器在输出负载下的 CLK→Q/输出到达约 0.6356 ns；
- 现有输入端口自身延迟约 0.3091 ns。

如果其他逻辑不变，剩余余量的一阶估计约为：

`1.3923 − (0.6356 − 0.3091) ≈ 1.0658 ns`。

这只是估计，不是时序收敛证明；内部 Q 负载和重新映射结果仍不确定。

### 方案 C：乘积寄存器，L=2

```verilog
reg signed [31:0] p0_q, p1_q, p2_q, p3_q;
reg               v_q;

always @(posedge clk) begin
    p0_q <= p0;
    p1_q <= p1;
    p2_q <= p2;
    p3_q <= p3;

    if (rst) begin
        v_q       <= 1'b0;
        out_valid <= 1'b0;
    end else begin
        v_q       <= in_valid;
        out_valid <= v_q;
    end

    out_data <= sat_from_products_q;
end
```

优点：

- 在自然算术边界切断“乘法器 → 加法树 → 饱和”路径；
- 新增寄存器数量与方案 B 接近，约 129 位；
- 可能比“输入寄存后仍保留完整算术链”的方案 B 更均衡。

不确定性：

- 第一级只有 `27.3541 − 5.5820 = 21.7721 ns` 可用；
- 当前材料没有给出单个乘法器到乘积寄存器的到达时间，因此不能判断该级是否必然满足。

建议与方案 B 并行综合，而不是在缺少边界数据时预先选定。

### 方案 D：乘积寄存器 + 求和/溢出标志寄存器，L=3

如果两种 L=2 方案仍不能在所有 corner 收敛，使用允许的最大 L=3：

1. 第 n 个沿：寄存四个乘积；
2. 第 n+1 个沿：寄存 34 位 `sum` 及 `pos_ovf`、`neg_ovf`；
3. 第 n+2 个沿：只执行最终饱和选择并写入 `out_data`。

```verilog
reg signed [31:0] p0_q, p1_q, p2_q, p3_q;
reg signed [33:0] sum_q;
reg               pos_q, neg_q;
reg               v1_q, v2_q;

always @(posedge clk) begin
    p0_q <= p0;
    p1_q <= p1;
    p2_q <= p2;
    p3_q <= p3;

    sum_q <= sum_next;
    pos_q <= pos_next;
    neg_q <= neg_next;

    if (rst) begin
        v1_q      <= 1'b0;
        v2_q      <= 1'b0;
        out_valid <= 1'b0;
    end else begin
        v1_q      <= in_valid;
        v2_q      <= v1_q;
        out_valid <= v2_q;
    end

    out_data <= pos_q ? 32'h7FFF_FFFF :
                neg_q ? 32'h8000_0000 :
                        sum_q[31:0];
end
```

新增寄存器约：

- 128 位乘积；
- 34 位 `sum`；
- 2 位饱和标志；
- 2 位 valid 管道；

合计约 166 位。它能最大程度降低每级组合深度，并把疑似公共高扇出的饱和控制信号改为寄存器输出，但面积最大。

### 方案 E：条件性的高扇出复制或缓冲

只有在查询确认 `_11509_/Y` 确实是公共饱和选择信号后，才建议：

- 按输出字节或半字复制饱和选择信号；
- 建立结构化的平衡选择树；
- 或直接采用方案 D，将该标志寄存。

需要注意：即使完全消除 `_11509_` 和 `_11512_` 的 3.4987 ns，当前路径仍可能约有 −0.691 ns 违例，因此它更适合作为流水方案的补充，而不是唯一修复手段。

### 修正后的实施顺序

1. 先取得完整违例终点列表，并确认 `_11302_`、`_11509_` 的覆盖率及功能归属。
2. 尝试方案 A 的无延迟算术优化；若总改善不足 4.19 ns，则不继续依赖 L=1。
3. 并行综合方案 B 和方案 C：
   - 方案 B 有最直接的对照时序依据；
   - 方案 C 可能更均衡，但缺少乘积边界到达时间。
4. 若 L=2 候选在任一 corner 仍有 setup 违例，改用方案 D。
5. 最终方案必须重新验证：
   - 6 个 corner 的 setup 和 hold 全部非负；
   - L≤3；
   - 每周期接收一笔交易；
   - 接口、T 和 IO 约束不变；
   - 面积不超过基线的 1.25 倍；
   - `out_valid`、同步复位、精确求和和饱和行为全部等价。
