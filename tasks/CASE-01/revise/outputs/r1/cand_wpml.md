## 修改假设

把基线 L=1 的单周期组合路径 `输入 → 四个 16×16 乘法 → 34 位求和 → 饱和 → 输出寄存器` 拆成两级流水（L=2）：第一级在四个乘积 `p0..p3` 后插入乘积寄存器，第二级再完成 34 位精确求和、饱和并打入输出寄存器；`in_valid` 相应延迟两拍以对齐 `out_valid`。

依据：基线最差 setup 路径 `in_b[2] → _12026_/D` 在 `ss_n40C_1v60` 违例为 −4.1897，数据到达 31.5439、要求 27.3541（path_report.rpt:87-100）。该路径中乘积后的求和/饱和链很长，且有 `_11509_/Y` 高扇出段 fanout=31、delay=2.6362（path_report.rpt:83-85）。把求和与饱和移到乘积寄存器之后，可把输入到第一级寄存器的组合深度缩小到基本只剩乘法；第一级输入组合预算在扣掉 0.2T 输入延迟后约 21.77 ns，乘积级明显可容纳（阶段A答复.md:103-106）。第二级乘积寄存器到输出寄存器不受输入延迟影响，预算约 27.35 ns，只承担求和与饱和，预计可由级间寄存器覆盖（阶段A答复.md:105-106）。

## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 在四个 16×16 乘积后插入乘积寄存器，形成 L=2 流水，把求和/饱和移入第二级 | slack | setup | all | global | absolute | 改善 | 未知 | 未知 | ns | 未知 | path_report.rpt:97-100；阶段A答复.md:103-106 |
| P2 | 同一流水线改动对最差输入到寄存器 setup 路径的影响 | slack | setup | ss_n40C_1v60 | in2reg | delta | 改善 | 未知 | 未知 | ns | 未知 | path_report.rpt:1-5、97-100；阶段A答复.md:105-106 |
| P3 | 增加 4×32 位乘积寄存器和 1 个 valid 延迟寄存器 | area | | | | absolute | 退化 | 未知 | 56729.408 | µm² | 未知 | constraints.md:19-20 |
| P4 | 采用两级流水实现，L=2 | L | | | | | | | | | 2 | 阶段A答复.md:105 |
| P5 | 保持 34 位精确求和与饱和语义不变，且 valid 随数据对齐 | function | | | | | | | | | pass | contract_excerpt.md:38-39、64-67；dot4sat.v:28-35 |

## 代价

- **面积**：新增 4 个 32 位乘积寄存器和 1 个 valid 延迟寄存器，面积会相对 F1 基线上涨；具体综合面积未知，以不超过 56729.408 µm² 为上限（constraints.md:19-20）。
- **延迟 L**：由 1 变为 2，满足 L≤3（constraints.md:14）。
- **hold**：新增级间寄存器后 hold 检查会发生改变；hold 只记录、不判正式成功（constraints.md:24-25）。
- **功能风险**：求和必须用 34 位有符号数，不能先截断；本实现通过把乘积符号扩展后求和，并保留基线的饱和比较表达式。数据寄存器不复位，TB 仅在 `out_valid=1` 时检查 `out_data`，符合合同（contract_excerpt.md:51-53）。

## 失败条件

- 任一 std corner 的最差 setup WS < 0（constraints.md:22-24）。
- 综合后面积 > 56729.408 µm²（constraints.md:19）。
- RTL 仿真或门级功能仿真中，任何观测点 `out_valid`/`out_data` 与 L=2 期望不符（contract_excerpt.md:38-39、53）。
- 实际延迟不是 2，或因配置校验失败使候选被拒（contract_excerpt.md:58-59；constraints.md:44、46）。

## 声明行和 RTL

DECLARED_L = 2

```verilog
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    wire signed [15:0] a0 = in_a[15:0];
    wire signed [15:0] a1 = in_a[31:16];
    wire signed [15:0] a2 = in_a[47:32];
    wire signed [15:0] a3 = in_a[63:48];
    wire signed [15:0] b0 = in_b[15:0];
    wire signed [15:0] b1 = in_b[31:16];
    wire signed [15:0] b2 = in_b[47:32];
    wire signed [15:0] b3 = in_b[63:48];

    wire signed [31:0] p0 = a0 * b0;
    wire signed [31:0] p1 = a1 * b1;
    wire signed [31:0] p2 = a2 * b2;
    wire signed [31:0] p3 = a3 * b3;

    // First pipeline stage: register the four products.
    reg signed [31:0] p0_q;
    reg signed [31:0] p1_q;
    reg signed [31:0] p2_q;
    reg signed [31:0] p3_q;

    // Second pipeline stage: exact 34-bit sum and saturation.
    wire signed [33:0] s0 = p0_q;
    wire signed [33:0] s1 = p1_q;
    wire signed [33:0] s2 = p2_q;
    wire signed [33:0] s3 = p3_q;
    wire signed [33:0] sum = s0 + s1 + s2 + s3;

    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;

    wire [31:0] sat = (sum > SMAX) ? 32'h7fff_ffff :
                      (sum < SMIN) ? 32'h8000_0000 : sum[31:0];

    // Valid pipeline: one internal delay stage plus the output register.
    reg valid_q;

    always @(posedge clk) begin
        if (rst) begin
            valid_q   <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            valid_q   <= in_valid;
            out_valid <= valid_q;
        end
        p0_q <= p0;
        p1_q <= p1;
        p2_q <= p2;
        p3_q <= p3;
        out_data <= sat;
    end

endmodule
```