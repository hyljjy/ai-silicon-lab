## 修改假设

**要改什么**

把基线的单周期结构（`dot4sat.v:23-40`，输入经全部组合逻辑直接进输出寄存器）改成 3 级流水，L = 3：

1. 第 1 级：`in_a`、`in_b` 直接打入输入寄存器（128 位）。`in_valid` 打入 `v1`，同步复位清零。
2. 第 2 级：每路用寄存后的操作数做 16×16 有符号乘法，结果打入 4 个 32 位乘积寄存器。`v1` 打入 `v2`，同步复位清零。
3. 第 3 级：4 个乘积符号扩展到 34 位后相加，再饱和，打入 `out_data`。`v2` 打入 `out_valid`，同步复位清零。

位宽和饱和常数与基线一致（`dot4sat.v:28-35`）。

**为什么能改善**

- 基线的违例全部是 in2reg 一类，最差 −4.1897 ns，在 ss_n40C（`slack_summary.tsv:35-37`）。这类路径要在扣掉 0.2T 输入延迟（5.582 ns，`path_report.rpt:11`）后的时间内，走完乘法、四数相加、34 位进位传播和饱和全部逻辑（`path_report.rpt:12-87`）。
- 阶段 A 已确认：
  - 从端口到 D 的组合延迟是 25.96 ns（`阶段A答复.md:63`）。
  - 饱和级之前的到达时间就已晚于 required（`阶段A答复.md:79`）。
  - 单点尺寸替换只改善 0.67 ns（`阶段A答复.md:43`）。
  - 所以问题是结构性的逻辑过深（`阶段A答复.md:85`），只能靠切分流水级解决。
- 阶段 A 首选的方案 C（L = 2，只寄存乘积）有一个已知的不确定点：第一级"端口约束加一个乘法器及其 CPA"能否在约 21.8 ns 内完成（`阶段A答复.md:151`、`阶段A答复.md:172`）。本候选在此基础上再加一级输入寄存器，消除这个不确定点：
  - 输入端口只直接驱动寄存器 D，in2reg 路径几乎没有逻辑。
  - 乘法器变成 reg2reg 路径，可用时间约 26.8 ns（`阶段A答复.md:152`）。原来全部逻辑合起来是 25.96 ns，单个乘法器明显更短。
  - 第 3 级"四数相加加饱和"同样是 reg2reg。阶段 A 估算约 20 ns 或更少，小于 26.8 ns（`阶段A答复.md:171`）。
- L = 3 在允许范围 1–3 之内（`constraints.md:14`、`constraints.md:40`）。

**面积依据**

- 新增 128 + 128 位数据寄存器和 2 个 valid 寄存器，共 258 个触发器。
- 按阶段 A 假设的 `dfxtp_1` 约 20 µm²，约增加 5160 µm²。这个单元面积在材料中**未确认**（`阶段A答复.md:103`、`阶段A答复.md:158`）。
- 面积上限对应的可增面积约 11346 µm²（`constraints.md:19-20`）。

**功能依据**

- valid 每级都用同步 `rst` 清零，满足合同第 2.3 节的公式：对 L = 3，`O_(n+3).valid` 要求 `rst[n]`、`rst[n+1]`、`rst[n+2]` 都为 0（`contract_excerpt.md:38`、`contract_excerpt.md:40`）。
- 数据寄存器不复位，合同允许（`contract_excerpt.md:51`）。
- 乘积最大值是 (−32768)² = 2^30，32 位有符号能表示。和用 34 位有符号计算，不截断，不提前饱和（`contract_excerpt.md:65`、`contract_excerpt.md:69`）。

## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 3 级流水（输入寄存、乘积寄存、输出寄存） | slack | setup | all | global | absolute | 改善 | 0 | 21.7 | ns | 8 | 阶段A答复.md:63 |
| P2 | 3 级流水（输入寄存、乘积寄存、输出寄存） | slack | setup | all | global | delta | 改善 | 4.19 | 25.9 | ns | 12 | slack_summary.tsv:35 |
| P3 | 3 级流水，乘法器和加法饱和变为 reg2reg | slack | setup | ss_n40C_1v60 | reg2reg | absolute | 未知 | 0 | 未知 | ns | 8 | 阶段A答复.md:152 |
| P4 | 输入端口只直接驱动输入寄存器 | slack | setup | ss_n40C_1v60 | in2reg | absolute | 改善 | 20.5 | 22.5 | ns | 21.8 | path_report.rpt:11 |
| P5 | 输出寄存器结构不变 | slack | setup | ss_n40C_1v60 | reg2out | absolute | 不变 | 21.5 | 21.8 | ns | 21.69 | slack_summary.tsv:41 |
| P6 | 新增 128 位输入寄存器、128 位乘积寄存器、2 个 valid 寄存器 | area |  |  |  |  delta | 退化 | 4000 | 11345.9 | µm² | 5200 | 阶段A答复.md:158 |
| P7 | 新增 258 个触发器 | area |  |  |  | absolute | 退化 | 49383 | 56729.408 | µm² | 50600 | constraints.md:19-20 |
| P8 | 端口直连输入寄存器 D、valid 经复位门 | slack | hold | all | global | absolute | 未知 | 未知 | 未知 | ns | 未知 | slack_summary.tsv:52 |
| P9 | 3 级流水 | L |  |  |  |  |  |  |  |  | 3 | contract_excerpt.md:28 |
| P10 | 3 级流水，每级 valid 同步复位，34 位精确求和后饱和 | function |  |  |  |  |  |  |  |  | pass | contract_excerpt.md:38-40 |

（注：P3 的 reg2reg 在基线中是 NONE（`slack_summary.tsv:39`），没有可比的基线值，所以 direction 写"未知"。）

## 代价

**面积**
- 新增 258 个触发器。按约 20 µm² 估算约 +5160 µm²，这个单元面积**未确认**。
- 拆成 4 个独立乘法器加一个四输入加法器后，综合结果可能与基线合并的乘加结构不同，组合逻辑面积变化**不确定**。
- 预计总面积约 5.0–5.2 万 µm²，低于 56729.408 µm² 的上限。但如果组合逻辑明显膨胀，余量会收窄。

**延迟 L**
- 从 1 增加到 3，达到允许的上限。
- 吞吐不变，仍是每拍接收一笔交易，没有停顿和背压。

**hold**
- 新增的 hold 路径有两类：
  - 输入端口直连输入寄存器 D，输入延迟 min 为 0，中间没有组合逻辑。
  - valid 链的寄存器到寄存器路径，只经过一个复位门。
- 这两类可能比基线最差 hold（约 0.059 ns，`slack_summary.tsv:52`）更小，甚至接近 0，具体数值**不确定**。
- hold 只记录，不作判据（`constraints.md:25`）。

**功能风险**
- 合同要求交易级等价，这一点由 valid 链长度和数据链长度一致来保证，两条链都是 3 级。
- 风险在于有符号扩展写法，例如乘积寄存器是否声明为 signed、34 位求和时各操作数是否按有符号扩展。RTL 中全部声明为 signed，并沿用基线已验证的求和与比较写法（`dot4sat.v:29-35`）。

## 失败条件

- 6 个 std 点中最差的 setup slack（WS max 的最小值）< 0。
- ss_n40C_1v60 下 reg2reg 类最差 setup slack < 0。这说明单个乘法器或四数相加加饱和一级仍然超过一个周期。
- ss_n40C_1v60 下 in2reg 类最差 setup slack 没有高于基线的 −4.1897 ns。
- 综合面积 > 56729.408 µm²。
- RTL 仿真或门级功能仿真任一失败（function = fail）。
- 评估按 L = 3 比对时，出现 valid 错位、丢失、重复，或者 valid 为 1 时 `out_data` 与参考值不等。
- 候选因 G1–G8 任一规则被拒，没有进入评估。

## 声明行和 RTL

DECLARED_L = 3

```verilog
// CASE-01 candidate: three-stage pipeline, latency L = 3.
// Stage 1: register operands. Stage 2: register four signed 16x16 products.
// Stage 3: exact 34-bit sum, saturate to 32-bit signed, register output.
// Valid bits are cleared by synchronous active-high reset at every stage.
// Data registers are not reset (data is don't-care when valid is 0).
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    // stage 1 registers
    reg [63:0] a_r;
    reg [63:0] b_r;
    reg        v1;

    // stage 2 registers
    reg signed [31:0] p0_r;
    reg signed [31:0] p1_r;
    reg signed [31:0] p2_r;
    reg signed [31:0] p3_r;
    reg               v2;

    wire signed [15:0] a0 = a_r[15:0];
    wire signed [15:0] a1 = a_r[31:16];
    wire signed [15:0] a2 = a_r[47:32];
    wire signed [15:0] a3 = a_r[63:48];
    wire signed [15:0] b0 = b_r[15:0];
    wire signed [15:0] b1 = b_r[31:16];
    wire signed [15:0] b2 = b_r[47:32];
    wire signed [15:0] b3 = b_r[63:48];

    wire signed [31:0] p0 = a0 * b0;
    wire signed [31:0] p1 = a1 * b1;
    wire signed [31:0] p2 = a2 * b2;
    wire signed [31:0] p3 = a3 * b3;

    // full range is [-4294836224, 4294967296]: needs 34 signed bits
    wire signed [33:0] sum = p0_r + p1_r + p2_r + p3_r;

    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;

    wire [31:0] sat = (sum > SMAX) ? 32'h7FFF_FFFF :
                      (sum < SMIN) ? 32'h8000_0000 : sum[31:0];

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