## 修改假设

**第 1 轮结果说明了什么**

- 第 1 轮候选的 RTL 仿真和门级功能仿真都通过（各 checked=2816），面积 48790.544 µm²，没有超过上限 56729.408 µm²（`constraints.md:19`）。
- 失败发生在 STA 步骤：OpenSTA 读综合网表 `netlist.v` 第 6102 行时报 syntax error，所以没有任何 slack 数据。流水线的功能和面积已有实测，问题出在"网表能否被 STA 读入"。
- 门级仿真器能读这个网表，OpenSTA 不能。这说明网表是合法的 Verilog，只是含有 OpenSTA 结构网表读入器不支持的写法。
- 网表没有提供给我（`constraints.md:83`），所以第 6102 行的确切内容和根因都**不确定**。

**根因假设（推断，未确认）**

- 基线中所有寄存器的输出都是端口 `out_data`、`out_valid`，它们不是 signed（`dot4sat.v:10-11`）。基线中的 signed 线网（`dot4sat.v:14-29`）都是组合中间量，基线网表能被 STA 读入（`slack_summary.tsv:11-58`）。
- 第 1 轮候选新增了带 `signed` 的内部寄存器 `p0_r`…`p3_r`。它们是触发器 Q 端的线网，会以公共名字保留在网表中，Yosys 可能把它们写成 `wire signed [31:0] ...`。OpenSTA 的网表读入器很可能不接受 `signed` 关键字。
- 这是我能想到的最可能的差异，但没有直接证据。

**要改什么**

- 保持 3 级流水结构不变（输入寄存 → 乘积寄存 → 求和饱和后寄存，L = 3）。这个结构的功能已经通过两种仿真。
- RTL 中去掉所有 `signed` 声明，所有 reg 和 wire 都是无符号的：
  - 乘法用 `$signed()` 转换表达式实现。
  - 34 位求和用显式符号位复制扩展。
  - 饱和判断改为按符号位和高位做比特判断，与原比较等价：
    - 正溢出：`sum[33]=0` 且 `sum[32:31]≠00`，即 s ≥ 2^31。
    - 负溢出：`sum[33]=1` 且 `sum[32:31]≠11`，即 s < −2^31。
  - 这一改动在数学上符合 `contract_excerpt.md:64-69`。

**为什么能改善时序（与第 1 轮相同）**

- 基线的违例全部是 in2reg，最差 −4.1897 ns，出现在 ss_n40C_1v60（`slack_summary.tsv:35-37`）。
- 原因是单周期内逻辑过深（`阶段A答复.md:85`）：端口到 D 的组合延迟为 25.96 ns（`阶段A答复.md:63`），饱和级之前就已超时（`阶段A答复.md:79`）。
- 切成 3 级以后：
  - in2reg 只剩端口直接到 D。
  - 乘法和"四数相加加饱和"都变成 reg2reg，可用时间约 26.8 ns（`阶段A答复.md:152`）。

**为什么没有选择 NO_SUBMISSION**

功能和面积都已实测通过，失败点很可能是可规避的网表格式问题，重新提交的代价很小。

## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 3 级流水，RTL 去掉 signed 声明 | slack | setup | all | global | absolute | 改善 | 0 | 21.7 | ns | 9 | 阶段A答复.md:152 |
| P2 | 3 级流水，RTL 去掉 signed 声明 | slack | setup | all | global | delta | 改善 | 4.19 | 25.9 | ns | 13 | slack_summary.tsv:35 |
| P3 | 乘法器、加法饱和变为 reg2reg | slack | setup | ss_n40C_1v60 | reg2reg | absolute | 未知 | 0 | 未知 | ns | 9 | 阶段A答复.md:171 |
| P4 | 输入端口直接驱动输入寄存器 | slack | setup | ss_n40C_1v60 | in2reg | absolute | 改善 | 20.5 | 22.5 | ns | 21.4 | path_report.rpt:11-12 |
| P5 | 输出寄存器直接驱动端口，结构不变 | slack | setup | ss_n40C_1v60 | reg2out | absolute | 不变 | 21.5 | 21.8 | ns | 21.69 | slack_summary.tsv:41 |
| P6 | 新增 258 个触发器，饱和逻辑改写 | area |  |  |  | delta | 退化 | 2500 | 5500 | µm² | 3400 | constraints.md:20 |
| P7 | 新增 258 个触发器，饱和逻辑改写 | area |  |  |  | absolute | 退化 | 47900 | 50900 | µm² | 48800 | constraints.md:19-20 |
| P8 | 端口直连寄存器 D，valid 链 | slack | hold | all | global | absolute | 未知 | 未知 | 未知 | ns | 未知 | slack_summary.tsv:52 |
| P9 | 3 级流水 | L |  |  |  |  |  |  |  |  | 3 | contract_excerpt.md:28 |
| P10 | 每级 valid 同步复位，34 位精确求和，按位饱和 | function |  |  |  |  |  |  |  |  | pass | contract_excerpt.md:38-40 |

注：P6、P7 参考了第 1 轮的实测面积 48790.544 µm²。本轮只改了写法，结构相同，预计面积接近这个值。

## 代价

**面积**
- 第 1 轮同结构的实测面积为 48790.544 µm²，比基线多约 3407 µm²（`constraints.md:20`）。
- 本轮的按位饱和判断可能让面积略有变化，预计仍远低于 56729.408 µm²（`constraints.md:19`）。

**延迟 L**
- L 从 1 增加到 3，达到上限（`constraints.md:14`）。
- 吞吐不变，每拍接收一笔交易。

**hold**
- 新增的 hold 路径有两类：端口直接到输入寄存器 D（输入延迟 min 为 0，`case01_sdc.tcl:14`），以及 valid 链的 reg2reg 路径。
- 这些路径的 hold slack 可能低于基线的约 0.059 ns（`slack_summary.tsv:52`），具体数值不确定。
- hold 只记录，不作判据（`constraints.md:25`）。

**功能风险**
- 有符号处理从 signed 声明改为 `$signed()` 和手工符号扩展，饱和改为按位判断。这里引入了新的写法风险，但数学上等价。
- 乘积的真实值在 [−2^30+2^15, 2^30] 之内，32 位能精确表示。

**残余风险**
- 如果 STA 的解析失败并不是 `signed` 引起的，本轮仍然会在 STA 步骤失败。根因**不确定**。

## 失败条件

- STA 步骤再次报网表 syntax error 或其他读入错误。这说明 `signed` 声明不是根因，或者不是唯一根因。
- 6 个 std 点中最差的 setup slack < 0。
- ss_n40C_1v60 下 reg2reg 类最差 setup slack < 0。
- ss_n40C_1v60 下 in2reg 类最差 setup slack ≤ −4.1897 ns。
- 综合面积 > 56729.408 µm²。
- RTL 仿真或门级功能仿真任一失败（function = fail）。
- 候选因 G1–G8 任一规则被拒，没有进入评估。

## 声明行和 RTL

DECLARED_L = 3

```verilog
// CASE-01 candidate rev2: three-stage pipeline, latency L = 3.
// No signed declarations anywhere (avoid signed nets in the synthesized netlist).
// Stage 1: register operands. Stage 2: register four 16x16 signed products.
// Stage 3: exact 34-bit sum, saturate to 32-bit signed, register output.
// Valid bits are cleared by synchronous active-high reset at every stage.
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    reg [63:0] a_r;
    reg [63:0] b_r;
    reg        v1;

    reg [31:0] p0_r;
    reg [31:0] p1_r;
    reg [31:0] p2_r;
    reg [31:0] p3_r;
    reg        v2;

    // signed 16x16 products; true value fits in 32-bit two's complement
    wire [31:0] p0 = $signed(a_r[15:0])  * $signed(b_r[15:0]);
    wire [31:0] p1 = $signed(a_r[31:16]) * $signed(b_r[31:16]);
    wire [31:0] p2 = $signed(a_r[47:32]) * $signed(b_r[47:32]);
    wire [31:0] p3 = $signed(a_r[63:48]) * $signed(b_r[63:48]);

    // exact 34-bit two's complement sum via explicit sign extension
    wire [33:0] e0 = {{2{p0_r[31]}}, p0_r};
    wire [33:0] e1 = {{2{p1_r[31]}}, p1_r};
    wire [33:0] e2 = {{2{p2_r[31]}}, p2_r};
    wire [33:0] e3 = {{2{p3_r[31]}}, p3_r};
    wire [33:0] sum = e0 + e1 + e2 + e3;

    // s > 2^31-1  <=> non-negative and sum[32:31] != 00
    // s < -2^31   <=> negative and sum[32:31] != 11
    wire ovf_pos = ~sum[33] & (sum[32] | sum[31]);
    wire ovf_neg =  sum[33] & ~(sum[32] & sum[31]);

    wire [31:0] sat = ovf_pos ? 32'h7FFF_FFFF :
                      ovf_neg ? 32'h8000_0000 : sum[31:0];

    always @(posedge clk) begin
        if (rst) begin
            v1        <= 1'b0;
            v2        <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            v1        <= in_valid;
            v2        <= v1;
            out_valid <= v2;
        end
        a_r      <= in_a;
        b_r      <= in_b;
        p0_r     <= p0;
        p1_r     <= p1;
        p2_r     <= p2;
        p3_r     <= p3;
        out_data <= sat;
    end

endmodule
```