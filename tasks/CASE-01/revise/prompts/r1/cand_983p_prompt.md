下面是数字电路模块 `dot4sat` 的材料。请阅读全部材料，然后按要求作答。每个文件的每一行前面都标了行号。约束、提交格式和预测表的填写规则见 `constraints.md`。

=== 文件：constraints.md（共 83 行）===
   1| # 阶段 B 的约束和提交要求
   2| 
   3| 本文件只列硬约束、数字、RTL 的提交格式和预测表的填写规则。
   4| 
   5| 文中"合同"指 CASE-01 设计合同，相关条款见 `contract_excerpt.md`（合同第 1、2 节和第 3.1 节原文）。"F1 基线"指材料中的 `dot4sat.v`（L = 1）在冻结评估中的结果：各 corner 的 slack 见 `slack_summary.tsv`，面积见下面第 3 节。
   6| 
   7| ## 1. 不变的部分
   8| 
   9| - 时钟周期 T、IO 约束、SDC、工艺库、综合配方、corner 都不变（取值和原文见 `values.txt`、`case01_sdc.tcl`、`context.md`）。
  10| - 修改只能改 RTL。
  11| 
  12| ## 2. 延迟和吞吐
  13| 
  14| - 延迟 L 允许 1–3（L 的定义见合同第 2.2 节）。
  15| - 每个时钟周期接收一笔交易，没有停顿，没有背压。
  16| 
  17| ## 3. 面积
  18| 
  19| - 面积上限：56729.408 µm²。
  20| - F1 基线面积：45383.5264 µm²。
  21| 
  22| ## 4. 正式成功标准
  23| 
  24| - 6 个 std 点（`tt_025C_1v80`、`tt_100C_1v80`、`ss_100C_1v60`、`ss_n40C_1v60`、`ff_n40C_1v95`、`ff_100C_1v95`）中最差的 setup slack ≥ 0。
  25| - hold 只记录，不作判据。
  26| 
  27| ## 5. RTL 的要求
  28| 
  29| 提交的 RTL 必须满足下表全部规则。"合同要求"来自合同；"阶段 B 附加提交格式限制"不是合同条款，是本阶段对提交格式的额外限制。任何一条不满足，候选都不进入评估；被附加提交格式限制拒绝的候选，结果记为"违反阶段 B 附加提交格式限制"，不记为"违反合同"。
  30| 
  31| | 编号 | 规则 | 性质和来源 |
  32| |---|---|---|
  33| | G1 | 模块名 `dot4sat`，端口集合与合同第 1 节完全一致：名称、方向、位宽，不多不少（`clk`、`rst`、`in_valid`、`in_a[63:0]`、`in_b[63:0]`、`out_valid`、`out_data[31:0]`） | 合同要求（第 1 节） |
  34| | G2 | 不使用 plusarg、文件读写、shell、波形转储类系统任务，不用 `` `include `` | 合同要求（第 1 节）；`grade.py` 的 lint 也会再查 |
  35| | G3 | 文件中只有一个模块 | 阶段 B 附加提交格式限制：冻结的综合配方不展平层次，`grade.py` 只在单模块的基线和自检夹具上验证过 |
  36| | G4 | 不用 `parameter`（可以用 `localparam`） | 阶段 B 附加提交格式限制：合同只禁止用参数改变功能；这里直接禁止，免得判断"是否改变功能" |
  37| | G5 | 不用任何反引号编译指令（`` `define ``、`` `ifdef ``、`` `timescale `` 等） | 阶段 B 附加提交格式限制：合同只禁止用宏改变功能；`` `timescale `` 等指令可能与 TB 冲突或产生白名单之外的 warning |
  38| | G6 | 时序 always 块的事件控制恰好是 `@(posedge clk)`；组合逻辑只用连续赋值（`assign`，或像基线那样带赋值的 `wire` 声明）或 `always @*`/`always @(*)`；不用 `initial`、`#` 延时、`negedge` | 阶段 B 附加提交格式限制，对应合同第 1、2.3 节"只在 `clk` 上升沿动作、同步复位" |
  39| | G7 | 标识符 `clk`（转义形式按同一标识符处理）只出现在以下位置：模块头的端口列表；ANSI 或非 ANSI 的端口声明；在模块顶层对模块头端口 `clk` 的不带赋值的线网声明（如非 ANSI 写法中的 `wire clk;`）；G6 允许的 `posedge clk` 事件控制。作为数据、条件或表达式操作数出现即拒绝 | 阶段 B 附加提交格式限制：不把时钟用作数据或条件 |
  40| | G8 | `DECLARED_L` 在 1..3 之间 | `config/f1.cfg` 的 L_max（等于 3） |
  41| 
  42| ## 6. 提交格式
  43| 
  44| - 答复中恰好一个 verilog 代码块：以单独一行 ```` ```verilog ```` 开始，以单独一行 ```` ``` ```` 结束；内容是完整的 `dot4sat` 模块文件。
  45| - 如果给出多个代码块，只有第一个 verilog 代码块会被评估；第一个代码块不完整时，不会改用后面的代码块。
  46| - 单独一行写 `DECLARED_L = <n>`，n 是实现的延迟 L。这一行不放在代码块、引用或行内代码里，全文只写一次。评估使用的 L 以这一行为准。
  47| 
  48| ## 7. 预测表的填写规则
  49| 
  50| 预测表是一个 Markdown 表格，表头一字不差地写成下面这一行：
  51| 
  52| | id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
  53| 
  54| 各字段的取值：
  55| 
  56| | 字段 | 取值 |
  57| |---|---|
  58| | `id` | 自己编号，如 P1、P2；第 2 轮可以写 `same_as=<第 1 轮编号>` 表示沿用 |
  59| | `action` | 对应 RTL 中的哪项改动（自由文字） |
  60| | `metric` | `slack`、`area`、`L`、`function` 之一 |
  61| | `check` | `metric` 为 `slack` 时必填：`setup` 或 `hold` |
  62| | `corner` | `all`（6 个 std 点中最差的那个）或某个 corner 名（见第 4 节） |
  63| | `category` | `global`、`in2reg`、`reg2reg`、`reg2out` 之一 |
  64| | `value_kind` | `absolute`（候选的数值本身）或 `delta`（候选减 F1 基线） |
  65| | `direction` | 改善 / 退化 / 不变 / 未知（一律相对 F1 基线，两轮都是） |
  66| | `low`、`high`、`unit` | 数值范围；没有依据写"未知"；只写一端时另一端写"未知" |
  67| | `point` | 点估计（如有），与范围分开写 |
  68| | `basis` | 依据，引用"文件名:行号" |
  69| 
  70| 补充说明：
  71| 
  72| - 比较基准一律相对 F1 基线。
  73| - 没有依据的数值写"未知"，不强求给数。
  74| - 每行保留 `id`、`metric`，并填写适用的 `action`、`basis`。`metric` 为 `L` 时，数值和判定字段只填整数 `point`；为 `function` 时只填 `point` = `pass` 或 `fail`；这两类的 `check`、`corner`、`category`、`value_kind`、`direction`、`low`、`high`、`unit` 留空。
  75| - `function` 的实际结果取 RTL 仿真和门级功能仿真：两者都通过为 `pass`，任一失败为 `fail`，其他情况为无结果。
  76| - `category`：`global` 指不分类别、该 corner 所有路径中最差的一条（对应 `slack_summary.tsv` 的 WS 行）；`in2reg` 为输入到寄存器，`reg2reg` 为寄存器到寄存器，`reg2out` 为寄存器到输出（对应 CAT 行）。
  77| - `unit`：slack 写 `ns`，面积写 `µm²`。
  78| - 每行只写一项预测；同一个 `id` 不重复使用。
  79| 
  80| ## 8. 评估方式
  81| 
  82| - 评估用冻结的流程：RTL 仿真、门级功能仿真、综合、6 个 std 点的 STA。STA 的分析条件同 `context.md`（综合后、理想时钟、连线负载只计引脚电容）。
  83| - 本阶段不能调用工具或查询，也不提供网表。原样材料中关于查询的说明属于阶段 A。
=== 文件结束：constraints.md ===

=== 文件：contract_excerpt.md（共 69 行）===
   1| ## 1. 接口
   2| 
   3| 模块名 `dot4sat`。单时钟，只在 `clk` 上升沿动作。
   4| 
   5| | 端口 | 方向 | 位宽 | 说明 |
   6| |---|---|---|---|
   7| | `clk` | 入 | 1 | |
   8| | `rst` | 入 | 1 | 同步复位，高有效 |
   9| | `in_valid` | 入 | 1 | |
  10| | `in_a`、`in_b` | 入 | 64 | 第 i 路（i = 0..3）为 `in_a[16*i +: 16]`、`in_b[16*i +: 16]`，各自按 16 位二进制补码解释 |
  11| | `out_valid` | 出 | 1 | |
  12| | `out_data` | 出 | 32 | 32 位二进制补码 |
  13| 
  14| 实现不得通过参数、宏或 plusarg 改变上述功能。DUT 不能向 TB 提供"期望延迟"。
  15| 
  16| ## 2. 时序与交易规则
  17| 
  18| ### 2.1 记号
  19| 
  20| - `R_n`：第 n 个上升沿。`F_n`：紧随 `R_n` 之后、先于 `R_(n+1)` 的下降沿。
  21| - `I_n`：DUT 在 `R_n` 采样到的输入，记为 `rst[n]`、`valid[n]`、`a[n]`、`b[n]`。这里用方括号下标表示"第 n 个边沿采样到的值"，`rst[n]` 不是低有效复位 `rst_n`。
  22| - `O_k`：TB 在 `F_(k−1)` 读到的输出（`out_valid`、`out_data`）。
  23| 
  24| 在 `F_n` 这个时刻，TB **先**读取并检查当前输出（即 `O_(n+1)`），**再**驱动供 `R_(n+1)` 采样的下一拍输入。下降沿读数只是功能仿真的采样约定，不表示 STA 使用半周期路径。
  25| 
  26| ### 2.2 延迟 L
  27| 
  28| 延迟为 L 的实现：交易 `I_n` 在 `R_(n+L−1)` 之后形成寄存输出，在 `F_(n+L−1)` 被读到，记为 `O_(n+L)`。基线 L=1：输入经组合逻辑在 `R_n` 打入输出寄存器，在 `F_n` 被读到，即 `O_(n+1)`。
  29| 
  30| | | `R_n` | `R_(n+1)` … `R_(n+L−1)` | `F_(n+L−1)` |
  31| |---|---|---|---|
  32| | 输入 | DUT 采样 `I_n` | — | — |
  33| | valid | 进入第 1 级 | 逐级传递 | — |
  34| | 输出 | — | — | TB 读到 `O_(n+L)`：`out_valid=1`，`out_data = f(a[n], b[n])` |
  35| 
  36| ### 2.3 期望值
  37| 
  38| - `O_k.valid = valid[k−L] AND（对所有 j ∈ [k−L, k−1]，rst[j] = 0）`。如果 `k−L` 早于第一个输入，期望 valid 为 0。
  39| - 期望 valid 为 1 时，还要求 `O_k.data = f(a[k−L], b[k−L])`，f 的定义见第 3.1 节。
  40| - 每个 `R_j` 上，同步复位的优先级高于接收新交易，并且清空所有在途的 valid。
  41| 
  42| 几个边界情况：
  43| - **L=1**：`O_(n+1).valid = valid[n] AND NOT rst[n]`。
  44| - **复位恰好在 `R_(n+L−1)`**：交易 n 被清掉，`O_(n+L).valid` 必须为 0。
  45| - **复位恰好在 `R_(n+L)`**：`O_(n+L)` 已经在之前的下降沿读完，这次复位不会追溯取消已经交付的输出，它影响的是之后的观测。
  46| 
  47| 上面的公式已经隐含了以下要求：每拍都能接收新交易，没有停顿；气泡随数据一起流动；交易不能丢失、重复或乱序，也不能多出输出。
  48| 
  49| ### 2.4 复位、初始化与 X/Z
  50| 
  51| - 数据寄存器可以不复位。期望 valid 为 0 的观测点，不检查 `out_data`。
  52| - TB 在第一个采样边沿之前就把 `rst` 置为已知的 1，并至少保持 4 个上升沿。设第一个采样到 `rst=1` 的边沿为 `R_j`，从 `F_j` 开始，每个观测点都要检查。
  53| - 每个观测点上，`out_valid` 必须是确定的 0 或 1（不能是 X 或 Z），并且与期望值严格一致。期望 valid 为 1 时，`out_data` 出现任何 X/Z 或数值不等，都判失败。必须用四态比较（例如 `!==`），不能用可能把 X 当成"条件不成立"的普通比较代替。
  54| - 测试向量里的 `rst`、`in_valid` 以及有效交易的数据，都必须是已知值。本合同不要求 DUT 对未知输入给出有定义的结果。
  55| 
  56| ### 2.5 L 的配置
  57| 
  58| - 每个实现的 L 写在 `config/impl.<name>.cfg` 里，TB 通过 plusarg 读入。每个实现的 L 固定，不随输入变化。
  59| - L 缺失、不是整数、超出允许范围，或与已审阅过的配置不一致，都必须报错，不能静默使用默认值。允许范围在 F1 之前是 1–3，F1 之后是 1–L_max。
  60| - 候选与基线只要求交易级等价，不要求逐周期等价。
  61| 
  62| ### 3.1 参考函数
  63| 
  64| 1. 把每一路的 16 位比特模式解码为有符号整数：a_i、b_i ∈ [−32768, 32767]。
  65| 2. 用任意精度整数计算 s = Σ a_i·b_i。s 的范围是 [−4294836224, 4294967296]，需要 34 位有符号数才能表示。
  66| 3. y = clamp(s, −2^31, 2^31−1)。
  67| 4. 把 y 编码为 32 位二进制补码，再与 `out_data` 比较。
  68| 
  69| 中间步骤不得截断，也不得提前饱和。参考模型要独立编写，不能照搬 RTL 的表达式。
=== 文件结束：contract_excerpt.md ===

=== 文件：context.md（共 29 行）===
   1| ## 1. 接口
   2| 
   3| 模块名 `dot4sat`。单时钟，只在 `clk` 上升沿动作。
   4| 
   5| | 端口 | 方向 | 位宽 | 说明 |
   6| |---|---|---|---|
   7| | `clk` | 入 | 1 | |
   8| | `rst` | 入 | 1 | 同步复位，高有效 |
   9| | `in_valid` | 入 | 1 | |
  10| | `in_a`、`in_b` | 入 | 64 | 第 i 路（i = 0..3）为 `in_a[16*i +: 16]`、`in_b[16*i +: 16]`，各自按 16 位二进制补码解释 |
  11| | `out_valid` | 出 | 1 | |
  12| | `out_data` | 出 | 32 | 32 位二进制补码 |
  13| 
  14| 实现不得通过参数、宏或 plusarg 改变上述功能。DUT 不能向 TB 提供"期望延迟"。
  15| 
  16| ## 分析条件（只说明条件和限制，不含对任何路径的分析）
  17| 
  18| - 分析对象：上面接口描述的 `dot4sat` 模块经综合得到的门级网表。这是基线实现：只在输出端寄存，延迟 L = 1。延迟 L 的定义见合同第 2.2 节：第 n 个上升沿采样到的交易，在第 n+L−1 个上升沿打入输出寄存器；L = 1 时，输入经组合逻辑，在采样它的那个上升沿打入输出寄存器。
  19| - 分析工具：OpenSTA 3.1.0。这个版本用 scene（场景）组织 corner：`report_checks`、`find_timing_paths` 用 `-scenes` 选择场景（缩写 `-scene` 也可以用）；`report_wns`、`report_tns`、`report_worst_slack` 没有选择场景的选项。
  20| - 分析模型：综合后分析；理想时钟（时钟延迟、uncertainty、transition 都为 0）；不读取寄生参数，连线负载只计引脚电容。
  21| - 工艺库：Sky130 HD（`sky130_fd_sc_hd`），共 6 个 PVT 点：`tt_025C_1v80`、`tt_100C_1v80`、`ss_100C_1v60`、`ss_n40C_1v60`、`ff_n40C_1v95`、`ff_100C_1v95`。
  22| - 输入约束：数据和控制输入（`in_a`、`in_b`、`in_valid`、`rst`）由 `sky130_fd_sc_hd__buf_2`（A→X）驱动，输入 transition 为 0；输入延迟 max 为 0.2T，min 为 0。
  23| - 输出约束：输出延迟 max 为 0.2T，min 为 0；输出负载为 C_load。约束原文见 `case01_sdc.tcl`，取值见 `values.txt`。
  24| - 综合配方：固定的专用 Yosys/ABC 命令序列，没有时钟目标和 IO 目标，不包含物理层面的时序修复。
  25| - 综合网表存在，但没有提供给你。你可以在"下一步查询"中提出针对网表的 OpenSTA 查询。
  26| - `path_report.rpt` 是下面这条命令的输出，内容是 `ss_n40C_1v60` 下"输入到寄存器"这一类的 setup 路径。按默认设置，`report_checks` 只报告 slack 最差的一条：
  27|   `report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4`
  28| - 时钟周期 T 的来历：T 是按"基线最差 setup slack 约为周期的 −15%"校准得到的固定值。修改建议不得改变 T 或任何约束；查询中可以提出改变周期或约束的对照分析，其结果只作对照。
  29| - 修改建议必须满足的限制：延迟 L 不超过 3；每个时钟周期都能接收一笔新交易；接口和 IO 约束不变；面积不超过基线的 1.25 倍。
=== 文件结束：context.md ===

=== 文件：path_report.rpt（共 102 行）===
   1| Startpoint: in_b[2] (input port clocked by clk)
   2| Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
   3| Path Group: clk
   4| Path Type: max
   5| Corner: ss_n40C_1v60
   6| 
   7| Fanout       Cap      Slew     Delay      Time   Description
   8| -------------------------------------------------------------------------------------
   9|                     0.0000    0.0000    0.0000   clock clk (rise edge)
  10|                               0.0000    0.0000   clock network delay (ideal)
  11|                               5.5820    5.5820 ^ input external delay
  12|     19    0.0415    0.4338    0.3091    5.8911 ^ in_b[2] (in)
  13|                     0.4338    0.0000    5.8911 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
  14|      2    0.0046    0.1123    0.2453    6.1365 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
  15|                     0.1123    0.0000    6.1365 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
  16|      2    0.0054    0.1199    0.9804    7.1168 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
  17|                     0.1199    0.0000    7.1168 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
  18|      3    0.0110    0.6492    0.6267    7.7436 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
  19|                     0.6492    0.0000    7.7436 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
  20|      2    0.0063    0.1268    1.0379    8.7814 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
  21|                     0.1268    0.0000    8.7814 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
  22|      2    0.0060    0.1002    0.2727    9.0542 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
  23|                     0.1002    0.0000    9.0542 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
  24|      3    0.0113    0.6618    0.6601    9.7142 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
  25|                     0.6618    0.0000    9.7142 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
  26|      2    0.0090    0.1536    1.0917   10.8059 v _11186_/X (sky130_fd_sc_hd__xor3_1)
  27|                     0.1536    0.0000   10.8059 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
  28|      2    0.0061    0.1254    0.9265   11.7324 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
  29|                     0.1254    0.0000   11.7324 v _11257_/B (sky130_fd_sc_hd__xor2_1)
  30|      2    0.0063    0.3752    0.3997   12.1321 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
  31|                     0.3752    0.0000   12.1321 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
  32|      2    0.0073    0.1401    0.7300   12.8620 v _11302_/X (sky130_fd_sc_hd__xor3_1)
  33|                     0.1401    0.0000   12.8620 v _11306_/B (sky130_fd_sc_hd__maj3_1)
  34|      2    0.0073    0.1599    0.9433   13.8053 v _11306_/X (sky130_fd_sc_hd__maj3_1)
  35|                     0.1599    0.0000   13.8053 v _11338_/B (sky130_fd_sc_hd__xor3_1)
  36|      2    0.0061    0.1307    0.9799   14.7852 v _11338_/X (sky130_fd_sc_hd__xor3_1)
  37|                     0.1307    0.0000   14.7852 v _11340_/B (sky130_fd_sc_hd__xor2_1)
  38|      2    0.0065    0.3820    0.4077   15.1930 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
  39|                     0.3820    0.0000   15.1930 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
  40|      2    0.0067    0.1299    0.2608   15.4538 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
  41|                     0.1299    0.0000   15.4538 v _11418_/C (sky130_fd_sc_hd__maj3_1)
  42|      2    0.0055    0.1444    0.9285   16.3823 v _11418_/X (sky130_fd_sc_hd__maj3_1)
  43|                     0.1444    0.0000   16.3823 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
  44|      2    0.0063    0.4984    0.5449   16.9272 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
  45|                     0.4984    0.0000   16.9272 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
  46|      2    0.0065    0.1750    0.5349   17.4621 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
  47|                     0.1750    0.0000   17.4621 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
  48|      2    0.0067    0.1381    0.1799   17.6420 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
  49|                     0.1381    0.0000   17.6420 v _11423_/C (sky130_fd_sc_hd__maj3_1)
  50|      2    0.0067    0.1552    0.9453   18.5873 v _11423_/X (sky130_fd_sc_hd__maj3_1)
  51|                     0.1552    0.0000   18.5873 v _11424_/C (sky130_fd_sc_hd__maj3_1)
  52|      2    0.0056    0.1456    0.9406   19.5278 v _11424_/X (sky130_fd_sc_hd__maj3_1)
  53|                     0.1456    0.0000   19.5278 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
  54|      2    0.0065    0.5098    0.5289   20.0567 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
  55|                     0.5098    0.0000   20.0567 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
  56|      2    0.0069    0.1331    0.3197   20.3764 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
  57|                     0.1331    0.0000   20.3764 v _11428_/C (sky130_fd_sc_hd__maj3_1)
  58|      2    0.0069    0.1564    0.9447   21.3211 v _11428_/X (sky130_fd_sc_hd__maj3_1)
  59|                     0.1564    0.0000   21.3211 v _11429_/C (sky130_fd_sc_hd__maj3_1)
  60|      2    0.0061    0.1494    0.9456   22.2667 v _11429_/X (sky130_fd_sc_hd__maj3_1)
  61|                     0.1494    0.0000   22.2667 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
  62|      2    0.0065    0.3918    0.4391   22.7059 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
  63|                     0.3918    0.0000   22.7059 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
  64|      3    0.0050    0.1137    0.2517   22.9576 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
  65|                     0.1137    0.0000   22.9576 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
  66|      2    0.0065    0.5099    0.5119   23.4695 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
  67|                     0.5099    0.0000   23.4695 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
  68|      3    0.0084    0.1479    0.3357   23.8052 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
  69|                     0.1479    0.0000   23.8052 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
  70|      3    0.0088    0.8527    0.8462   24.6514 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
  71|                     0.8527    0.0000   24.6514 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
  72|      3    0.0058    0.1806    0.4326   25.0840 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
  73|                     0.1806    0.0000   25.0840 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
  74|      3    0.0068    1.0230    1.0241   26.1081 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
  75|                     1.0230    0.0000   26.1081 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
  76|      3    0.0042    0.1761    0.4919   26.6000 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
  77|                     0.1761    0.0000   26.6000 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
  78|      2    0.0045    0.7912    0.8376   27.4376 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
  79|                     0.7912    0.0000   27.4376 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
  80|      1    0.0041    0.1315    0.3533   27.7908 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
  81|                     0.1315    0.0000   27.7908 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
  82|      2    0.0037    0.0814    0.2543   28.0452 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
  83|                     0.0814    0.0000   28.0452 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
  84|     31    0.0511    3.2455    2.6362   30.6814 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
  85|                     3.2455    0.0000   30.6814 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
  86|      1    0.0015    0.3761    0.8625   31.5439 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
  87|                     0.3761    0.0000   31.5439 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
  88|                                        31.5439   data arrival time
  89| 
  90|                     0.0000   27.9100   27.9100   clock clk (rise edge)
  91|                               0.0000   27.9100   clock network delay (ideal)
  92|                               0.0000   27.9100   clock reconvergence pessimism
  93|                                        27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  94|                              -0.5559   27.3541   library setup time
  95|                                        27.3541   data required time
  96| -------------------------------------------------------------------------------------
  97|                                        27.3541   data required time
  98|                                       -31.5439   data arrival time
  99| -------------------------------------------------------------------------------------
 100|                                        -4.1897   slack (VIOLATED)
 101| 
 102| 
=== 文件结束：path_report.rpt ===

=== 文件：case01_sdc.tcl（共 19 行）===
   1| # CASE-01 SDC (spec 4.3). Expects Tcl variables T (ns) and C_load (pF) to be set by the caller.
   2| # Must be sourced AFTER sky130_define_scenes: set_load issued before define_scene is silently cleared
   3| # (docs/env/TOOL_ISSUES.md TOOL-012).
   4| create_clock -name clk -period $T -waveform [list 0 [expr {$T / 2.0}]] [get_ports clk]
   5| set_clock_uncertainty -setup 0 [get_clocks clk]
   6| set_clock_uncertainty -hold  0 [get_clocks clk]
   7| set_clock_transition 0 [get_clocks clk]
   8| set_clock_latency -source 0 [get_clocks clk]
   9| set_clock_latency 0 [get_clocks clk]
  10| 
  11| set ins  [get_ports {in_a[*] in_b[*] in_valid rst}]
  12| set outs [get_ports {out_data[*] out_valid}]
  13| set_input_delay  -clock clk -max [expr {0.2 * $T}] $ins
  14| set_input_delay  -clock clk -min 0 $ins
  15| set_driving_cell -lib_cell sky130_fd_sc_hd__buf_2 -from_pin A -pin X \
  16|                  -input_transition_rise 0 -input_transition_fall 0 $ins
  17| set_output_delay -clock clk -max [expr {0.2 * $T}] $outs
  18| set_output_delay -clock clk -min 0 $outs
  19| set_load -pin_load $C_load $outs
=== 文件结束：case01_sdc.tcl ===

=== 文件：values.txt（共 2 行）===
   1| T_ns = 27.91
   2| C_load_pF = 0.0024
=== 文件结束：values.txt ===

=== 文件：slack_summary.tsv（共 58 行）===
   1| # slack_summary.tsv：F1 基线运行 sta/sta_results.tsv 中 WS、CAT、TOPO 三类原始行，按原顺序保留，字段之间用制表符分隔。
   2| # WS   <corner> <max|min> <slack>：该 corner 的最差 slack。max 对应 setup 检查，min 对应 hold 检查。
   3| # CAT  <corner> <类别> <max|min> <slack> <起点> <终点>：该 corner 下这一类路径中最差的一条。
   4| #      类别：in2reg = 输入到寄存器，reg2reg = 寄存器到寄存器，reg2out = 寄存器到输出。
   5| #      slack 写作 NONE 时，表示拓扑中不存在这一类路径，此时没有起点和终点。
   6| # TOPO <类别> <数目>：在结构上能到达该类终点的起点数目。
   7| # slack 与 path_report.rpt 使用同一时间单位。min（hold）一栏是理想时钟、综合后模型下的值。
   8| TOPO	in2reg	130
   9| TOPO	reg2reg	0
  10| TOPO	reg2out	33
  11| WS	tt_025C_1v80	max	11.185458209594348
  12| WS	tt_025C_1v80	min	0.09305387279663745
  13| CAT	tt_025C_1v80	in2reg	max	11.185458	in_b[35]	_12026_/D
  14| CAT	tt_025C_1v80	in2reg	min	0.093054	rst	_12058_/D
  15| CAT	tt_025C_1v80	reg2reg	max	NONE
  16| CAT	tt_025C_1v80	reg2reg	min	NONE
  17| CAT	tt_025C_1v80	reg2out	max	22.047794	_12026_/Q	out_data[0]
  18| CAT	tt_025C_1v80	reg2out	min	0.272520	_12026_/Q	out_data[0]
  19| WS	tt_100C_1v80	max	11.317221258240215
  20| WS	tt_100C_1v80	min	0.08983023607005908
  21| CAT	tt_100C_1v80	in2reg	max	11.317222	in_b[35]	_12026_/D
  22| CAT	tt_100C_1v80	in2reg	min	0.089830	rst	_12058_/D
  23| CAT	tt_100C_1v80	reg2reg	max	NONE
  24| CAT	tt_100C_1v80	reg2reg	min	NONE
  25| CAT	tt_100C_1v80	reg2out	max	22.045441	_12026_/Q	out_data[0]
  26| CAT	tt_100C_1v80	reg2out	min	0.278449	_12026_/Q	out_data[0]
  27| WS	ss_100C_1v60	max	-0.687277809672019
  28| WS	ss_100C_1v60	min	0.18567888030452087
  29| CAT	ss_100C_1v60	in2reg	max	-0.687278	in_b[35]	_12026_/D
  30| CAT	ss_100C_1v60	in2reg	min	0.185679	rst	_12058_/D
  31| CAT	ss_100C_1v60	reg2reg	max	NONE
  32| CAT	ss_100C_1v60	reg2reg	min	NONE
  33| CAT	ss_100C_1v60	reg2out	max	21.742086	_12026_/Q	out_data[0]
  34| CAT	ss_100C_1v60	reg2out	min	0.538051	_12026_/Q	out_data[0]
  35| WS	ss_n40C_1v60	max	-4.189726018044011
  36| WS	ss_n40C_1v60	min	0.18500412836443383
  37| CAT	ss_n40C_1v60	in2reg	max	-4.189726	in_b[2]	_12026_/D
  38| CAT	ss_n40C_1v60	in2reg	min	0.185004	rst	_12058_/D
  39| CAT	ss_n40C_1v60	reg2reg	max	NONE
  40| CAT	ss_n40C_1v60	reg2reg	min	NONE
  41| CAT	ss_n40C_1v60	reg2out	max	21.692432	_12026_/Q	out_data[0]
  42| CAT	ss_n40C_1v60	reg2out	min	0.548442	_12026_/Q	out_data[0]
  43| WS	ff_n40C_1v95	max	15.871505448031069
  44| WS	ff_n40C_1v95	min	0.06347266641938298
  45| CAT	ff_n40C_1v95	in2reg	max	15.871506	in_b[2]	_12026_/D
  46| CAT	ff_n40C_1v95	in2reg	min	0.063473	rst	_12058_/D
  47| CAT	ff_n40C_1v95	reg2reg	max	NONE
  48| CAT	ff_n40C_1v95	reg2reg	min	NONE
  49| CAT	ff_n40C_1v95	reg2out	max	22.154276	_12026_/Q	out_data[0]
  50| CAT	ff_n40C_1v95	reg2out	min	0.173251	_12026_/Q	out_data[0]
  51| WS	ff_100C_1v95	max	15.894228605363333
  52| WS	ff_100C_1v95	min	0.059112952317363035
  53| CAT	ff_100C_1v95	in2reg	max	15.894229	in_b[2]	_12026_/D
  54| CAT	ff_100C_1v95	in2reg	min	0.059113	rst	_12058_/D
  55| CAT	ff_100C_1v95	reg2reg	max	NONE
  56| CAT	ff_100C_1v95	reg2reg	min	NONE
  57| CAT	ff_100C_1v95	reg2out	max	22.143078	_12026_/Q	out_data[0]
  58| CAT	ff_100C_1v95	reg2out	min	0.179844	_12026_/Q	out_data[0]
=== 文件结束：slack_summary.tsv ===

=== 文件：dot4sat.v（共 43 行）===
   1| // CASE-01 baseline (spec 1, D1): four signed 16x16 products summed exactly, saturated to 32-bit signed.
   2| // Output registered only; latency L = 1. Synchronous active-high reset clears out_valid.
   3| // out_data is not reset and has no enable (spec 2.4: data is don't-care when out_valid = 0).
   4| module dot4sat (
   5|     input  wire        clk,
   6|     input  wire        rst,
   7|     input  wire        in_valid,
   8|     input  wire [63:0] in_a,
   9|     input  wire [63:0] in_b,
  10|     output reg         out_valid,
  11|     output reg  [31:0] out_data
  12| );
  13| 
  14|     wire signed [15:0] a0 = in_a[15:0];
  15|     wire signed [15:0] a1 = in_a[31:16];
  16|     wire signed [15:0] a2 = in_a[47:32];
  17|     wire signed [15:0] a3 = in_a[63:48];
  18|     wire signed [15:0] b0 = in_b[15:0];
  19|     wire signed [15:0] b1 = in_b[31:16];
  20|     wire signed [15:0] b2 = in_b[47:32];
  21|     wire signed [15:0] b3 = in_b[63:48];
  22| 
  23|     wire signed [31:0] p0 = a0 * b0;
  24|     wire signed [31:0] p1 = a1 * b1;
  25|     wire signed [31:0] p2 = a2 * b2;
  26|     wire signed [31:0] p3 = a3 * b3;
  27| 
  28|     // full range is [-4294836224, 4294967296]: needs 34 signed bits
  29|     wire signed [33:0] sum = p0 + p1 + p2 + p3;
  30| 
  31|     localparam signed [33:0] SMAX = 34'sd2147483647;
  32|     localparam signed [33:0] SMIN = -34'sd2147483648;
  33| 
  34|     wire [31:0] sat = (sum > SMAX) ? 32'h7FFF_FFFF :
  35|                       (sum < SMIN) ? 32'h8000_0000 : sum[31:0];
  36| 
  37|     always @(posedge clk) begin
  38|         if (rst) out_valid <= 1'b0;
  39|         else     out_valid <= in_valid;
  40|         out_data <= sat;
  41|     end
  42| 
  43| endmodule
=== 文件结束：dot4sat.v ===

下面是你自己在阶段 A 第 2 轮的答复，已按行编号。引用时文件名写 `阶段A答复.md`。

=== 文件：阶段A答复.md（共 612 行）===
   1| ## 一、报告事实
   2| 
   3| > 说明：原题材料用“文件名:行号”引用；本轮新增的查询结果没有行号，以下用“查询 Bn 输出”定位。
   4| 
   5| ### 1. 已确认的基线结构和约束
   6| 
   7| - 基线在同一个时钟周期内完成四个有符号 16×16 乘法、34 位精确求和以及 32 位饱和选择，只寄存输出，L=1（`dot4sat.v:23-40`，`context.md:18`）。
   8| - `out_valid` 受同步高有效复位控制；`out_data` 无复位、无使能（`dot4sat.v:37-41`）。
   9| - 时钟周期固定为 27.91 ns，而且这个周期是按“基线最差 setup slack 约为周期的 −15%”校准出来的（`values.txt:1`，`context.md:28`）。因此当前违例不是偶然约束错误，而是该基线在既定校准条件下预期处于违例状态。
  10| - 输入 max delay 为 0.2T，即 5.582 ns；输入 min delay 为 0（`case01_sdc.tcl:13-14`，`path_report.rpt:11`）。
  11| - 分析使用理想时钟、不读寄生参数，连线负载只计引脚电容（`context.md:20`）。
  12| 
  13| ### 2. 最差 setup 路径及时间预算
  14| 
  15| - 最差路径为 `in_b[2] → _12026_/D`，corner 为 `ss_n40C_1v60`（`path_report.rpt:1-5`）。
  16| - 数据到达时间为 31.5439 ns，要求时间为 27.3541 ns，slack 为 −4.1897 ns（`path_report.rpt:87-100`）。
  17| - 从输入外部延迟之后到触发器 D 的内部路径耗时为：
  18| 
  19|   `31.5439 − 5.5820 = 25.9619 ns`。
  20| 
  21| - 扣除输入外部延迟后，该路径可用时间为：
  22| 
  23|   `27.3541 − 5.5820 = 21.7721 ns`。
  24| 
  25|   两者差值正好约为当前违例量 4.1898 ns。
  26| 
  27| ### 3. 第 1 轮中的若干判断已被查询确认
  28| 
  29| - **`_12026_` 的身份已确认。**  
  30|   查询 B7 的 `report_instance` 输出显示：
  31|   - `_12026_` 是 `sky130_fd_sc_hd__dfxtp_1`；
  32|   - 其 Q 输出直接连接到 `out_data[0]`；
  33|   - D 输入连接到内部网络 `_00030_`。  
  34|   因此第 1 轮“`_12026_` 很可能是 `out_data[0]` 触发器”的判断现在可以改为确认事实。
  35| 
  36| - **基线确实不存在 reg2reg 路径。**  
  37|   查询 B4 在全部 6 个 corner 下均返回 `No paths found.`，与原始拓扑摘要中的 reg2reg 数目为 0 一致（`slack_summary.tsv:9`）。
  38| 
  39| - **reg2out 不是当前瓶颈。**  
  40|   查询 B4 和 B9 显示，在 `ss_n40C_1v60` 下，`_12026_/CLK → out_data[0]` 的到达时间约为 0.6356 ns，reg2out slack 为 21.6924 ns。原摘要也给出 21.692432 ns 的正 slack（`slack_summary.tsv:41-42`）。
  41| 
  42| ### 4. 各 corner 的 in2reg 最差 setup 结果
  43| 
  44| 查询 B4 给出的紧凑结果与原摘要一致：
  45| 
  46| | Corner | Actual | Required | Slack |
  47| |---|---:|---:|---:|
  48| | `tt_025C_1v80` | 16.522688 | 27.708145 | +11.185458 |
  49| | `tt_100C_1v80` | 16.404186 | 27.721409 | +11.317222 |
  50| | `ss_100C_1v60` | 28.161348 | 27.474070 | −0.687278 |
  51| | `ss_n40C_1v60` | 31.543875 | 27.354149 | −4.189726 |
  52| | `ff_n40C_1v95` | 11.924675 | 27.796181 | +15.871506 |
  53| | `ff_100C_1v95` | 11.910374 | 27.804602 | +15.894229 |
  54| 
  55| 因此，“只有两个低电压 slow corner 违例”得到确认（另见 `slack_summary.tsv:27-42`）。
  56| 
  57| 但第 1 轮中隐含的“延迟应随 PVT 严格单调变化”判断需要修正：`tt_100C_1v80` 的 actual delay 为 16.404186 ns，反而小于 `tt_025C_1v80` 的 16.522688 ns。可以确认的是**低电压 slow corner 最关键**，不能声称所有相邻 PVT 点之间都单调变化。
  58| 
  59| ### 5. 输入延迟贡献已被对照查询精确确认
  60| 
  61| 查询 B10 在单独会话中把输入 max delay 临时改为 0。结果显示：
  62| 
  63| - 同一条 `in_b[2] → _12026_/D` 路径的内部逐级延迟不变；
  64| - data arrival time 从 31.5439 ns 变为 25.9619 ns；
  65| - slack 从 −4.1897 ns 变为 **+1.3923 ns**。
  66| 
  67| 变化量正好等于 5.5820 ns 的输入 max delay。因此第 1 轮的“0.2T 输入延迟与 L=1 结构叠加”判断得到确认。
  68| 
  69| 同时也要修正其表述：0.2T 输入延迟不是唯一问题。即使输入外部延迟为 0，整条组合逻辑仍消耗 25.9619 ns，只留下 1.3923 ns 余量，约占可用窗口的 94.9%。
  70| 
  71| ### 6. `_11509_/Y` 是共同结构热点，但其 RTL 功能仍不确定
  72| 
  73| - `_11509_/Y` 的扇出为 31，单元延迟为 2.6362 ns，输出 slew 为 3.2455 ns；下一级 `_11512_` 又贡献 0.8625 ns（`path_report.rpt:84-86`）。
  74| - 查询 B8 确认 `_11509_` 是 `sky130_fd_sc_hd__o21ai_0`，输出网络名为 `_05587_`，但只给出了网络名，没有给出 RTL 功能归属。
  75| - 查询 B2 可见的最差路径和输出末尾的近最差路径都经过 `_11509_/Y`；两条不同起点的路径还在 `_11302_/X` 后汇合成相同的后缀。
  76| - 查询 B6 加了 `-through _11509_/Y` 后，仍返回与 B2 同量级、同为 5103 行的报告，首尾示例也均经过该网络。
  77| 
  78| 这支持“`_11509_/Y` 覆盖了最差路径集中的大量路径”的判断。不过由于输出被截断，不能精确声称全部 50 条路径都经过它；也不能仅凭 fanout=31 断定它就是饱和选择信号。
  79| 
  80| ### 7. 高扇出热点不是唯一充分原因
  81| 
  82| 在 `_11509_` 的 A1 输入处，数据已经在 28.0452 ns 到达（`path_report.rpt:83`），而 data required time 是 27.3541 ns。
  83| 
  84| 因此，即使假设 `_11509_` 和 `_11512_` 两级延迟完全消失，仍然大约违例：
  85| 
  86| `28.0452 − 27.3541 = 0.6911 ns`。
  87| 
  88| 所以局部缓冲、复制或饱和选择优化可能很重要，但不能只凭这两级就解释全部 −4.1897 ns 违例。
  89| 
  90| ### 8. 面积证据仍缺失
  91| 
  92| - 第 1 轮提出的 `report_cell_usage` 和 `report_design_area` 在当前 OpenSTA 环境中都不是有效命令（查询 B12）。
  93| - 因此基线面积、触发器数量之外的单元构成、候选方案是否小于 1.25 倍面积，仍全部不确定。
  94| 
  95| ---
  96| 
  97| ## 二、原因假设
  98| 
  99| ### 假设 1：主要原因是 L=1 基线把完整算术链压在一个周期内——已基本确认
 100| 
 101| 四个乘法器、加法树和饱和选择都位于输入端口与输出寄存器之间（`dot4sat.v:23-40`）。路径报告中大量 XOR/XNOR/MAJ 和复合门也与长算术链一致（`path_report.rpt:13-86`）。
 102| 
 103| 查询 B10 进一步确认：即使把输入外部延迟清零，内部路径仍需 25.9619 ns，距离 27.3541 ns 的要求时间只剩 1.3923 ns。
 104| 
 105| **仍可推翻的方式：**
 106| 
 107| - 若完整网表映射证明这条 XOR/MAJ 长链不属于乘法、求和或饱和，而属于其他意外逻辑，则该判断被推翻。
 108| - 若候选 RTL 只做自然流水、但综合后长链并未被切断，也说明第 1 轮对结构边界的理解不正确。
 109| 
 110| ### 假设 2：0.2T 输入延迟是造成违例的直接预算因素，但不是唯一根因——已确认并修正
 111| 
 112| 查询 B10 精确显示，输入 max delay 从 5.5820 ns 改为 0 后，slack 改善完全相同，从 −4.1897 ns 变为 +1.3923 ns。
 113| 
 114| 因此：
 115| 
 116| - 输入寄存器、让算术链使用完整周期，是很有针对性的候选方案；
 117| - 但原始组合链本身已经接近一个完整周期，插入寄存器后的 clock-to-Q 和重新映射仍可能吃掉这部分余量。
 118| 
 119| **推翻方式：**
 120| 
 121| - 如果输入寄存器候选网表中，新增寄存器 clock-to-Q、Q 端负载和重新映射合计吃掉超过约 1.39 ns，则“输入寄存即可可靠收敛”的工程判断被推翻。
 122| - 如果新输入寄存器的 setup/hold 自身违例，也说明该方案不能直接接受。
 123| 
 124| ### 假设 3：`_11509_/Y` 是共同高扇出热点——结构部分得到支持，功能归属仍不确定
 125| 
 126| - 最差和近最差返回路径均经过 `_11509_/Y`。
 127| - 多条不同起点路径在 `_11302_/X` 后汇合，并共享后续 `_11509_` 后缀。
 128| - fanout=31 和一个公共饱和选择信号驱动多个输出数据 mux 的结构相符，但查询 B8 没有证明这一点。
 129| 
 130| 同时，该热点不是唯一根因：其输入端已经比要求时间晚约 0.6911 ns。
 131| 
 132| **推翻方式：**
 133| 
 134| - 若 `_11509_/Y` 的 31 个负载不是输出数据选择/mux，而是其他无关逻辑，则“饱和选择热点”判断被推翻。
 135| - 若完整未截断的前 50 条违例路径中，只有少数经过 `_11509_/Y`，则“共同热点”判断被推翻。
 136| - 若复制或寄存该网络后，重新综合的 slack 没有实质变化，也应推翻其作为主要热点的判断。
 137| 
 138| ### 假设 4：低电压 slow corner 是关键场景——确认；严格 PVT 单调性——修正
 139| 
 140| 确认部分：
 141| 
 142| - 只有 `ss_100C_1v60` 和 `ss_n40C_1v60` 违例；
 143| - `ss_n40C_1v60` 最差。
 144| 
 145| 修正部分：
 146| 
 147| - 不能声称延迟随温度或 PVT 严格单调变化，因为查询 B4 中 `tt_100C_1v80` 的 actual delay 小于 `tt_025C_1v80`。
 148| - 更准确的表述是：当前设计的时序裕量主要由低电压 slow corner 决定。
 149| 
 150| ### 假设 5：固定综合流程没有得到时序驱动的驱动强度或缓冲优化——仍不确定
 151| 
 152| 支持点：
 153| 
 154| - 综合流程没有时钟目标、IO 目标或物理层面的时序修复（`context.md:24`）。
 155| - 最差路径存在 fanout=31、驱动强度为 `_0` 的单元（`path_report.rpt:84`）。
 156| 
 157| 反对或限制点：
 158| 
 159| - 即便完全消除 `_11509_` 和 `_11512_` 的延迟，仍约有 −0.691 ns 违例。
 160| - 因此不能把全部问题归因于驱动不足或缺少缓冲；算术逻辑深度本身仍然是主要因素。
 161| 
 162| ---
 163| 
 164| ## 三、缺失的证据
 165| 
 166| 1. **`_11509_` 的完整负载与功能归属**
 167|    - 需要 `_11509_/Y` 的全部 31 个负载引脚。
 168|    - 需要确认这些负载是否分别对应 31 个输出数据位的饱和 mux。
 169|    - 查询 B8 只得到内部网络名 `_05587_`，没有功能映射。
 170| 
 171| 2. **完整、未截断的违例路径分布**
 172|    - 查询 B2/B6 返回了 5103 行，但本轮只显示首尾各 100 行。
 173|    - 仍缺少精确的违例终点数、slack 直方图，以及经过 `_11302_/X`、`_11509_/Y` 的路径比例。
 174| 
 175| 3. **自然算术边界的到达时间**
 176|    - 需要知道四个乘积、`p0+p1`、`p2+p3`、最终 `sum`、饱和标志分别何时到达。
 177|    - 没有这些数据，不能判断 L=2 的最佳切分点是输入寄存还是乘积寄存。
 178| 
 179| 4. **门级实例到 RTL 的映射**
 180|    - `_11302_` 后的公共后缀很可能属于求和/饱和，但尚未被证明。
 181|    - `_11512_`、`_11574_`、`_12052_` 等实例和输出位的关系也只部分可见。
 182| 
 183| 5. **新增输入寄存器的实际 clock-to-Q 和负载**
 184|    - 查询 B9 只给出现有输出寄存器在输出负载条件下的 CLK→输出到达时间约 0.6356 ns。
 185|    - 新增内部输入寄存器的 Q 端负载不同，不能直接把这个数当成确定值。
 186| 
 187| 6. **基线和候选方案面积**
 188|    - `report_cell_usage`、`report_design_area` 在当前环境不可用。
 189|    - 需要改用综合侧面积报告或解析 Liberty/网表。
 190| 
 191| 7. **候选流水结构的完整 setup/hold 结果**
 192|    - 新方案会产生 reg2reg 路径。
 193|    - 基线最低 hold slack 只有约 0.059 ns，新增输入寄存器后的 min-delay 路径必须单独验证。
 194| 
 195| 8. **功能等价证据**
 196|    - 所有流水方案都需要验证 `out_valid` 与新延迟严格对齐。
 197|    - 算术重写需要证明乘积、34 位求和和正负饱和边界不变。
 198| 
 199| ---
 200| 
 201| ## 四、下一步查询
 202| 
 203| ### 1. 用非弃用选项重新生成完整的违例终点摘要
 204| 
 205| ```tcl
 206| report_checks \
 207|   -from [all_inputs -no_clocks] \
 208|   -to [all_registers -data_pins] \
 209|   -path_delay max \
 210|   -scene ss_n40C_1v60 \
 211|   -slack_max 0.0 \
 212|   -sort_by_slack \
 213|   -group_path_count 1000 \
 214|   -endpoint_path_count 1000 \
 215|   -unique_paths_to_endpoint \
 216|   -format end \
 217|   -digits 6
 218| ```
 219| 
 220| 目的：用紧凑格式得到完整的违例终点列表，避免 full 报告再次被截断。
 221| 
 222| ### 2. 得到经过 `_11509_/Y` 的违例终点摘要
 223| 
 224| ```tcl
 225| report_checks \
 226|   -from [all_inputs -no_clocks] \
 227|   -to [all_registers -data_pins] \
 228|   -through [get_pins {_11509_/Y}] \
 229|   -path_delay max \
 230|   -scene ss_n40C_1v60 \
 231|   -slack_max 0.0 \
 232|   -sort_by_slack \
 233|   -group_path_count 1000 \
 234|   -endpoint_path_count 1000 \
 235|   -unique_paths_to_endpoint \
 236|   -format end \
 237|   -digits 6
 238| ```
 239| 
 240| 与查询 1 的完整端点列表比较，可精确计算共同热点覆盖率。
 241| 
 242| ### 3. 检查 `_11302_/X` 是否也是公共汇合点
 243| 
 244| ```tcl
 245| report_checks \
 246|   -from [all_inputs -no_clocks] \
 247|   -to [all_registers -data_pins] \
 248|   -through [get_pins {_11302_/X}] \
 249|   -path_delay max \
 250|   -scene ss_n40C_1v60 \
 251|   -slack_max 0.0 \
 252|   -sort_by_slack \
 253|   -group_path_count 1000 \
 254|   -endpoint_path_count 1000 \
 255|   -unique_paths_to_endpoint \
 256|   -format end \
 257|   -digits 6
 258| ```
 259| 
 260| 目的：确认共同瓶颈是否从 `_11302_` 已经开始，而不是仅发生在 `_11509_`。
 261| 
 262| ### 4. 修正后的 `_11509_/Y` 网络和负载查询
 263| 
 264| 第 1 轮中 `report_pin` 和 `report_net -connections` 不可用，应改为：
 265| 
 266| ```tcl
 267| report_instance [get_cells {_11509_}]
 268| 
 269| set net_11509_y [get_nets -of_objects [get_pins {_11509_/Y}]]
 270| report_net -verbose $net_11509_y
 271| 
 272| foreach p [get_pins -of_objects $net_11509_y] {
 273|     puts [get_full_name $p]
 274| }
 275| ```
 276| 
 277| 目的：列出驱动和全部负载，确认 fanout=31 的准确归属。
 278| 
 279| ### 5. 查看 `_11509_/Y` 的逻辑扇出终点和扇入起点
 280| 
 281| ```tcl
 282| foreach p [all_fanout -from [get_pins {_11509_/Y}] -endpoints_only] {
 283|     puts [get_full_name $p]
 284| }
 285| 
 286| foreach p [all_fanin -to [get_pins {_11509_/Y}] -startpoints_only] {
 287|     puts [get_full_name $p]
 288| }
 289| ```
 290| 
 291| 目的：
 292| 
 293| - 扇出是否主要终止于 32 个 `out_data` 寄存器；
 294| - 扇入是否覆盖四路输入乘积或饱和比较所需的数据位。
 295| 
 296| ### 6. 用紧凑格式重新查询同一条路径的全部 corner
 297| 
 298| ```tcl
 299| foreach scene [list \
 300|     tt_025C_1v80 \
 301|     tt_100C_1v80 \
 302|     ss_100C_1v60 \
 303|     ss_n40C_1v60 \
 304|     ff_n40C_1v95 \
 305|     ff_100C_1v95] {
 306| 
 307|     puts "===== $scene ====="
 308|     report_checks \
 309|       -from [get_ports {in_b[2]}] \
 310|       -to [get_pins {_12026_/D}] \
 311|       -path_delay max \
 312|       -scene $scene \
 313|       -format end \
 314|       -digits 6
 315| }
 316| ```
 317| 
 318| 目的：避免 full 报告截断，取得同一起终点的完整六 corner 数值。
 319| 
 320| ### 7. 确认其他关键实例的归属
 321| 
 322| ```tcl
 323| report_instance [get_cells {_11512_}]
 324| report_instance [get_cells {_11574_}]
 325| report_instance [get_cells {_12052_}]
 326| ```
 327| 
 328| 如果查询 1 得到其他违例终点，也应对其执行：
 329| 
 330| ```tcl
 331| report_instance [get_cells {<endpoint_cell_name>}]
 332| ```
 333| 
 334| ### 8. 面积查询
 335| 
 336| 当前 OpenSTA 中没有可用的面积命令，因此只能在 OpenSTA 中先取得单元数量：
 337| 
 338| ```tcl
 339| puts "cell_count = [llength [get_cells *]]"
 340| ```
 341| 
 342| 面积必须改用综合侧报告。例如用与综合网表匹配的 Liberty 执行 Yosys 面积统计：
 343| 
 344| ```tcl
 345| yosys -p \
 346|   "read_verilog <mapped_netlist.v>; \
 347|    hierarchy -check -top dot4sat; \
 348|    stat -liberty <sky130_hd_library.lib>"
 349| ```
 350| 
 351| 需要分别对基线和每个候选网表执行，并比较是否不超过 1.25 倍。
 352| 
 353| ### 9. 候选网表的完整 setup/hold 回归
 354| 
 355| 对每个候选网表，在原 T、原输入/输出约束和原负载下执行：
 356| 
 357| ```tcl
 358| foreach scene [list \
 359|     tt_025C_1v80 \
 360|     tt_100C_1v80 \
 361|     ss_100C_1v60 \
 362|     ss_n40C_1v60 \
 363|     ff_n40C_1v95 \
 364|     ff_100C_1v95] {
 365| 
 366|     puts "===== $scene setup ====="
 367|     report_checks \
 368|       -path_delay max \
 369|       -scene $scene \
 370|       -sort_by_slack \
 371|       -group_path_count 50 \
 372|       -endpoint_path_count 50 \
 373|       -format end \
 374|       -digits 6
 375| 
 376|     puts "===== $scene hold ====="
 377|     report_checks \
 378|       -path_delay min \
 379|       -scene $scene \
 380|       -sort_by_slack \
 381|       -group_path_count 50 \
 382|       -endpoint_path_count 50 \
 383|       -format end \
 384|       -digits 6
 385| }
 386| ```
 387| 
 388| 对流水候选还应单独列出三类路径：
 389| 
 390| ```tcl
 391| report_checks \
 392|   -from [all_inputs -no_clocks] \
 393|   -to [all_registers -data_pins] \
 394|   -path_delay max \
 395|   -scene ss_n40C_1v60 \
 396|   -format end \
 397|   -digits 6
 398| 
 399| report_checks \
 400|   -from [all_registers -clock_pins] \
 401|   -to [all_registers -data_pins] \
 402|   -path_delay max \
 403|   -scene ss_n40C_1v60 \
 404|   -format end \
 405|   -digits 6
 406| 
 407| report_checks \
 408|   -from [all_registers -clock_pins] \
 409|   -to [all_outputs] \
 410|   -path_delay max \
 411|   -scene ss_n40C_1v60 \
 412|   -format end \
 413|   -digits 6
 414| ```
 415| 
 416| ---
 417| 
 418| ## 五、可能的修改
 419| 
 420| ### 方案 A：先做无额外延迟的算术优化，但不能期望局部热点优化必然足够
 421| 
 422| #### A1. 用高三位生成饱和标志
 423| 
 424| 现有 RTL 使用两个 34 位数值比较（`dot4sat.v:31-35`）。可以改写为：
 425| 
 426| ```verilog
 427| wire pos_ovf = ~sum[33] & (|sum[32:31]);
 428| wire neg_ovf =  sum[33] & ~(&sum[32:31]);
 429| 
 430| wire [31:0] sat = pos_ovf ? 32'h7FFF_FFFF :
 431|                   neg_ovf ? 32'h8000_0000 :
 432|                             sum[31:0];
 433| ```
 434| 
 435| 这可能减少比较器和公共选择逻辑的复杂度。若 `_11509_` 最终被证明是饱和选择信号，此方案与热点直接相关。
 436| 
 437| 但新结果表明，即使 `_11509_` 和 `_11512_` 两级延迟全部消失，仍约缺 0.691 ns。因此 A1 只有在同时明显缩短其前级比较/求和逻辑时，才可能单独关闭 4.19 ns 违例。
 438| 
 439| #### A2. 显式平衡加法树
 440| 
 441| ```verilog
 442| wire signed [32:0] p0e = {p0[31], p0};
 443| wire signed [32:0] p1e = {p1[31], p1};
 444| wire signed [32:0] p2e = {p2[31], p2};
 445| wire signed [32:0] p3e = {p3[31], p3};
 446| 
 447| wire signed [32:0] s01 = p0e + p1e;
 448| wire signed [32:0] s23 = p2e + p3e;
 449| 
 450| wire signed [33:0] s01e = {s01[32], s01};
 451| wire signed [33:0] s23e = {s23[32], s23};
 452| wire signed [33:0] sum  = s01e + s23e;
 453| ```
 454| 
 455| 若当前综合结果已经把加法树平衡好，此方案收益可能很小；需要用重新综合结果验证。
 456| 
 457| ### 方案 B：输入寄存器，L=2
 458| 
 459| 这是当前证据最直接支持的流水方案：
 460| 
 461| ```verilog
 462| reg [63:0] a_q, b_q;
 463| reg        v_q;
 464| 
 465| // sat_q 由 a_q、b_q 经乘法、求和、饱和组合逻辑得到
 466| 
 467| always @(posedge clk) begin
 468|     a_q <= in_a;
 469|     b_q <= in_b;
 470| 
 471|     if (rst) begin
 472|         v_q       <= 1'b0;
 473|         out_valid <= 1'b0;
 474|     end else begin
 475|         v_q       <= in_valid;
 476|         out_valid <= v_q;
 477|     end
 478| 
 479|     out_data <= sat_q;
 480| end
 481| ```
 482| 
 483| 特点：
 484| 
 485| - 第 n 个沿寄存输入；
 486| - 第 n+1 个沿写入输出寄存器；
 487| - L=2，仍能每周期接收一笔交易；
 488| - 新增约 129 位寄存器：128 位数据加 1 位 valid 管道。
 489| 
 490| 一阶估计：
 491| 
 492| - 输入外部延迟清零后的现有路径 slack 为 +1.3923 ns；
 493| - 当前输出触发器在输出负载下的 CLK→Q/输出到达约 0.6356 ns；
 494| - 现有输入端口自身延迟约 0.3091 ns。
 495| 
 496| 如果其他逻辑不变，剩余余量的一阶估计约为：
 497| 
 498| `1.3923 − (0.6356 − 0.3091) ≈ 1.0658 ns`。
 499| 
 500| 这只是估计，不是时序收敛证明；内部 Q 负载和重新映射结果仍不确定。
 501| 
 502| ### 方案 C：乘积寄存器，L=2
 503| 
 504| ```verilog
 505| reg signed [31:0] p0_q, p1_q, p2_q, p3_q;
 506| reg               v_q;
 507| 
 508| always @(posedge clk) begin
 509|     p0_q <= p0;
 510|     p1_q <= p1;
 511|     p2_q <= p2;
 512|     p3_q <= p3;
 513| 
 514|     if (rst) begin
 515|         v_q       <= 1'b0;
 516|         out_valid <= 1'b0;
 517|     end else begin
 518|         v_q       <= in_valid;
 519|         out_valid <= v_q;
 520|     end
 521| 
 522|     out_data <= sat_from_products_q;
 523| end
 524| ```
 525| 
 526| 优点：
 527| 
 528| - 在自然算术边界切断“乘法器 → 加法树 → 饱和”路径；
 529| - 新增寄存器数量与方案 B 接近，约 129 位；
 530| - 可能比“输入寄存后仍保留完整算术链”的方案 B 更均衡。
 531| 
 532| 不确定性：
 533| 
 534| - 第一级只有 `27.3541 − 5.5820 = 21.7721 ns` 可用；
 535| - 当前材料没有给出单个乘法器到乘积寄存器的到达时间，因此不能判断该级是否必然满足。
 536| 
 537| 建议与方案 B 并行综合，而不是在缺少边界数据时预先选定。
 538| 
 539| ### 方案 D：乘积寄存器 + 求和/溢出标志寄存器，L=3
 540| 
 541| 如果两种 L=2 方案仍不能在所有 corner 收敛，使用允许的最大 L=3：
 542| 
 543| 1. 第 n 个沿：寄存四个乘积；
 544| 2. 第 n+1 个沿：寄存 34 位 `sum` 及 `pos_ovf`、`neg_ovf`；
 545| 3. 第 n+2 个沿：只执行最终饱和选择并写入 `out_data`。
 546| 
 547| ```verilog
 548| reg signed [31:0] p0_q, p1_q, p2_q, p3_q;
 549| reg signed [33:0] sum_q;
 550| reg               pos_q, neg_q;
 551| reg               v1_q, v2_q;
 552| 
 553| always @(posedge clk) begin
 554|     p0_q <= p0;
 555|     p1_q <= p1;
 556|     p2_q <= p2;
 557|     p3_q <= p3;
 558| 
 559|     sum_q <= sum_next;
 560|     pos_q <= pos_next;
 561|     neg_q <= neg_next;
 562| 
 563|     if (rst) begin
 564|         v1_q      <= 1'b0;
 565|         v2_q      <= 1'b0;
 566|         out_valid <= 1'b0;
 567|     end else begin
 568|         v1_q      <= in_valid;
 569|         v2_q      <= v1_q;
 570|         out_valid <= v2_q;
 571|     end
 572| 
 573|     out_data <= pos_q ? 32'h7FFF_FFFF :
 574|                 neg_q ? 32'h8000_0000 :
 575|                         sum_q[31:0];
 576| end
 577| ```
 578| 
 579| 新增寄存器约：
 580| 
 581| - 128 位乘积；
 582| - 34 位 `sum`；
 583| - 2 位饱和标志；
 584| - 2 位 valid 管道；
 585| 
 586| 合计约 166 位。它能最大程度降低每级组合深度，并把疑似公共高扇出的饱和控制信号改为寄存器输出，但面积最大。
 587| 
 588| ### 方案 E：条件性的高扇出复制或缓冲
 589| 
 590| 只有在查询确认 `_11509_/Y` 确实是公共饱和选择信号后，才建议：
 591| 
 592| - 按输出字节或半字复制饱和选择信号；
 593| - 建立结构化的平衡选择树；
 594| - 或直接采用方案 D，将该标志寄存。
 595| 
 596| 需要注意：即使完全消除 `_11509_` 和 `_11512_` 的 3.4987 ns，当前路径仍可能约有 −0.691 ns 违例，因此它更适合作为流水方案的补充，而不是唯一修复手段。
 597| 
 598| ### 修正后的实施顺序
 599| 
 600| 1. 先取得完整违例终点列表，并确认 `_11302_`、`_11509_` 的覆盖率及功能归属。
 601| 2. 尝试方案 A 的无延迟算术优化；若总改善不足 4.19 ns，则不继续依赖 L=1。
 602| 3. 并行综合方案 B 和方案 C：
 603|    - 方案 B 有最直接的对照时序依据；
 604|    - 方案 C 可能更均衡，但缺少乘积边界到达时间。
 605| 4. 若 L=2 候选在任一 corner 仍有 setup 违例，改用方案 D。
 606| 5. 最终方案必须重新验证：
 607|    - 6 个 corner 的 setup 和 hold 全部非负；
 608|    - L≤3；
 609|    - 每周期接收一笔交易；
 610|    - 接口、T 和 IO 约束不变；
 611|    - 面积不超过基线的 1.25 倍；
 612|    - `out_valid`、同步复位、精确求和和饱和行为全部等价。
=== 文件结束：阶段A答复.md ===

## 填写格式

下面各节是格式要求。答复中不要先复述一遍题目中的格式模板或示例标题，直接按"作答要求"交付各部分。

### 预测表的格式

预测表是一个 Markdown 表格，表头一字不差地写成下面这一行，之后是分隔行，每项预测一行：

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | <对应的改动> | <metric> | <check> | <corner> | <category> | <value_kind> | <direction> | <low> | <high> | <unit> | <point> | <文件名:行号> |

各字段的取值：

| 字段 | 取值 |
|---|---|
| `id` | 自己编号，如 P1、P2；第 2 轮可以写 `same_as=<第 1 轮编号>` 表示沿用 |
| `action` | 对应 RTL 中的哪项改动（自由文字） |
| `metric` | `slack`、`area`、`L`、`function` 之一 |
| `check` | `metric` 为 `slack` 时必填：`setup` 或 `hold` |
| `corner` | `all`（6 个 std 点中最差的那个）或某个 corner 名 |
| `category` | `global`、`in2reg`、`reg2reg`、`reg2out` 之一 |
| `value_kind` | `absolute`（候选的数值本身）或 `delta`（候选减 F1 基线） |
| `direction` | 改善 / 退化 / 不变 / 未知（一律相对 F1 基线，两轮都是） |
| `low`、`high`、`unit` | 数值范围；没有依据写"未知"；只写一端时另一端写"未知" |
| `point` | 点估计（如有），与范围分开写 |
| `basis` | 依据，引用"文件名:行号" |

- 比较基准一律相对 F1 基线。
- 没有依据的数值写"未知"，不强求给数。
- 每行保留 `id`、`metric`，并填写适用的 `action`、`basis`。`metric` 为 `L` 时，数值和判定字段只填整数 `point`；为 `function` 时只填 `point` = `pass` 或 `fail`；这两类的 `check`、`corner`、`category`、`value_kind`、`direction`、`low`、`high`、`unit` 留空。
- 表头使用上面的原始列名，不给列名加反引号、加粗或其他装饰。
- 每项预测占一行；单元格中如需写字面的竖线，写成 `\|`。
- 其余说明（`category` 的含义、`unit` 的写法等）见 `constraints.md` 第 7 节。

### 失败条件的写法

- 失败条件说明：出现什么结果，就说明这个修改没有达到它的目的。
- 每条失败条件写成一个顶层列表项（以 `- ` 开头），不要把独立的条件缩进成上一条的子项。
- 尽量写成可以用评估结果直接检查的条件。

### 声明行

- 单独一行写 `DECLARED_L = <n>`，n 是你的实现的延迟 L（1–3 的一位整数）。
- 这一行不放在代码块、引用或行内代码里，全文只写一次。评估使用的 L 以这一行为准。
- 保留 `DECLARED_L = <n>` 的精确写法：等号两边各一个空格，等号用 ASCII 字符 `=`。

### RTL 代码块

- 恰好一个 verilog 代码块：以单独一行 ```` ```verilog ```` 开始，以单独一行 ```` ``` ```` 结束。代码围栏的语言名写小写的 `verilog`。
- 内容是完整的 `dot4sat` 模块文件，满足 `constraints.md` 第 5 节的全部规则。
- 如果给出多个代码块，只有第一个 verilog 代码块会被评估；第一个代码块不完整时，不会改用后面的代码块。

## 作答要求

只交一个候选。请依次交付以下六个部分。每个部分用一个二级标题开头，第 5、6 部分共用一个标题；五个标题的文字依次是 `修改假设`、`预测表`、`代价`、`失败条件`、`声明行和 RTL`（例如 `## 预测表`），标题中不要加其他文字。

1. 修改假设：要改什么、为什么能改善、依据（引用材料，写"文件名:行号"）。
2. 预测表：按上面的格式填写。
3. 代价：面积、延迟 L、hold、功能风险，用自由文字写。
4. 失败条件：按上面的写法。
5. 声明行：在标题 `## 声明行和 RTL` 下，单独一行 `DECLARED_L = <n>`，不放在代码块里。
6. RTL：在同一标题下、声明行之后，恰好一个 verilog 代码块，内容是完整的 `dot4sat` 模块文件。
