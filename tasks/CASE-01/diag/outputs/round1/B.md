## 一、报告事实

1. **功能与基线结构**
   - DUT 计算 4 个有符号 16×16 乘积，将它们作为 34 位有符号数精确求和，再饱和到 32 位有符号输出（`dot4sat.v:23-35`）。
   - 基线只有输出寄存器：`out_valid` 由同步高有效 `rst` 清零，`out_data` 每个时钟无条件更新（`dot4sat.v:37-41`）。基线延迟为 L=1（`context.md:18`）。
   - 因此一次输入采样后，乘法、四输入求和和饱和选择都必须在同一个时钟周期内完成。

2. **分析条件与约束**
   - 时钟周期为 **27.91 ns**，输出负载为 **0.0024 pF**（`values.txt:1-2`）。
   - 使用理想时钟，不读寄生参数，连线负载只计引脚电容（`context.md:20`）。
   - 数据和控制输入由 `sky130_fd_sc_hd__buf_2` 驱动，输入 transition 为 0；输入 max delay 为 0.2T，min delay 为 0（`context.md:22`、`case01_sdc.tcl:13-16`）。
   - 输出 max delay 为 0.2T，min delay 为 0，负载为 `C_load`（`context.md:23`、`case01_sdc.tcl:17-19`）。
   - 27.91 ns 周期是按“基线最差 setup slack 约为周期的 −15%”校准的固定值，修改时不能改变（`context.md:28`）。

3. **给出的最差 setup 路径**
   - 起点是 `in_b[2]`，终点是触发器 `_12026_` 的 D 引脚，corner 为 `ss_n40C_1v60`（`path_report.rpt:1-5`）。
   - 输入外部延迟为 5.5820 ns，正好等于 0.2×27.91 ns；输入端口自身在 5.8911 ns 到达（`path_report.rpt:11-12`）。
   - 数据最终在 31.5439 ns 到达 `_12026_/D`（`path_report.rpt:87-88`）。
   - 捕获沿在 27.9100 ns，库 setup 时间为 0.5559 ns，因此 data required time 为 27.3541 ns（`path_report.rpt:90-95`）。
   - slack 为 **−4.1897 ns**，setup 违例（`path_report.rpt:97-100`）。这约为周期的 **−15.01%**，与周期校准说明一致（`context.md:28`）。

4. **路径预算**
   - 相对于输入外部延迟的起点，路径内部耗时为：
     `31.5439 − 5.5820 = 25.9619 ns`。
   - 在扣除 0.2T 输入延迟和触发器 setup 后，可用于该路径的时间为：
     `27.3541 − 5.5820 = 21.7721 ns`。
   - 若从输入端口实际到达时间算起，端口之后逻辑耗时为：
     `31.5439 − 5.8911 = 25.6528 ns`（依据 `path_report.rpt:12` 和 `path_report.rpt:87-88`）。

5. **路径中的显著高扇出点**
   - `_11509_/Y` 的扇出为 **31**，引脚电容为 0.0511 pF，输出 slew 为 3.2455 ns，单元延迟为 2.6362 ns（`path_report.rpt:84`）。
   - 下一级 `_11512_` 在该大 slew 输入下又产生 0.8625 ns 延迟（`path_report.rpt:85-86`）。
   - 这两级合计约 3.4987 ns，占端口后 25.6528 ns 内部延迟的约 13.6%。但材料没有说明 `_11509_` 对应 RTL 中哪个信号。

6. **跨 corner 结果**
   - 最差 setup slack 只在两个 slow corner 为负：
     - `ss_100C_1v60`：−0.687278 ns；
     - `ss_n40C_1v60`：−4.189726 ns。
     其余四个 corner 均为正（`slack_summary.tsv:11-56`）。
   - 全部 corner 的最差 hold slack 均为正；最低值是 `ff_100C_1v95` 的 0.059113 ns（`slack_summary.tsv:51-54`）。
   - `ss_n40C_1v60` 下 reg2out setup slack 为 21.692432 ns，远大于输入到寄存器路径的负 slack，因此输出延迟约束不是当前主要问题（`slack_summary.tsv:41-42`）。

7. **拓扑信息**
   - in2reg 起点数为 130，正好对应 64+64 个数据输入位，再加 `in_valid` 和 `rst`（`context.md:7-12`、`slack_summary.tsv:8`）。
   - reg2reg 路径数为 0，reg2out 起点数为 33（`slack_summary.tsv:9-10`），与“只有 32 位 `out_data` 和 1 位 `out_valid` 输出寄存器、没有内部流水线寄存器”一致。
   - `_12026_/Q` 在所有 corner 的 reg2out 最差路径中都连接到 `out_data[0]`，因此 `_12026_` 很可能是 `out_data[0]` 的触发器（例如 `slack_summary.tsv:17`、`slack_summary.tsv:41`）。但由于没有提供网表和实例映射，这一点还不能视为完全确认（`context.md:25`）。

8. **报告覆盖范围的限制**
   - `path_report.rpt` 是默认设置的 `report_checks` 输出，只报告了该类别中 slack 最差的一条路径（`context.md:26-27`）。因此不能从这份报告推断第二差路径、违例终点数量或整体路径分布。
   - OpenSTA 3.1.0 中 `report_checks` 和 `find_timing_paths` 可用 `-scene` 选择场景，但 `report_wns`、`report_tns`、`report_worst_slack` 不能选择场景（`context.md:19`）。

---

## 二、原因假设

### 假设 1：根本原因是 L=1 将乘法、求和和饱和全部放在同一级组合逻辑中

- 四个 16×16 乘法器、34 位加法树和饱和比较/选择在采样输入的同一个沿写入输出寄存器（`dot4sat.v:23-40`）。
- 观察到的路径包含大量 XOR/XNOR/MAJ 和复合门，呈现长算术链特征（`path_report.rpt:13-86`）。
- 端口后逻辑耗时 25.6528 ns，而扣除输入延迟后的可用窗口只有 21.7721 ns。

**可推翻方式：**

- 若网表映射显示 `_12026_` 不是输出数据触发器，且该长链并不属于乘法/求和/饱和逻辑，则此假设被推翻。
- 若对自然算术边界——乘积、部分和、总和、饱和标志——的到达时间查询表明绝大部分延迟来自无关控制或复位逻辑，也应推翻此假设。

### 假设 2：0.2T 输入延迟与 L=1 结构叠加，是造成违例的重要预算因素

- 输入 max delay 为 5.5820 ns（`path_report.rpt:11`），而整条路径只超出 4.1897 ns。
- 在只作对照、不改变设计约束的前提下，把该路径的输入 max delay 临时设为 0，若其他延迟不变，其 slack 应约变为：
  `−4.1897 + 5.5820 = +1.3923 ns`。
- 这说明把数据输入先寄存、让长算术逻辑使用完整时钟周期，是时间上很有针对性的候选方案。

**可推翻方式：**

- 在对照分析中把输入 max delay 改为 0 后，如果同一条路径的 slack 没有按约 5.582 ns 改善，说明上述预算解释不成立。
- 如果插入输入寄存器后的实际网表中，时钟到 Q、扇出变化和重新映射使关键级仍明显违例，则“仅寄存输入即可解决”的工程判断被推翻。

### 假设 3：饱和选择或某个公共选择信号的高扇出是局部热点

- `_11509_/Y` 扇出 31、slew 3.2455 ns、延迟 2.6362 ns，下一级又产生 0.8625 ns 延迟（`path_report.rpt:84-86`）。
- 扇出 31 与“一个饱和选择信号驱动多个输出数据位”的结构相符，但材料没有提供实例到 RTL 的映射，所以目前只能认为有可能。

**可推翻方式：**

- 若 `_11509_/Y` 的负载清单显示它不是输出数据 mux/饱和选择网络，而是与最终数据无关的逻辑，则此假设被推翻。
- 若前几十条最差 setup 路径大多不经过 `_11509_/Y`，且仍存在类似幅度的违例，则说明它不是共同主要热点。
- 若将该网络对应的饱和标志寄存或复制后，重新综合的时序没有改善，也应推翻其作为主要热点的判断。

### 假设 4：违例主要在 slow corner 显现，设计本身处于临界状态

- `ss_100C_1v60` 仅违例 0.687278 ns，`ss_n40C_1v60` 违例扩大到 4.189726 ns，其他 corner 均有较大正 slack（`slack_summary.tsv:27-42`）。
- 这更像是长组合路径在慢工艺、低电压下被放大，而不是所有 corner 下都存在约束配置错误。

**可推翻方式：**

- 若同一条 `in_b[2] → _12026_/D` 路径在各 corner 的延迟排序不随 PVT 单调变化，或 slack 差异主要来自 setup/约束异常，则该假设被推翻。
- 若其他 corner 也存在大量未在摘要中体现的不同违例路径，则“主要是 slow corner 放大”的描述需要修正。

### 假设 5：固定综合流程没有得到足够浅或足够强驱动的算术映射

- 综合配方固定，没有时钟目标、IO 目标或物理层面的时序修复（`context.md:24`）。
- 最差路径中大量单元是 `_1` 驱动强度，并出现一个扇出 31 的网络（`path_report.rpt:13-86`）。

**可推翻方式：**

- 若关键链已经使用库中合适的高驱动单元，且进一步驱动强度提升只能带来很小收益，则“驱动不足”部分被推翻。
- 若显式平衡加法树、简化饱和逻辑或流水化后的重新综合仍产生几乎相同的关键路径，则说明主要问题不是当前映射，而是所要求的功能在该周期约束下本身过深。

---

## 三、缺失的证据

1. **完整门级网表及 RTL 信号映射**
   - 需要确认 `_12026_` 是否确为 `out_data[0]` 触发器。
   - 需要确认 `_11509_`、`_11512_` 等实例分别对应乘积、加法树、饱和比较还是输出 mux。
   - 当前材料明确说明网表存在但未提供（`context.md:25`）。

2. **完整路径分布**
   - 需要前几十条 in2reg setup 路径，而不只是默认最差一条。
   - 需要知道有多少终点违例、是否所有 `out_data` 位都经过同一个高扇出选择信号、第二差路径与最差路径相差多少。

3. **自然算术边界的到达时间**
   - 需要每个 `p0`～`p3`、部分和、最终 `sum`、饱和标志和输出 mux 输入的到达时间。
   - 没有这些信息，无法判断最佳流水边界是在输入、乘积、部分和还是饱和标志处。

4. **高扇出网络的完整信息**
   - 需要 `_11509_/Y` 的驱动、全部负载引脚、负载分布和功能归属。
   - 只凭 fanout=31 不能确定它就是饱和选择信号。

5. **触发器时钟到 Q 延迟和插入寄存器后的路径数据**
   - 输入寄存方案能否成立，取决于新增输入触发器在 `ss_n40C_1v60` 下的时钟到 Q 延迟以及重新综合后的实际映射。
   - 当前报告没有给出 `_12026_/CLK → _12026_/Q` 的详细延迟。

6. **基线面积**
   - 材料没有给出基线单元面积或等效门数，因此无法证明任何新增寄存器方案满足“面积不超过基线 1.25 倍”（`context.md:29`）。

7. **修改后的完整多 corner setup/hold 结果**
   - 插入寄存器后会出现 reg2reg 路径，必须重新检查所有 6 个 corner 的 setup 和 hold。
   - 基线最低 hold slack 只有 0.059113 ns，修改后不能只看 setup。

8. **算术改写的等价性证明**
   - 对饱和比较和加法树进行重写后，需要形式等价或充分仿真证明：
     - 四路乘积完全精确；
     - 34 位求和无截断；
     - 正负饱和边界与 RTL 原表达式一致；
     - `out_valid` 延迟和同步复位行为正确。

---

## 四、下一步查询

以下命令假设已经完成读库、读网表、`link_design`、建立 6 个 scene，并已按正确顺序加载 `case01_sdc.tcl`。

### 1. 查看 `ss_n40C_1v60` 下前 50 条违例 in2reg 路径

```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -slack_max 0.0 \
  -sort_by_slack \
  -group_count 50 \
  -endpoint_count 50 \
  -unique_paths_to_endpoint \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```

目的：确认违例路径数量、终点分布，以及 `_11509_/Y` 是否为共同热点。

### 2. 在所有 corner 下报告同一条起终点路径

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
    -format full_clock_expanded \
    -fields {slew cap input_pins fanout} \
    -digits 4
}
```

目的：验证同一路径的 PVT 敏感性，而不是只比较各 corner 可能不同的最差路径。

### 3. 分 corner 查看 in2reg、reg2reg、reg2out 最差路径

```tcl
foreach scene [list \
    tt_025C_1v80 \
    tt_100C_1v80 \
    ss_100C_1v60 \
    ss_n40C_1v60 \
    ff_n40C_1v95 \
    ff_100C_1v95] {

  puts "===== $scene in2reg ====="
  report_checks \
    -from [all_inputs -no_clocks] \
    -to [all_registers -data_pins] \
    -path_delay max \
    -scene $scene \
    -format end \
    -digits 6

  puts "===== $scene reg2reg ====="
  report_checks \
    -from [all_registers -clock_pins] \
    -to [all_registers -data_pins] \
    -path_delay max \
    -scene $scene \
    -format end \
    -digits 6

  puts "===== $scene reg2out ====="
  report_checks \
    -from [all_registers -clock_pins] \
    -to [all_outputs] \
    -path_delay max \
    -scene $scene \
    -format end \
    -digits 6
}
```

目的：不用 `report_worst_slack`，从而避开它不能选择 scene 的限制。

### 4. 统计最差路径是否经过高扇出网络

```tcl
report_checks \
  -from [all_inputs -no_clocks] \
  -to [all_registers -data_pins] \
  -through [get_pins {_11509_/Y}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -sort_by_slack \
  -group_count 50 \
  -endpoint_count 50 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```

若前 50 条最差路径中的大多数都经过该引脚，则支持“公共高扇出热点”假设；否则应弱化该假设。

### 5. 确认 `_12026_` 与 `out_data[0]` 的连接关系

```tcl
report_instance [get_cells {_12026_}]
report_pin [get_pins {_12026_/D}]
report_pin [get_pins {_12026_/Q}]

set qnet_12026 [get_nets -of_objects [get_pins {_12026_/Q}]]
report_net -connections -verbose $qnet_12026

set out0net [get_nets -of_objects [get_ports {out_data[0]}]]
report_net -connections -verbose $out0net
```

目的：确认 `_12026_` 是否确实是 `out_data[0]` 的输出寄存器。

### 6. 查看 `_11509_/Y` 的全部负载

```tcl
report_instance [get_cells {_11509_}]
report_pin [get_pins {_11509_/Y}]

set net_11509_y [get_nets -of_objects [get_pins {_11509_/Y}]]
report_net -connections -verbose $net_11509_y
```

目的：确认 31 个负载是否主要是输出数据 mux 或其他饱和逻辑。

### 7. 查看当前库触发器的时钟到 Q 特性

```tcl
report_checks \
  -from [get_pins {_12026_/CLK}] \
  -to [get_ports {out_data[0]}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```

目的：用现有 `sky130_fd_sc_hd__dfxtp_1` 的 clock-to-Q 延迟，对“输入寄存器方案”的一阶可行性进行估计。

### 8. 做“输入延迟为 0”的对照分析

此查询只作对照，不是修改建议；修改建议仍必须保持原 0.2T 输入约束。

```tcl
set ins [get_ports {in_a[*] in_b[*] in_valid rst}]

set_input_delay -clock clk -max 0 $ins

report_checks \
  -from [get_ports {in_b[2]}] \
  -to [get_pins {_12026_/D}] \
  -path_delay max \
  -scene ss_n40C_1v60 \
  -format full_clock_expanded \
  -fields {slew cap input_pins fanout} \
  -digits 4
```

最好在单独 OpenSTA 会话中执行；若在同一会话执行，之后应恢复：

```tcl
set_input_delay -clock clk -max 5.582 $ins
```

### 9. 查询基线面积和单元构成

```tcl
report_cell_usage -verbose
report_design_area
```

目的：为 1.25 倍面积限制建立基线。若 Liberty 面积信息不完整，还需要从固定综合流程的 Yosys/ABC `stat` 输出中获取面积或等效面积。

### 10. 对候选修改后的网表执行完整回归

对每个候选网表，在原 T、原 SDC、原输出负载下执行：

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
    -group_count 20 \
    -endpoint_count 20 \
    -format end \
    -digits 6

  puts "===== $scene hold ====="
  report_checks \
    -path_delay min \
    -scene $scene \
    -sort_by_slack \
    -group_count 20 \
    -endpoint_count 20 \
    -format end \
    -digits 6
}

report_design_area
```

---

## 五、可能的修改

以下方案都不改变接口、T、输入/输出延迟或输出负载，并且都能每个时钟接收一笔新交易。由于缺少基线面积，任何方案在完成综合和 `report_design_area` 前都不能声称已经满足 1.25 倍面积限制。

### 方案 A：先进行无额外延迟的算术局部优化

#### A1. 简化饱和比较

现有 RTL 使用两个 34 位大小比较（`dot4sat.v:31-35`）。可以利用 34 位有符号数的高 3 位直接生成溢出标志：

```verilog
wire pos_ovf = ~sum[33] & (|sum[32:31]);
wire neg_ovf =  sum[33] & ~(&sum[32:31]);

wire [31:0] sat = pos_ovf ? 32'h7FFF_FFFF :
                  neg_ovf ? 32'h8000_0000 :
                            sum[31:0];
```

含义：

- 正数可表示时，高 3 位必须为 `000`；
- 负数可表示时，高 3 位必须为 `111`；
- 因此不需要两个完整 34 位数值比较器。

这可能同时减少延迟和面积，但 ABC 可能已经做过类似常量优化，所以不能预先保证有效。

#### A2. 显式平衡四输入加法树

将四个乘积按 `(p0+p1)+(p2+p3)` 求和，并显式进行符号扩展：

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

目的：避免综合器将 `p0+p1+p2+p3` 映射成过长的线性加法链。若当前网表已经是平衡树，则收益会很小。

### 方案 B：插入输入寄存器，形成 L=2

结构：

- 第 n 个上升沿：寄存 `in_a`、`in_b`、`in_valid`；
- 第 n+1 个上升沿：对已寄存输入执行完整乘法、求和、饱和，并写入现有输出寄存器；
- 延迟从 L=1 变为 L=2；
- 没有停顿，仍能每个时钟接收一笔交易。

控制逻辑示意：

```verilog
reg [63:0] a_q, b_q;
reg        v_q;

// 乘法、求和、饱和均改用 a_q、b_q，
// 得到的组合结果记为 sat_q。

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

    out_data <= sat_q;   // out_data 不需要复位
end
```

时间上的依据：

- 当前端口后逻辑耗时约 25.6528 ns；
- 输出寄存器所需时间为 27.3541 ns；
- 若重新映射不变，新增输入触发器留给 clock-to-Q 的一阶余量约为：
  `27.3541 − 25.6528 = 1.7013 ns`。
- 这还没有计入新增触发器的 clock-to-Q、Q 端负载变化和重新综合造成的差异，所以必须用候选网表验证。

优点：

- 不改变乘法、求和和饱和算法；
- 只增加约 128 个数据输入寄存器和 1 个 `in_valid` 管道寄存器；
- 对高扇出饱和选择仍提供完整时钟周期。

风险：

- 新增寄存器面积未验证；
- 重新综合后逻辑映射可能改变；
- 必须检查新输入寄存器到输出寄存器的 hold/setup。

### 方案 C：在乘积之后插入寄存器，形成 L=2

结构：

- 第 n 个上升沿：寄存 `p0`～`p3` 和 `in_valid`；
- 第 n+1 个上升沿：对寄存的四个乘积求和、饱和并写入输出寄存器。

示意：

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

- 在自然算术边界切断“乘法器 → 加法树 → 饱和”的长路径；
- 与输入寄存方案一样，大约增加 129 位寄存器；
- 后级求和和饱和享有完整时钟周期。

风险：

- 第一级仍只有扣除 0.2T 输入延迟后的 21.7721 ns 可用，必须确认单个 16×16 乘法器在该窗口内可满足；
- 目前缺少乘积边界的到达时间，不能判断它是否比输入寄存方案更好。

### 方案 D：插入乘积寄存器和求和/溢出标志寄存器，形成 L=3

若 L=2 仍有违例，可使用允许的最大延迟 L=3：

1. 第 n 个沿：寄存四个 32 位乘积；
2. 第 n+1 个沿：寄存 34 位总和，以及由高 3 位生成的 `pos_ovf`、`neg_ovf`；
3. 第 n+2 个沿：只执行输出饱和选择并写入 `out_data`。

示意：

```verilog
reg signed [31:0] p0_q, p1_q, p2_q, p3_q;
reg signed [33:0] sum_q;
reg               pos_q, neg_q;
reg               v1_q, v2_q;

// sum_next 由 p0_q～p3_q 计算
// pos_next/neg_next 由 sum_next[33:31] 计算

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

优点：

- 将乘法、四输入求和、饱和选择分成三个较明确的阶段；
- 饱和标志提前寄存，可以把当前疑似高扇出的选择信号从长算术路径末端移出；
- 最后一级基本只剩 32 位 mux。

面积估计：

- 新增约 128 个乘积寄存器；
- 34 个 `sum` 寄存器；
- 2 个溢出标志寄存器；
- 2 个 valid 管道寄存器；
- 合计约 166 位新增寄存器，实际面积必须经综合确认。

### 方案 E：条件性的高扇出结构处理

只有在查询确认 `_11509_/Y` 确实是饱和选择或公共输出 mux 控制信号后，才建议：

- 将饱和标志按输出字节或输出半字复制，形成较小的扇出组；
- 或在结构层面为该控制网络建立平衡缓冲树；
- 或优先采用方案 D，直接寄存饱和标志。

不建议在确认功能归属前盲目复制逻辑，因为可能只增加面积而不能缩短真正的关键路径。

### 建议的实施顺序

1. 先完成第四部分的网表映射和前 50 条路径查询。
2. 尝试方案 A 的无额外延迟算术优化，并做形式等价检查。
3. 若仍违例，优先评估方案 B 或 C 的 L=2 版本；两者新增寄存器数量相近，应根据乘积边界到达时间和面积结果选择。
4. 若 L=2 仍不满足任一 corner 的 setup，采用方案 D 的 L=3 版本。
5. 最终候选必须同时满足：
   - 6 个 corner 的 setup 和 hold 均非负；
   - L≤3；
   - 每周期接收一笔交易；
   - 接口及 IO 约束不变；
   - 面积 ≤ 基线面积的 1.25 倍。
