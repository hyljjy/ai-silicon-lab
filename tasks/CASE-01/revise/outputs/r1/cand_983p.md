## 修改假设

采用阶段 A 的方案 B：在输入端插入一级寄存器（128 位数据 + 1 位 valid 管道），把原来"输入端口 → 乘法 → 求和 → 饱和 → 输出寄存器"的单周期长路径拆成两段，延迟从 L=1 变为 L=2，吞吐不变（每周期仍接收一笔交易）。

依据：

- 基线全部算术链压在一个周期内，最差路径 `in_b[2] → _12026_/D` 在 `ss_n40C_1v60` 下 slack 为 −4.1897 ns（`path_report.rpt:1-5`、`path_report.rpt:87-100`），只有两个低电压 slow corner 违例（`slack_summary.tsv:27-42`）。
- 阶段 A 查询 B10 已确认：把输入 max delay（0.2T = 5.582 ns）清零后，同一路径 slack 从 −4.1897 变为 +1.3923 ns（`阶段A答复.md:59-69`）。输入寄存器正好让算术链不再承担输入外部延迟。
- 扣除输入端口自身延迟、计入新增寄存器 clock-to-Q 后，一阶估计剩余约 +1.07 ns 余量（`阶段A答复.md:490-500`）。
- L=2 在允许范围 1–3 内（`constraints.md:14`），且 valid 管道和同步复位语义按合同第 2.2、2.3 节对齐（`contract_excerpt.md:28-47`）。

## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 插入输入寄存器，算术链不再承担 0.2T 输入延迟，L=2 | slack | setup | all | global | absolute | 改善 | 0 | 1.4 | ns | 1.07 | 阶段A答复.md:61-69；阶段A答复.md:496-500 |
| P2 | 同上，`ss_100C_1v60` 下内部路径余量更大 | slack | setup | ss_100C_1v60 | global | absolute | 改善 | 0 | 4.9 | ns | 4.57 | slack_summary.tsv:27-29；path_report.rpt:11 |
| P3 | 新增输入寄存器后 reg2reg 路径成为最差类别（基线无此类） | slack | setup | all | reg2reg | absolute | 未知 | 未知 | 未知 | ns | 未知 | slack_summary.tsv:9；阶段A答复.md:191-193 |
| P4 | 新增约 129 位寄存器（128 数据 + 1 valid） | area | | | | delta | 退化 | 未知 | 未知 | µm² | 未知 | 阶段A答复.md:488-489；constraints.md:19-20 |
| P5 | 新增 reg2reg 短路径，hold 只记录不判定 | slack | hold | all | reg2reg | absolute | 未知 | 未知 | 未知 | ns | 未知 | 阶段A答复.md:191-193；constraints.md:25 |
| P6 | 延迟由 1 改为 2 | L | | | | | | | | | 2 | constraints.md:14；contract_excerpt.md:26-34 |
| P7 | valid 两级管道 + 同步复位清管道，数据路径算术不变 | function | | | | | | | | | pass | contract_excerpt.md:36-47；dot4sat.v:23-35 |

## 代价

- **面积**：新增约 129 位触发器（128 位输入数据寄存 + 1 位 valid 管道），面积相对基线 45383.5264 µm² 增加；无面积测量手段（`阶段A答复.md:90-94`），具体数值不确定，但 129 个 dfxtp 相对整个四乘法器设计的面积占比小，预计远低于 56729.408 µm² 上限（`constraints.md:19-20`）。
- **延迟 L**：从 1 增加到 2，仍在允许范围 1–3 内（`constraints.md:14`）；吞吐不变，每周期接收一笔交易。
- **hold**：新增 reg2reg 和 in2reg 短路径，基线最低 hold slack 仅约 0.059 ns（`slack_summary.tsv:52`），新路径的 min-delay 表现不确定；但 hold 只记录不作判据（`constraints.md:25`）。
- **功能风险**：valid 管道级数、同步复位清空在途交易的时序必须与合同第 2.3 节严格对齐，尤其是"复位恰好在 R_(n+L−1)"的边界情况（`contract_excerpt.md:43-45`）；算术部分逐字保留基线表达式，降低了算术错误风险。

## 失败条件

- 6 个 std corner 中最差 setup slack < 0，即正式成功标准未满足（`constraints.md:24`）。
- RTL 仿真或门级功能仿真任一失败（valid 对齐、复位边界、饱和数值任一不符），function 判为 fail（`constraints.md:75`）。
- 综合后面积超过 56729.408 µm²（`constraints.md:19`）。
- 因违反 G1–G8 中任一条（端口集合、单模块、无 parameter/宏、事件控制形式、clk 用法、DECLARED_L 范围）被拒绝评估（`constraints.md:31-40`）。
- 最差 setup slack 改善量明显小于 P1 的下端（例如仍低于 −1 ns），说明"输入寄存即可收敛"的一阶估计被推翻（`阶段A答复.md:119-122`）。

## 声明行和 RTL

DECLARED_L = 2

```verilog
// CASE-01 candidate: input-registered pipeline, latency L = 2.
// Stage 1 registers in_a/in_b/in_valid; stage 2 computes products, exact 34-bit sum,
// saturation and registers the output. Synchronous active-high reset clears both
// valid pipeline stages; data registers are not reset (spec 2.4).
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    reg [63:0] a_q;
    reg [63:0] b_q;
    reg        v_q;

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

    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;

    wire [31:0] sat = (sum > SMAX) ? 32'h7FFF_FFFF :
                      (sum < SMIN) ? 32'h8000_0000 : sum[31:0];

    always @(posedge clk) begin
        a_q      <= in_a;
        b_q      <= in_b;
        out_data <= sat;
        if (rst) begin
            v_q       <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            v_q       <= in_valid;
            out_valid <= v_q;
        end
    end

endmodule
```