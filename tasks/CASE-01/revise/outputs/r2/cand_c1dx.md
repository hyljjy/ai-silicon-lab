## 修改假设

上一轮候选在 STA 步骤失败，失败点在综合网表读取时出现语法错误，因此本轮换一种结构更接近基线的流水实现：把 `in_a`、`in_b` 先打入 64 位输入寄存器（`a_q`、`b_q`），乘法、34 位求和、饱和仍然沿用基线的表达式，但数据源从输入端口改成输入寄存器，整体作为第二拍 reg2reg 逻辑写入输出寄存器；`in_valid` 额外延迟一拍实现对 L=2 的 valid 对齐。

这样做的时序理由是：基线的关键违例是 `in_b[2] → _12026_/D` 的输入到寄存器路径，数据到达 31.5439、要求 27.3541，slack 为 −4.1897（path_report.rpt:87-100）。该到达时间包含固定输入外部延迟 5.582（path_report.rpt:11），扣除后组合延迟约 25.96（阶段A答复.md:5）。把长算术路径放进输入寄存器之后的 reg2reg 段，算术路径不再背负这段输入外部延迟；而新的 in2reg 路径只到 `a_q`、`b_q`、`valid_q` 的 D 端，深度极短。第二拍 reg2reg 的要求时间仍约为 `T - setup = 27.3541`（path_report.rpt:90-95），预计可以容纳原有约 25.96 的算术延迟，最终需要综合后 STA 确认。

算术形式保持与基线 `dot4sat.v:28-35` 相同，不再新增上一轮中独立的 `s0..s3` 34 位中间连续赋值，以降低生成网表不能被 OpenSTA 解析的风险。数据寄存器不复位，符合合同允许数据寄存器不复位的要求（contract_excerpt.md:51；dot4sat.v:2-3）。

## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 输入先寄存为 a_q/b_q，乘法/求和/饱和整体移入第二拍 reg2reg | slack | setup | all | global | absolute | 改善 | 未知 | 未知 | ns | 未知 | path_report.rpt:11、87-100 |
| P2 | 同一改动使 in2reg 路径缩短为输入到 129 位寄存器 D 端 | slack | setup | ss_n40C_1v60 | in2reg | delta | 改善 | 未知 | 未知 | ns | 未知 | path_report.rpt:87-100；slack_summary.tsv:35-38 |
| P3 | 新出现的 a_q/b_q→out_data 的 reg2reg setup 路径 | slack | setup | ss_n40C_1v60 | reg2reg | absolute | 未知 | 未知 | 未知 | ns | 未知 | path_report.rpt:90-100；阶段A答复.md:5 |
| P4 | 新增 64+64 位输入寄存器和 1 位 valid 延迟寄存器 | area | | | | absolute | 退化 | 未知 | 56729.408 | µm² | 未知 | constraints.md:19-20 |
| P5 | 实现为 L=2 两级流水 | L | | | | | | | | | 2 | contract_excerpt.md:28-35 |
| P6 | 保持 34 位精确求和与饱和语义不变，valid 按 L=2 对齐 | function | | | | | | | | | pass | contract_excerpt.md:38-39、64-67；dot4sat.v:28-35 |
| P7 | 新增内部寄存器后 hold 检查的变化 | slack | hold | all | global | absolute | 未知 | 未知 | 未知 | ns | 未知 | constraints.md:24-25 |

## 代价

- **面积**：相比 F1 基线新增 `a_q` 64 位、`b_q` 64 位和 `valid_q` 1 位，共 129 个寄存器位；算术部分与基线相同。面积预计仍低于上限 56729.408 µm²（constraints.md:19-20）。
- **延迟 L**：由 1 变为 2，满足允许范围 1–3（constraints.md:14）。
- **hold**：新增输入寄存器和 reg2reg 路径会改变 hold 结果；hold 只记录，不进入正式成功判据（constraints.md:24-25）。
- **功能风险**：求和仍用 34 位有符号数，未提前截断；饱和逻辑沿用基线比较式。数据寄存器不复位，TB 只在 `out_valid=1` 时检查 `out_data`（contract_excerpt.md:51-53）。

## 失败条件

- 任一 std corner 的全局最差 setup slack < 0（constraints.md:22-24）。
- 综合后的网表在 STA 读取时再次出现语法错误，导致无法得到有效时序结果。
- 综合后面积 > 56729.408 µm²（constraints.md:19）。
- RTL 仿真或门级功能仿真中，任何观测点 `out_valid`/`out_data` 与 L=2 期望不符（contract_excerpt.md:38-39、53）。
- 实际延迟不是 2，或因配置校验失败使候选被拒（contract_excerpt.md:58-59）。

## 声明行和 RTL

DECLARED_L = 2

```verilog
// CASE-01 L=2 implementation: register inputs first, then multiply/sum/saturate
// in the second stage. Synchronous active-high reset clears all valid state.
// Data registers are intentionally not reset (data is don't-care when out_valid=0).
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    // First pipeline stage: capture inputs and a valid bit.
    reg [63:0] a_q;
    reg [63:0] b_q;
    reg        valid_q;

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

    // Full range is [-4294836224, 4294967296]: needs 34 signed bits.
    wire signed [33:0] sum = p0 + p1 + p2 + p3;

    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;

    wire [31:0] sat = (sum > SMAX) ? 32'h7fff_ffff :
                      (sum < SMIN) ? 32'h8000_0000 : sum[31:0];

    always @(posedge clk) begin
        if (rst) begin
            valid_q   <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            valid_q   <= in_valid;
            out_valid <= valid_q;
        end
        a_q      <= in_a;
        b_q      <= in_b;
        out_data <= sat;
    end

endmodule
```