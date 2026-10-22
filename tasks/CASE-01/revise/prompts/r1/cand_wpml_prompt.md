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

=== 文件：阶段A答复.md（共 116 行）===
   1| ## 一、报告事实
   2| 
   3| - 查询 C1 首先确认：本 OpenSTA 3.1.0 的 `report_checks` 不接受 `-nworst`，报错 `Error 514: '-nworst' is not a known keyword or flag`（查询 C1 输出）。第一轮想用 `-nworst` 枚举多条路径的查询不可用。
   4| - 跨 corner 查询可见部分仍以 `ss_n40C_1v60` 下 `in_b[2] -> _12026_/D` 为最差路径，路径内容与 `path_report.rpt` 一致（查询 C1 输出；path_report.rpt:1-5、87-100）。
   5| - 对照查询：`set_input_delay -clock clk -max 0` 后，同一条路径在 `ss_n40C_1v60` 下组合到达时间为 25.9619，要求时间仍为 27.3541，slack 为 1.3923 MET（查询 C1 输出尾部）。这说明原始到达时间 31.5439 ≈ 5.582 输入外部延迟 + 25.9619 组合延迟。
   6| - 已知汇总：`ss_n40C_1v60` 最差 setup 为 -4.1897，`ss_100C_1v60` 为 -0.6873；tt/ff 角 setup 为正（slack_summary.tsv:11-29、35-36）。
   7| - 原路径中高扇出点 `_11509_/Y`：fanout=31，cap=0.0511，slew=3.2455，delay=2.6362（path_report.rpt:83-85）。
   8| - 查询 C1 的可见部分没有给出多条 `in2reg` 路径排序、`_11509_` 连接/驱动详情，也没有给出 `reg2out`、hold 的详细逐路径报告；这些被截断或因命令语法失败未获得（查询 C1 输出标记为“已截断”；`-nworst` 报错）。
   9| - 题目说明对照查询是“改变冻结模型的查询”，“结果只作对照，不代表冻结模型”（查询 C1 元信息）。
  10| 
  11| ## 二、原因假设
  12| 
  13| - **H1 需要修正：不能简单说“主因是单周期组合逻辑深度过长”。**  
  14|   对照查询显示：去掉输入延迟后，组合段 25.9619 ns 小于数据要求时间 27.3541 ns，slack 为正 1.3923。因此组合深度很长，但单独并不违例；本路径违例是“组合延迟 + 固定输入 max 延迟 5.582”共同超过要求时间。原 H1 的说法被事实部分推翻或弱化。  
  15|   - 可证伪：若另一条 in2reg 路径在去掉输入延迟后仍为负 slack，则说明某些路径的组合段本身超过一个周期，仍应保留“组合深度单独违例”的判断；但当前最差路径不是这种情况。
  16| 
  17| - **H2 被确认：固定输入延迟是违例的必要成分。**  
  18|   同一路径仅把输入 max 延迟清 0，slack 从 -4.1897 变为 +1.3923。注意这不是合法修复，只是对照分析，但可确认输入延迟是重要组成部分。  
  19|   - 可证伪：若清 0 后仍为负，则固定输入延迟不是必要成因；事实已推翻这一反证。
  20| 
  21| - **H3 被确认：最差 setup 在算术数据路径上，终点是 `_12026_/D`。**  
  22|   可见最差路径仍为 `in_b[2] -> _12026_/D`，且 `_12026_` 是 `out_data[0]` 对应的输出寄存器；`slack_summary.tsv` 也显示最差 `in2reg` 起点为 `in_b[2]`。没有看到更差的控制路径。
  23| 
  24| - **H4 被确认并可以量化：高扇出点 `_11509_/Y` 是局部瓶颈，但单点修复不够。**  
  25|   即使把 `_11509_/Y` 的 2.6362 ns 全部消除，组合段估算约为 25.9619 − 2.6362 = 23.3257 ns；再加输入延迟 5.582 = 28.9077 ns，仍大于要求时间 27.3541，slack 仍约 -1.55。因此它只是次级瓶颈，不能单独转正。
  26| 
  27| - **H5 维持成立：需要重点修复低速 ss 角。**  
  28|   从汇总和跨角可见部分看，`ss_n40C_1v60` 与 `ss_100C_1v60` 违例，tt/ff 角有正裕量。
  29| 
  30| ## 三、缺失的证据
  31| 
  32| - 缺少全部 130 条 `in2reg` setup 路径的完整排序，无法确认最差路径是否集中在 `out_data` 若干 bit，还是均匀分布；`-nworst` 不可用后仍需找到替代枚举方式。
  33| - 缺少 `_11509_` 的完整连接/驱动报告（fanout 分布、各负载轨迹、可替换驱动单元）。
  34| - 缺少乘法、求和、饱和三段的时延分割，尤其是从输入端口到乘积寄存器的可行分割点。
  35| - 缺少 `reg2out`、hold 的详细逐路径报告；现有只有汇总，不能判断流水化后输出路径是否恶化。
  36| - 缺少门级网表和综合后面积数据，无法确认 L=2/L=3 增加寄存器的面积是否不超过基线的 1.25 倍。
  37| - 缺少 L=2/L=3 修改后重综合并全 corner STA 的结果。
  38| 
  39| ## 四、下一步查询
  40| 
  41| 第一轮的 `-nworst` 已证实不可用，因此需要先确认本版本可用的多路径枚举选项，再执行后续查询。
  42| 
  43| ```tcl
  44| # 0) 先确认本版本可用选项，不能再使用 -nworst
  45| help report_checks
  46| help find_timing_paths
  47| 
  48| # 1) 若 report_checks 支持 -slack_threshold，用它枚举 ss_n40C 下输入到寄存器 setup
  49| report_checks \
  50|   -from [all_inputs -no_clocks] \
  51|   -to [all_registers -data_pins] \
  52|   -path_delay max \
  53|   -scenes ss_n40C_1v60 \
  54|   -fields {slew cap input_pins fanout} \
  55|   -digits 4 \
  56|   -slack_threshold 1.0
  57| 
  58| # 2) 跨全部 corner 同类最差（仅默认最差也需确认各角）
  59| report_checks \
  60|   -from [all_inputs -no_clocks] \
  61|   -to [all_registers -data_pins] \
  62|   -path_delay max \
  63|   -scenes {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} \
  64|   -fields {slew cap input_pins fanout} \
  65|   -digits 4
  66| 
  67| # 3) 高扇出网络单独查询，避免与其他输出混在一起被截断
  68| report_net -connections _11509_
  69| report_driver -net _11509_
  70| 
  71| # 4) 已知最差路径单条确认
  72| report_checks \
  73|   -from in_b[2] \
  74|   -to _12026_/D \
  75|   -path_delay max \
  76|   -scene ss_n40C_1v60 \
  77|   -fields {slew cap input_pins fanout} \
  78|   -digits 4
  79| 
  80| # 5) reg2out 与 hold 详细报告
  81| report_checks \
  82|   -from [all_registers -clock_pins] \
  83|   -to [all_outputs] \
  84|   -path_delay max \
  85|   -scenes ss_n40C_1v60 \
  86|   -fields {slew cap input_pins fanout} \
  87|   -digits 4
  88| 
  89| report_checks \
  90|   -from [all_inputs -no_clocks] \
  91|   -to [all_registers -data_pins] \
  92|   -path_delay min \
  93|   -scenes ss_n40C_1v60 \
  94|   -fields {slew cap input_pins fanout} \
  95|   -digits 4
  96| 
  97| # 6) 确认冻结模型已恢复；若当前环境仍残留对照约束，则重新 source 原始 SDC
  98| # source case01_sdc.tcl（保持 T=27.91、C_load=0.0024 不变）
  99| ```
 100| 
 101| ## 五、可能的修改
 102| 
 103| - **首选仍为 L=2 流水化，新证据进一步支持其必要性。**  
 104|   扣掉 `0.2T` 输入延迟后，输入到第一级寄存器的可用组合时间约为 `27.3541 - 5.582 = 21.7721 ns`；基线组合段 25.9619 ns 虽然单独不超期，但超过这个扣除输入延迟后的预算。因此不能仅靠门级优化轻松吸收，流水化是最直接的路线。  
 105|   - 保持 L=2：在四个乘积 `p0..p3` 后插入一级乘积寄存器，第二拍完成 34 位求和与饱和并打入输出寄存器；`in_valid` 相应延迟一级以使 `out_valid` 对齐。  
 106|   - 输入到乘积寄存器预计明显小于 21.77 ns；乘积寄存器到输出寄存器无输入延迟，可用约 27.35 ns。需综合后全角 STA 确认。
 107| 
 108| - **L=3 备选：** 若 L=2 后第一级乘法段仍接近或超过 21.77 ns，或将求和再拆一级更稳，则插入乘积寄存器和 34 位和寄存器，形成 L=3；`in_valid` 相应移位两级。仍满足 L ≤ 3，且每周期可接收新一笔交易。
 109| 
 110| - **门级微调只能作为流水化后的补充，不能替代流水化。**  
 111|   对 `_11509_/Y` 高扇出点插入缓冲/复制驱动可降低局部 slew 和延时，但按现有路径推算，单点优化后仍为负 slack；因此不应把修复重点放在该点。
 112| 
 113| - **不可采用清输入延迟、增大周期或放宽输出约束作为正式修改。**  
 114|   对照分析只用于理解成因，不能变成实现方案；正式修改必须保持 `case01_sdc.tcl` 中的约束和 `T=27.91` 不变。
 115| 
 116| - **验证要求：** 修改后必须在六角下重跑 `in2reg`、`reg2reg`、`reg2out` 的 setup/hold，并确认 L ≤ 3、每个时钟周期可接收新交易、接口与 IO 约束不变、面积不超过基线的 1.25 倍。目前面积数据缺失，不能无证据断言 L=2/L=3 一定满足面积限制，需重新综合后确认。
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
