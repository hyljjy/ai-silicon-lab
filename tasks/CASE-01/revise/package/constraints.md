# 阶段 B 的约束和提交要求

本文件只列硬约束、数字、RTL 的提交格式和预测表的填写规则。

文中"合同"指 CASE-01 设计合同，相关条款见 `contract_excerpt.md`（合同第 1、2 节和第 3.1 节原文）。"F1 基线"指材料中的 `dot4sat.v`（L = 1）在冻结评估中的结果：各 corner 的 slack 见 `slack_summary.tsv`，面积见下面第 3 节。

## 1. 不变的部分

- 时钟周期 T、IO 约束、SDC、工艺库、综合配方、corner 都不变（取值和原文见 `values.txt`、`case01_sdc.tcl`、`context.md`）。
- 修改只能改 RTL。

## 2. 延迟和吞吐

- 延迟 L 允许 1–3（L 的定义见合同第 2.2 节）。
- 每个时钟周期接收一笔交易，没有停顿，没有背压。

## 3. 面积

- 面积上限：56729.408 µm²。
- F1 基线面积：45383.5264 µm²。

## 4. 正式成功标准

- 6 个 std 点（`tt_025C_1v80`、`tt_100C_1v80`、`ss_100C_1v60`、`ss_n40C_1v60`、`ff_n40C_1v95`、`ff_100C_1v95`）中最差的 setup slack ≥ 0。
- hold 只记录，不作判据。

## 5. RTL 的要求

提交的 RTL 必须满足下表全部规则。"合同要求"来自合同；"阶段 B 附加提交格式限制"不是合同条款，是本阶段对提交格式的额外限制。任何一条不满足，候选都不进入评估；被附加提交格式限制拒绝的候选，结果记为"违反阶段 B 附加提交格式限制"，不记为"违反合同"。

| 编号 | 规则 | 性质和来源 |
|---|---|---|
| G1 | 模块名 `dot4sat`，端口集合与合同第 1 节完全一致：名称、方向、位宽，不多不少（`clk`、`rst`、`in_valid`、`in_a[63:0]`、`in_b[63:0]`、`out_valid`、`out_data[31:0]`） | 合同要求（第 1 节） |
| G2 | 不使用 plusarg、文件读写、shell、波形转储类系统任务，不用 `` `include `` | 合同要求（第 1 节）；`grade.py` 的 lint 也会再查 |
| G3 | 文件中只有一个模块 | 阶段 B 附加提交格式限制：冻结的综合配方不展平层次，`grade.py` 只在单模块的基线和自检夹具上验证过 |
| G4 | 不用 `parameter`（可以用 `localparam`） | 阶段 B 附加提交格式限制：合同只禁止用参数改变功能；这里直接禁止，免得判断"是否改变功能" |
| G5 | 不用任何反引号编译指令（`` `define ``、`` `ifdef ``、`` `timescale `` 等） | 阶段 B 附加提交格式限制：合同只禁止用宏改变功能；`` `timescale `` 等指令可能与 TB 冲突或产生白名单之外的 warning |
| G6 | 时序 always 块的事件控制恰好是 `@(posedge clk)`；组合逻辑只用连续赋值（`assign`，或像基线那样带赋值的 `wire` 声明）或 `always @*`/`always @(*)`；不用 `initial`、`#` 延时、`negedge` | 阶段 B 附加提交格式限制，对应合同第 1、2.3 节"只在 `clk` 上升沿动作、同步复位" |
| G7 | 标识符 `clk`（转义形式按同一标识符处理）只出现在以下位置：模块头的端口列表；ANSI 或非 ANSI 的端口声明；在模块顶层对模块头端口 `clk` 的不带赋值的线网声明（如非 ANSI 写法中的 `wire clk;`）；G6 允许的 `posedge clk` 事件控制。作为数据、条件或表达式操作数出现即拒绝 | 阶段 B 附加提交格式限制：不把时钟用作数据或条件 |
| G8 | `DECLARED_L` 在 1..3 之间 | `config/f1.cfg` 的 L_max（等于 3） |

## 6. 提交格式

- 答复中恰好一个 verilog 代码块：以单独一行 ```` ```verilog ```` 开始，以单独一行 ```` ``` ```` 结束；内容是完整的 `dot4sat` 模块文件。
- 如果给出多个代码块，只有第一个 verilog 代码块会被评估；第一个代码块不完整时，不会改用后面的代码块。
- 单独一行写 `DECLARED_L = <n>`，n 是实现的延迟 L。这一行不放在代码块、引用或行内代码里，全文只写一次。评估使用的 L 以这一行为准。

## 7. 预测表的填写规则

预测表是一个 Markdown 表格，表头一字不差地写成下面这一行：

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |

各字段的取值：

| 字段 | 取值 |
|---|---|
| `id` | 自己编号，如 P1、P2；第 2 轮可以写 `same_as=<第 1 轮编号>` 表示沿用 |
| `action` | 对应 RTL 中的哪项改动（自由文字） |
| `metric` | `slack`、`area`、`L`、`function` 之一 |
| `check` | `metric` 为 `slack` 时必填：`setup` 或 `hold` |
| `corner` | `all`（6 个 std 点中最差的那个）或某个 corner 名（见第 4 节） |
| `category` | `global`、`in2reg`、`reg2reg`、`reg2out` 之一 |
| `value_kind` | `absolute`（候选的数值本身）或 `delta`（候选减 F1 基线） |
| `direction` | 改善 / 退化 / 不变 / 未知（一律相对 F1 基线，两轮都是） |
| `low`、`high`、`unit` | 数值范围；没有依据写"未知"；只写一端时另一端写"未知" |
| `point` | 点估计（如有），与范围分开写 |
| `basis` | 依据，引用"文件名:行号" |

补充说明：

- 比较基准一律相对 F1 基线。
- 没有依据的数值写"未知"，不强求给数。
- 每行保留 `id`、`metric`，并填写适用的 `action`、`basis`。`metric` 为 `L` 时，数值和判定字段只填整数 `point`；为 `function` 时只填 `point` = `pass` 或 `fail`；这两类的 `check`、`corner`、`category`、`value_kind`、`direction`、`low`、`high`、`unit` 留空。
- `function` 的实际结果取 RTL 仿真和门级功能仿真：两者都通过为 `pass`，任一失败为 `fail`，其他情况为无结果。
- `category`：`global` 指不分类别、该 corner 所有路径中最差的一条（对应 `slack_summary.tsv` 的 WS 行）；`in2reg` 为输入到寄存器，`reg2reg` 为寄存器到寄存器，`reg2out` 为寄存器到输出（对应 CAT 行）。
- `unit`：slack 写 `ns`，面积写 `µm²`。
- 每行只写一项预测；同一个 `id` 不重复使用。

## 8. 评估方式

- 评估用冻结的流程：RTL 仿真、门级功能仿真、综合、6 个 std 点的 STA。STA 的分析条件同 `context.md`（综合后、理想时钟、连线负载只计引脚电容）。
- 本阶段不能调用工具或查询，也不提供网表。原样材料中关于查询的说明属于阶段 A。
