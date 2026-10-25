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

=== 文件：阶段A答复.md（共 184 行）===
   1| # dot4sat 基线 STA 第 2 轮：根据查询结果确认和修正判断
   2| 
   3| ## 一、报告事实
   4| 
   5| 本节只列新增和修正的事实。第 1 轮已列出的事实仍然有效。
   6| 
   7| ### 1. 终点身份（A1）
   8| 
   9| - `_12026_` 是 `dfxtp_1`，Q 直接连到 `out_data[0]`，D 网络名为 `_00030_`。第 1 轮"`_12026_` 很可能是 `out_data[0]` 寄存器"的推测**已确认**。
  10| - `report_net [get_nets -of_objects ...]` 在 A1、A3、A4 中都报 Error 232。这是查询写法的问题，不是网表的问题。网络信息因此没有拿到。
  11| 
  12| ### 2. 违例终点分布（A2）
  13| 
  14| ss_n40C_1v60 下，in2reg 共有 **32 个违例终点**，`find_timing_paths` 返回 32 条：
  15| 
  16| | 组 | 终点 | slack (ns) | arrival (ns) |
  17| |---|---|---|---|
  18| | 1 | 27 个（`_12026_`、`_12027_`、`_12029_`、`_12032_`…`_12045_`、`_12047_`…`_12056_`） | −4.1897 | 31.5439 |
  19| | 2 | 4 个（`_12028_`、`_12030_`、`_12031_`、`_12046_`） | −4.0997 | 31.4791 |
  20| | 3 | 1 个（`_12057_`） | −0.9676 | 28.4953 |
  21| 
  22| 其他角点和汇总：
  23| 
  24| - ss_100C_1v60 下有 31 个违例终点，就是上表前两组，slack 为 −0.6873 / −0.6687。`_12057_` 在该角点不违例。
  25| - `report_tns` 的结果为 −130.4888。按上表手算：27×4.1897 + 4×4.0997 + 0.9676 ≈ 130.488，与它吻合。
  26|   - 所以这个值等于 ss_n40C 一个角点的 TNS，不是各角点 TNS 的累加。如果累加，还要再加 ss_100C 的约 21 ns。
  27|   - 它的具体语义是"每个终点取各场景中的最差值"还是"取最差场景"，**不确定**。在本例中两种语义结果相同。
  28| - `_12026_`…`_12057_` 共 32 个触发器，与 `out_data` 的 32 位数目吻合。`_12058_` 是 rst 的 hold 终点（slack_summary.tsv:38），很可能是 `out_valid`。逐位对应关系**未逐个确认**。
  29| 
  30| ### 3. `_11509_` 的身份（A3）
  31| 
  32| - `_11509_` 是 `o21ai_0`，输入网络为 `_05585_`/`_05586_`（A1/A2）和 `_05584_`（B1），输出网络为 `_05587_`。
  33| - 经过 `_11509_/Y` 的终点恰好是 **31 个**，即全部违例终点中除 `_12057_` 以外的那些。这与 fanout = 31（path_report.rpt:84）一致。
  34| - 这说明 `_11509_/Y` 是一个公共信号，扇出到 31 个输出位，而 `out_data` 的某一位（`_12057_`）不经过它。
  35| - 这与饱和逻辑的形态相符：`sat[30:0]` 在溢出时取同一个常数值，`sat[31]` 的逻辑不同。不过 `_12057_` 是否就是 `out_data[31]`，**未确认**。
  36| 
  37| ### 4. 中间节点（A4）
  38| 
  39| `-format summary` 只输出终点 slack，没有给出中间节点的到达时间。这条查询本身设计有误，没有得到新信息。中间节点时间仍以 path_report.rpt 为准。
  40| 
  41| ### 5. 尺寸替换对照（A5，只作对照）
  42| 
  43| `_11509_` 换成 `o21ai_4` 后，最差 slack 从 −4.1897 变为 **−3.5167**，只改善了 0.673 ns。
  44| 
  45| - arrival 减少 0.589 ns；setup 时间从 0.5559 降到 0.4715 ns，因为 D 端 slew 变小。
  46| - 最差路径**改走另一分支**：`_11451_` → `_11454_`（`a31oi_1`）→ `_11504_`（`xnor2_1`）→ **`_11510_`（`a21oi_1`，单级 1.9801 ns）** → `_11512_`。
  47| - `_11510_` 的单级延迟接近 2 ns。这说明饱和选择部分还有**第二个重负载网络**，它同样汇入 `_11512_`。这是推断，`_11510_` 的 fanout 没有直接查到。
  48| 
  49| ### 6. 同一路径的角点对照（A6）
  50| 
  51| 同一路径 `in_b[2]` → `_11509_/Y` → `_12026_/D` 的 slack：
  52| 
  53| | 角点 | slack (ns) |
  54| |---|---|
  55| | ss_100C | −0.5003 |
  56| | ss_n40C | −4.1897 |
  57| | tt_025C | +11.2014 |
  58| 
  59| 两个 ss 角点相差约 3.7 ns，**低温比高温慢**。温度反转（H5）**已确认**。
  60| 
  61| ### 7. 输入延迟对照（A7，只作对照）
  62| 
  63| 输入延迟设为 0 后，slack = +1.3923。这与第 1 轮的估算（约 +1.39）一致。从端口到 D 的组合延迟为 25.9619 ns。
  64| 
  65| ### 8. 面积与库数据（A8）
  66| 
  67| - 全部单元的面积和为 **45383.53**，单位应为库的面积单位，即 µm²，**未确认**。
  68| - 1.25 倍上限对应的可增面积约为 **11345.9**。
  69| - `report_lib_cell` 没有给出面积，也没有给出时序数值。
  70| 
  71| ### 9. 由已有数据推出的 clk→Q
  72| 
  73| - `_12026_/Q` 直接驱动 `out_data[0]`（A1）。reg2out 的 max 一项：required = T − 0.2T = 22.328，slack 为 21.6924（slack_summary.tsv:41），所以 arrival ≈ **0.636 ns**。
  74| - 这个 arrival 就是 ss_n40C、轻负载下的 clk→Q（max）。
  75| - 同理，min 一项 0.548（ss_n40C）和 0.173（ff_n40C）对应 clk→Q 的最小值（slack_summary.tsv:42、50）。
  76| 
  77| ### 10. 关键推论：饱和级之前已经超时
  78| 
  79| `_11507_/Y` 的到达时间是 28.0452（path_report.rpt:82），已经晚于 required 27.35。也就是说，即使把饱和选择的全部延迟（第④段约 3.50 ns）降为 0，这条路径仍然约有 −0.7 ns 的违例。
  80| 
  81| ## 二、原因假设（更新）
  82| 
  83| | 假设 | 状态 | 依据 |
  84| |---|---|---|
  85| | H1：单周期内逻辑过深（结构性） | **加强，仍是主因** | 单点尺寸替换只改善 0.67 ns，最差路径随即转移（A5）；输入延迟为 0 时也只剩 +1.39 ns 余量（A7）；饱和级之前的到达时间 28.05 已经超过 required |
  86| | H2：CPA 是 ripple 结构 | **未验证**（A4 没有给出信息） | 推翻条件不变：网表中存在前缀结构，或者链上单元不按位相邻级联 |
  87| | H3：饱和选择的高扇出 | **修正**：确认存在公共的 31 扇出信号，但它只是次要因素 | 至少有两个重负载网络（`_11509_`、`_11510_`）；单改一个只得到 0.67 ns；即使饱和级为 0 也仍然违例 |
  88| | H4：普遍使用最小尺寸单元 | 只得到部分对照，**不确定** | 没有做整条路径的尺寸替换。另外综合配方固定，尺寸调整不能作为修改手段，因此 H4 对修改方案的意义有限 |
  89| | H5：低温角点最差（温度反转） | **已确认**（A6） | 同一路径 ss_n40C 比 ss_100C 慢约 3.7 ns |
  90| | H6：输入端口驱动不是主因 | 维持 | 端口驱动 0.309 ns，A7 中不变 |
  91| 
  92| 新增假设：
  93| 
  94| **H7：`_12057_` 是 `out_data[31]`（符号位），它的饱和逻辑与其余 31 位不同，所以不经过 `_11509_`。**
  95| 推翻条件：`report_instance _12057_` 显示 Q 连接的不是 `out_data[31]`。
  96| 
  97| ## 三、缺失的证据
  98| 
  99| 1. `_11509_/Y`（网络 `_05587_`）和 `_11510_/Y` 的负载清单，以及 `_11510_` 的 fanout。这些用来确认饱和选择逻辑的结构。
 100| 2. `_12026_`…`_12057_` 与 `out_data` 各位的对应关系，尤其是 `_12057_`；以及 `_12057_` 的完整路径。
 101| 3. `_11509_` 的三个输入网络（`_05584_`/`_05585_`/`_05586_`）往回追溯的情况，用来确认它是否就是溢出判断。
 102| 4. 进位链（H2）的结构证据，目前仍然缺失。
 103| 5. `dfxtp_1` 的面积。按 Sky130 常见值约为 20 µm²，但材料里没有，**需要查询**。另外需要触发器数目和组合逻辑面积的拆分。
 104| 6. 修改方案是否成立，最终需要重新综合后的面积和 STA 结果，本环境无法获得。
 105| 
 106| ## 四、下一步查询
 107| 
 108| 不使用 `get_nets -of_objects`，改为直接写网络名。
 109| 
 110| ```tcl
 111| # 1. 饱和选择网络的负载
 112| report_net -digits 4 _05587_
 113| report_instance _11510_
 114| report_instance _11512_
 115| report_instance _11507_
 116| foreach n {_05584_ _05585_ _05586_} { report_net -digits 4 $n }
 117| 
 118| # 2. 终点与 out_data 各位的对应关系，以及 _12057_ 的路径
 119| foreach i {_12026_ _12028_ _12046_ _12056_ _12057_ _12058_} { report_instance $i }
 120| report_checks -to [get_pins _12057_/D] -path_delay max -scene ss_n40C_1v60 \
 121|   -fields {slew cap input_pins fanout} -digits 4
 122| 
 123| # 3. 第二个重负载网络（_11510_ 的输出网络名按上面 report_instance 的结果填入）
 124| # report_net -digits 4 <_11510_ 的 Y 网络>
 125| 
 126| # 4. 面积拆分
 127| puts [get_property [get_lib_cells */sky130_fd_sc_hd__dfxtp_1] area]
 128| puts [llength [get_cells *]]
 129| puts [llength [all_registers]]
 130| 
 131| # 5. 对照（只作对照）：两个重负载驱动同时加大
 132| replace_cell _11509_ sky130_fd_sc_hd__o21ai_4
 133| replace_cell _11510_ sky130_fd_sc_hd__a21oi_4
 134| report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] \
 135|   -path_delay max -scene ss_n40C_1v60 -digits 4
 136| replace_cell _11509_ sky130_fd_sc_hd__o21ai_0
 137| replace_cell _11510_ sky130_fd_sc_hd__a21oi_1
 138| 
 139| # 6. 进位链结构（H2）
 140| foreach i {_11418_ _11421_ _11423_ _11424_ _11428_ _11429_} { report_instance $i }
 141| ```
 142| 
 143| 关于第 4 项：`get_lib_cells */...` 这种通配写法在多库加载时会返回多个对象，是否可用**不确定**。如果不行，改用 `get_lib_cells sky130_fd_sc_hd__tt_025C_1v80/sky130_fd_sc_hd__dfxtp_1`。
 144| 
 145| ## 五、可能的修改（更新）
 146| 
 147| ### 时序预算（ss_n40C，已用实测数据修正）
 148| 
 149| | 级型 | 可用时间 | 计算 |
 150| |---|---|---|
 151| | in2reg | 约 21.8 ns | 27.91 − 5.582 − 约 0.5 |
 152| | reg2reg | 约 26.8 ns | 27.91 − clk→Q 0.64 − setup 约 0.5 |
 153| 
 154| 现有从端口算起的组合延迟为 25.96 ns（A7）。所以 **L = 2、切一刀**在时序上是足够的，结论不变。
 155| 
 156| ### 面积预算（新增）
 157| 
 158| 可增面积约为 11346。假设 `dfxtp_1` 约 20 µm²（**待查询确认**）：
 159| 
 160| | 方案 | 新增触发器 | 新增面积 | 约占基线 |
 161| |---|---|---|---|
 162| | A | 约 68 个 | 约 1360 | 3% |
 163| | C | 约 128 个 | 约 2560 | 5.6% |
 164| 
 165| 即使计入 RTL 重写带来的组合逻辑变化，也很可能在 1.25 倍以内。第 1 轮"方案 C 可能超出面积上限"的担心**基本消除**，但仍需重新综合后核实。
 166| 
 167| ### 方案排序调整
 168| 
 169| 1. **方案 C（L = 2，寄存 4 个乘积）提升为首选。**
 170|    - RTL 改动最简单，等价性风险最低。
 171|    - 第一级只有一个 16×16 乘法器，第二级是四数相加加饱和。按现有分段估算，第二级约为 4 加 13 加 3.5 ≈ 20 ns，小于 26.8 ns。
 172|    - 第一级（含端口约束）能否在 21.8 ns 内完成，取决于 Yosys 给单个乘法器生成的 CPA。这一点**不确定**，需要重新综合后跑 STA。
 173| 2. **方案 A（L = 2，寄存进位保留形式）作为时序最稳的备选。** 代价是需要手写压缩树，而且 ABC 是否会保留手写结构不确定。
 174| 3. **方案 B（寄存 s01/s23）降为次选。** 第一级包含"乘法加 33 位加法"，从端口算起很可能超过 21.8 ns。
 175| 4. **方案 D（L = 1：简化饱和判断、复制选择信号、前缀加法器）进一步降级。**
 176|    - A5 显示单点修复只得到 0.67 ns，最差路径随即转移到 `_11510_`。
 177|    - 饱和级之前的到达时间已经是 28.05，晚于 required 27.35。即使饱和级耗时为 0 也仍然违例。
 178|    - 所以单靠饱和优化**不可能**消除违例。只有同时把 CPA 改成前缀结构才有可能，而在综合配方固定的条件下，这一点不确定。
 179| 
 180| ### 所有流水线方案的共同要求（不变）
 181| 
 182| - `in_valid` 同步延迟一级，每级 valid 都用同步 `rst` 清零，保证 L 固定且每周期都能接收一笔新交易。
 183| - 数据寄存器可以不复位。
 184| - 新增的 reg2reg 路径需要在 ff 角点用 `-path_delay min` 检查 hold。clk→Q 最小值约为 0.17 ns（ff_n40C），预计没有问题，但需要实测确认。
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

以下是你在第 1 轮的答复。

<<<第 1 轮答复开始>>>
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
<<<第 1 轮答复结束>>>

第 2 轮的作答规则：

- 你可以提交一个修改后的候选，格式与第 1 轮相同：六个部分、五个二级标题（最后一个是 `声明行和 RTL`），见第 1 轮题目中的"填写格式"和"作答要求"。
- 预测表的比较基准仍然一律相对 F1 基线，不是相对你第 1 轮的候选。沿用第 1 轮的某一条预测时，`id` 可以写 `same_as=<第 1 轮编号>`。
- 你也可以选择不再提交：单独一行写 `NO_SUBMISSION`（这一行只有这个词），并说明理由，同时不给出任何 verilog 代码块。
- `NO_SUBMISSION` 写在代码块、引用或行内代码里不算数。
- `NO_SUBMISSION` 与 verilog 代码块同时出现时，按交付失败处理，不会替你判断想提交什么。

以下是你第 1 轮的结果。

GRADE FAIL

grade_status：GRADE FAIL

失败位置：步骤 sta

该位置的日志摘要：

```text
日志检查发现的问题：
sta error: Error: 171 <RUN>/synth/netlist.v line 6102, syntax error

日志末尾摘要（最多 40 个物理行）：
Error: 171 <RUN>/synth/netlist.v line 6102, syntax error
```

已有的结果字段（缺的写 not_available，没执行的写 not_run）：

- rtl_sim：pass（checked=2816）
- gl_sim：pass（checked=2816）
- sta_analysis：fail
- cfg_L：3
- 面积（µm²）：48790.544000
- 是否超过面积上限：否
- 全局最差 setup slack（ns）：not_available
- 全局最差 hold slack（ns）：not_available
- 是否数值上满足 setup_ge_0_std：not_available

6 个 std 点的全局最小 slack（ns）：

not_available

in2reg、reg2reg、reg2out 三类路径在 6 个点的 setup 和 hold slack（ns）及起点、终点（不存在的写 not_applicable）：

not_available

你第 1 轮的候选已经运行评估，但没有得到有效的时序分析结果，情况见上。你可以提交一个修改后的候选（格式同第 1 轮），也可以单独一行写 `NO_SUBMISSION` 并说明理由。
