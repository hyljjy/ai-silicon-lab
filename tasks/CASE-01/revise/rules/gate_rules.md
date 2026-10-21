# 合同门槛 G1–G8（`revise/scripts/gate.py`）

依据：规程 v0.5 §7.2、§6.3 第 3 部分；修订 `revise/revisions.md` RV-01（两阶段 Yosys 读取）、RV-06（`translate_off` 类注释）、RV-07（G7 允许 `wire clk;`）。第二列是规程 v0.5 §7.2 表中的规则原文（测试逐字核对；给模型的 `package_src/constraints.md` 第 5 节应与之一致）；`feedback.py` 按每行第一格的编号取第二格。

| 编号 | 规则 | 性质和来源 | 识别方法 |
|---|---|---|---|
| G1 | 模块名 `dot4sat`，端口集合与合同第 1 节完全一致：名称、方向、位宽，不多不少（`clk`、`rst`、`in_valid`、`in_a[63:0]`、`in_b[63:0]`、`out_valid`、`out_data[31:0]`） | 合同要求（第 1 节） | Yosys 第 2 阶段导出的 JSON：模块 `dot4sat` 的端口名、`direction`、位宽 `len(bits)`，不比较 `bits` 编号；没有 `dot4sat` 模块时行号取第一个 `module` 行，端口不符时取分词器找到的该端口声明行（先找端口声明语句，再找模块头），找不到取 `module` 行 |
| G2 | 不使用 plusarg、文件读写、shell、波形转储类系统任务，不用 `` `include `` | 合同要求（第 1 节）；`grade.py` 的 lint 也会再查 | 分词器：`systask` 记号去掉 `$` 后在 `grade.LINT_SYSTF`（从冻结的 `scripts/grade.py` 按显式路径只读载入）中，或 `directive` 为 `` `include `` |
| G3 | 文件中只有一个模块 | 附加提交格式限制：冻结的综合配方不展平层次，`grade.py` 只在单模块的基线和自检夹具上验证过 | 分词器：`module`/`macromodule` 关键字个数不等于 1，行号为第二个模块的关键字行（没有模块时为 0）；另与 JSON 的完整模块集合核对数量，不一致记 `unrecognized`，不掩盖 G3 |
| G4 | 不用 `parameter`（可以用 `localparam`） | 附加提交格式限制：合同只禁止用参数改变功能；这里直接禁止，免得判断"是否改变功能" | 分词器：关键字 `parameter` |
| G5 | 不用任何反引号编译指令（`` `define ``、`` `ifdef ``、`` `timescale `` 等） | 附加提交格式限制：合同只禁止用宏改变功能；`` `timescale `` 等指令可能与 TB 冲突或产生白名单之外的 warning | 分词器：任何 `directive` 记号（包括宏的使用处） |
| G6 | 时序 always 块的事件控制恰好是 `@(posedge clk)`；组合逻辑只用连续赋值（`assign`，或像基线那样带赋值的 `wire` 声明）或 `always @*`/`always @(*)`；不用 `initial`、`#` 延时、`negedge` | 附加提交格式限制，对应合同第 1、2.3 节"只在 `clk` 上升沿动作、同步复位" | 分词器：`always` 之后必须是 `@` 加 `*`、`( * )` 或 `( posedge clk )`（`clk` 可为转义形式）；其他形式、`initial`、`#`、`negedge`，以及不紧跟在 `always` 之后的 `@` 事件控制 |
| G7 | 标识符 `clk`（转义形式按同一标识符处理）只出现在以下位置：模块头的端口列表；ANSI 或非 ANSI 的端口声明；对模块头端口 `clk` 的不带赋值的线网声明（如非 ANSI 写法中的 `wire clk;`，v0.5 澄清，RV-07）；G6 允许的 `posedge clk` 事件控制。作为数据、条件或表达式操作数出现即拒绝 | 附加提交格式限制：不把时钟用作数据或条件 | 分词器：名为 `clk` 的 `ident`/`esc_ident` 只允许 (a) 紧跟在 `posedge` 之后；(b) 在模块头（`module` 到结束模块头的 `;`）或端口声明语句（`input`/`output`/`inout` 到 `;`）中、不在方括号内、前一个记号是关键字或 `,` `(` `]`、后一个记号是 `,` `)` `;`；(c) RV-07：恰好是 `wire clk;` 这一语句（前一个记号是 `;` 或 `end`/`endfunction`/`endtask`/`endgenerate`/`endcase`，不在圆括号内，所在模块的模块头列出了端口 `clk`；注释已被丢弃，所以中间可有空白和注释）；`wire clk = …;`、`wire [0:0] clk;`、`wire clk, x;` 等其他形式仍是 G7 |
| G8 | `DECLARED_L` 在 1..3 之间 | `config/f1.cfg` 的 L_max（等于 3） | `declared_L` 必须是整数且在 1..3；行号 0（不对应 RTL 行） |
| unrecognized | 门槛无法识别：分词器不能识别的字符，Yosys 读取失败或描述无法使用，Yosys 与分词器的模块数不一致，或出现 `synopsys`/`synthesis` 开头的 `translate_off`/`translate_on` 注释（Yosys 会跳过其间的代码，导出的描述不再对应整个文件，RV-06） | 也是 `gate_reject`，原因单列，不当作已证明的规则违规 | 分词器的 `unknown` 记号（行号为该字符所在行）；被丢弃的注释（`//` 或 `/* */`）去掉前导空白后以 `synopsys` 或 `synthesis` 开头、随后（中间可有空白）是 `translate_off` 或 `translate_on`（不区分大小写）时记一条，行号为注释开始的行，注释照常丢弃，不根据 Yosys 的警告文字判断（RV-06）；两阶段读取的任何问题（行号取 Yosys 错误信息中的行号，没有时为 0）；模块数不一致（行号 0） |

## Yosys 读取方法（RV-01，两阶段）

Yosys 0.69+187（WSL Ubuntu-24.04）。两次调用都经 `limits.run_limited(kind="yosys")`（60 s、stdout/stderr 各 10 MB），工作目录为候选文件所在目录，命令中只出现文件的基名：

1. **第 1 阶段（前端读取检查）**：`yosys -q -p "read_verilog <file>"`。只检查前端读取是否成功；不接 `proc`、不接 `write_json`。
2. **第 2 阶段（接口提取）**：第 1 阶段成功后，在**另一个全新的 Yosys 进程**中执行 `yosys -q -p "read_verilog -lib <file>; write_json <新目录>/ports.json"`。

- 不运行 `proc`、`hierarchy -top`、`synth`、`flatten` 或任何清理未使用模块的处理；用 JSON 的**完整模块集合**判定 G1、核对 G3。
- 任一阶段非零退出、超时、输出超限或不完整、进程清理失败或无法确认（`KILL FAIL`）、无法启动或监督失败，或者 JSON 不存在、为空、不是合法 JSON、缺少 `modules`/`ports`/`direction`/`bits`：记 `yosys_problem`，加一条 `unrecognized`；不使用任何旧 JSON（每次调用都在新建的目录里运行）。分词器的规则照常记录。
- 第 1 阶段的警告（例如隐式声明）只作为证据保存在 `<工作目录>/<新目录>/stage1.err` 和 `evidence.json`，不据此拒绝（RV-01 第 5 条）。工作目录默认 `tasks/CASE-01/runs/gate/`（不进 git）。
- `translate_off`/`translate_on` 类注释会让 Yosys 跳过其间的代码（例如把一个多余的端口声明藏起来，使导出的端口只有 7 个），所以分词器发现它就记 `unrecognized`（RV-06），不依赖 Yosys 的输出或警告。其他综合控制注释（如 `// synopsys full_case`）不受这一条影响，按注释丢弃；放错位置时 Yosys 第 1 阶段可能读取失败，照常记 `unrecognized`。
- 门槛证明不了接口语义、复位语义、延迟和吞吐、仿真与综合是否一致、锁存器（规程 §7.2），这些由回归和作者审查（§7.3）处理。

### 验收记录（2026-10-21，WSL）

两阶段流程对 `revise/scripts/fixtures/gate/` 的全部样例和基线运行：合法写法（ANSI、非 ANSI 与 `wire`/`reg` 声明、`localparam` 表达式给出的端口位宽、转义模块名 `\dot4sat`）两阶段都 rc=0，JSON 给出 7 个端口和正确位宽；`localparam` 位宽错误时 JSON 给出 31 位；无法求值的位宽、重复模块名、语法错误、`$fopen`/`$value$plusargs`、找不到的 `` `include `` 在第 1 阶段 rc=1；未使用的第二模块、空第二模块、第二模块在前、转义名的第二模块都完整保留在 JSON 中；`parameter` 能读入，由 G4 拒绝。详细表格见执行台账（Task 4 报告）。

## 分词器（规程 §7.2"识别方法"）

| kind | 规则 |
|---|---|
| （丢弃） | `//` 到行尾、`/* … */`（含综合控制注释）、`"…"` 字符串（支持 `\"`）；未结束的块注释或字符串记一个 `unknown` |
| `translate` | RV-06：被丢弃的注释若是 `synopsys`/`synthesis` 加 `translate_off`/`translate_on`（见 `unrecognized` 一行），另记这个标记记号；它只产生 `unrecognized`，不参与其他规则 |
| `attr` | `(*` 到 `*)` 的属性，整体一个记号，之后不参与规则判断；`(*` 后（跳过空白）紧跟 `)`（即 `@(*)`、`@(* )`）时不是属性，按运算符处理；未结束的属性记 `unknown` |
| `esc_ident` | `\` 开头到下一个空白；`text` 为去掉反斜杠的名字；永远不当关键字 |
| `kw` | Verilog-2005 关键字（清单见下） |
| `ident` | `[A-Za-z_][A-Za-z0-9_$]*` 且不是关键字 |
| `systask` | `$[A-Za-z0-9_$]+`；`text` 保留 `$`，与 `grade.LINT_SYSTF` 比较时去掉 `$` |
| `directive` | `` ` `` 紧跟标识符；`text` 含反引号 |
| `number` | 十进制、实数、带位宽和进制的字面量（如 `34'sd2147483647`、`32'h7FFF_FFFF`、`'b0`；位宽与 `'` 之间不留空白） |
| `delay` | `#` |
| `op` | 其余标点和运算符 |
| `unknown` | 以上都不匹配的字符（例如非 ASCII 字符、单独的 `` ` ``、`$`、`'`、`\`） |

`line` 为该记号第一个字符所在的行号。同一 (规则, 行号, 性质) 只记一次。`gate.json` 中每条有行号的记录带 `text`（该行原文，不含换行符）；行号 0 的记录 `text` 为 `null`。

### Verilog-2005 关键字清单（IEEE 1364-2005 附录 B，124 个）

`always` `and` `assign` `automatic` `begin` `buf` `bufif0` `bufif1` `case` `casex` `casez` `cell` `cmos` `config` `deassign` `default` `defparam` `design` `disable` `edge` `else` `end` `endcase` `endconfig` `endfunction` `endgenerate` `endmodule` `endprimitive` `endspecify` `endtable` `endtask` `event` `for` `force` `forever` `fork` `function` `generate` `genvar` `highz0` `highz1` `if` `ifnone` `incdir` `include` `initial` `inout` `input` `instance` `integer` `join` `large` `liblist` `library` `localparam` `macromodule` `medium` `module` `nand` `negedge` `nmos` `nor` `noshowcancelled` `not` `notif0` `notif1` `or` `output` `parameter` `pmos` `posedge` `primitive` `pull0` `pull1` `pulldown` `pullup` `pulsestyle_ondetect` `pulsestyle_onevent` `rcmos` `real` `realtime` `reg` `release` `repeat` `rnmos` `rpmos` `rtran` `rtranif0` `rtranif1` `scalared` `showcancelled` `signed` `small` `specify` `specparam` `strong0` `strong1` `supply0` `supply1` `table` `task` `time` `tran` `tranif0` `tranif1` `tri` `tri0` `tri1` `triand` `trior` `trireg` `unsigned` `use` `uwire` `vectored` `wait` `wand` `weak0` `weak1` `while` `wire` `wor` `xnor` `xor`
