## 修改假设

第 1 轮候选的功能（RTL 仿真、门级仿真均 pass，checked=2835）和面积（47983.520000 µm²，低于上限）都已通过，唯一失败在 STA 步骤：`synth/netlist.v line 6052, syntax error`。这不是时序违例，而是综合网表在 STA 读取阶段的解析失败。材料中没有提供该网表，且本阶段不能查询（`constraints.md:83`），所以无法定位是哪一行、哪种结构触发了解析错误；候选 RTL 本身通过了 lint 和仿真，不违反 G1–G8。

本轮策略：

1. **保留第 1 轮的输入寄存器流水架构（L=2）**。依据不变：基线把全部算术链压在一个周期，最差路径 slack −4.1897 ns（`path_report.rpt:87-100`）；阶段 A 查询 B10 已确认输入 max delay 清零后同路径 slack 为 +1.3923 ns（`阶段A答复.md:61-69`），计入寄存器 clock-to-Q 后一阶估计余量约 +1.07 ns（`阶段A答复.md:496-500`）。该架构的功能和面积已被第 1 轮评估验证。
2. **用高三位溢出标志替代两个 34 位数值比较器**（阶段 A 方案 A1，`阶段A答复.md:422-433`）：`pos_ovf = ~sum[33] & (|sum[32:31])`，`neg_ovf = sum[33] & ~(&sum[32:31])`。这在数学上与 `sum > 2^31−1`、`sum < −2^31` 严格等价（34 位有符号数中，大于 2^31−1 当且仅当符号位为 0 且 bits 32:31 非 00；小于 −2^31 当且仅当符号位为 1 且 bits 32:31 非 11）。收益有二：
   - 缩短时序：路径报告中 15.19–27.79 ns 区段存在 o31ai/a311oi/o311ai 多级级联（`path_report.rpt:69-78`），与 34 位比较器的进位/比较链特征一致，A1 将其替换为对 3 个比特的与或操作，缩短第 2 级组合深度，增大 `ss_n40C_1v60`/`ss_100C_1v60` 的余量；
   - 改变综合网表结构：由于无法定位网表解析错误的具体成因，让算术部分产生与第 1 轮明显不同的网表，是唯一可做的、不违反"只能改 RTL"约束（`constraints.md:10`）的规避手段。需要说明：这只是规避尝试，不是已确诊的修复。

L=2 的 valid 管道和同步复位语义与第 1 轮完全相同，该语义已通过第 1 轮两种仿真，且与合同第 2.2、2.3 节逐条对齐（`contract_excerpt.md:28-47`）。

## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 输入寄存器 + 高三位饱和标志，算术链不再承担 0.2T 输入延迟且比较链缩短 | slack | setup | all | global | absolute | 改善 | 0 | 未知 | ns | 1.5 | 阶段A答复.md:61-69；阶段A答复.md:496-500；path_report.rpt:69-78 |
| P2 | 同上，`ss_100C_1v60` 基线违例仅 −0.687 ns，去除 5.582 ns 输入延迟后余量更大 | slack | setup | ss_100C_1v60 | global | absolute | 改善 | 0 | 未知 | ns | 5.0 | slack_summary.tsv:27-29；path_report.rpt:11 |
| P3 | 新增寄存器使 reg2reg 类别出现（基线为 NONE），最差路径将落在此类 | slack | setup | all | reg2reg | absolute | 未知 | 未知 | 未知 | ns | 未知 | slack_summary.tsv:9；阶段A答复.md:191-193 |
| P4 | 新增约 129 位寄存器，A1 略减比较逻辑；第 1 轮同架构实测 47983.52 µm² | area | | | | delta | 退化 | 2000 | 2600 | µm² | 2400 | constraints.md:19-20；第 1 轮评估结果面积 47983.520000 |
| P5 | 新增 in2reg 直达寄存器与 FF→FF valid 短路径；hold 只记录不判定 | slack | hold | all | global | absolute | 未知 | 未知 | 未知 | ns | 未知 | 阶段A答复.md:191-193；constraints.md:25 |
| P6 | 延迟由 1 改为 2 | L | | | | | | | | | 2 | constraints.md:14；contract_excerpt.md:26-34 |
| P7 | valid 两级管道与复位语义同第 1 轮（已 pass），A1 与基线饱和严格等价 | function | | | | | | | | | pass | contract_excerpt.md:36-47；阶段A答复.md:422-433 |

## 代价

- **面积**：寄存器数量与第 1 轮相同（约 129 位），A1 去掉两个 34 位比较器会略减组合逻辑。第 1 轮同架构实测面积 47983.520000 µm²，本轮预计与之相近或略低，相对基线 45383.5264 µm² 退化约 2000–2600 µm²，仍低于 56729.408 µm² 上限（`constraints.md:19-20`）。
- **延迟 L**：从 1 增加到 2，在允许范围 1–3 内（`constraints.md:14`）；吞吐不变，每周期接收一笔交易（`contract_excerpt.md:47`）。
- **hold**：新增输入直达寄存器的 in2reg 短路径和 `v_q → out_valid` 的 FF→FF 短路径，min-delay 表现没有实测依据；基线最低 hold slack 约 0.059 ns（`slack_summary.tsv:52`）。hold 只记录不作判据（`constraints.md:25`）。
- **功能风险**：valid 管道和复位边界语义与第 1 轮逐字相同，第 1 轮 RTL 仿真和门级仿真均 pass（checked=2835）；A1 的等价性在修改假设中已按位级论证，主要剩余风险是综合重映射后时序余量与一阶估计的偏差（`阶段A答复.md:500`）。
- **残余风险**：第 1 轮的网表解析失败原因无法从材料确诊，本轮以改变网表结构作为规避，不能保证不再触发。

## 失败条件

- STA 步骤再次因 `synth/netlist.v` 语法错误失败，无有效 slack 结果（说明问题与 RTL 语义无关，且材料不足以定位；第 1 轮评估结果）。
- 6 个 std corner 中最差 setup slack < 0，正式成功标准未满足（`constraints.md:24`）。
- RTL 仿真或门级功能仿真任一失败，function 判 fail（`constraints.md:75`），特别是 A1 饱和边界或 L=2 valid 对齐出错。
- 综合后面积超过 56729.408 µm²（`constraints.md:19`）。
- 因违反 G1–G8 任一条被拒绝评估（`constraints.md:31-40`）。
- 最差 setup slack 低于约 +0.5 ns，说明"输入寄存 + A1 可收敛"的估计被推翻，应改走 L=3 方案（`阶段A答复.md:539-586`）。

## 声明行和 RTL

DECLARED_L = 2

```verilog
// CASE-01 candidate round 2: input-registered pipeline, latency L = 2.
// Stage 1 registers in_a/in_b/in_valid; stage 2 computes products, exact 34-bit
// sum, flag-based saturation and registers the output. Synchronous active-high
// reset clears both valid stages; data registers are not reset (spec 2.4).
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    reg  [63:0] a_q;
    reg  [63:0] b_q;
    reg         v_q;

    wire signed [15:0] a0 = a_q[15:0];
    wire signed [15:0] a1 = a_q[31:16];
    wire signed [15:0] a2 = a_q[47:32];
    wire signed [15:0] a3 = a_q[63:48];
    wire signed [15:0] b0 = b_q[15:0];
    wire signed [15:0] b1 = b_q[31:16];
    wire signed [15:0] b2 = b_q[47:32];
    wire signed [15:0] b3 = b_q[63:48];

    wire signed [31:0] p0 = a0 * b0;
    wire signed [31:0] p1 = a1 * b1;
    wire signed [31:0] p2 = a2 * b2;
    wire signed [31:0] p3 = a3 * b3;

    // full range is [-4294836224, 4294967296]: needs 34 signed bits
    wire signed [33:0] sum = p0 + p1 + p2 + p3;

    // exact saturation from the top three bits of the 34-bit sum:
    // sum >  2^31-1  <=>  sign = 0 and sum[32:31] != 00
    // sum < -2^31    <=>  sign = 1 and sum[32:31] != 11
    wire pos_ovf = ~sum[33] & (|sum[32:31]);
    wire neg_ovf =  sum[33] & ~(&sum[32:31]);

    wire [31:0] sat = pos_ovf ? 32'h7FFF_FFFF :
                      neg_ovf ? 32'h8000_0000 : sum[31:0];

    always @(posedge clk) begin
        if (rst) begin
            v_q       <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            v_q       <= in_valid;
            out_valid <= v_q;
        end
        a_q      <= in_a;
        b_q      <= in_b;
        out_data <= sat;
    end

endmodule
```