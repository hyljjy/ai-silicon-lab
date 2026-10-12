# 第 2 轮查询的执行细则（规程 v0.5 第 8 节；规程第 3 步预登记）

## 1. 查询单元（`scripts/extract_queries.py <代号>`）

由脚本确定性地抽取，作者复核。

- **范围**：从匹配"四、下一步查询"的那一行之后开始（"、"也可以是"."或"．"，前面可以有 `#`、`*` 等 Markdown 标记），到下一个以"五"加上述分隔符开头的标题行之前结束。找不到第四部分时，脚本报错退出；怎么处理由作者决定，并记入介入日志。
- **单元**：按出现顺序编号为 `<代号><序号>`，例如 `A1`、`A2`。分五种：

| 种类 | 什么算一条 | 存为 | 结果 |
|---|---|---|---|
| `codeblock` | ``` 代码块，整块算一条：标注为 `tcl`、`sdc` 或不标注语言的；以及标注为其他语言（`bash`、`shell` 等）、但第一条非注释行以命令名开头的。按内容判断，不只看语言标签 | `round2/q/<qid>.tcl` | 执行 |
| `nontcl` | 其他代码块，即第一条非注释行不以命令名开头、标注为其他语言的（`grep`、`python`、`yosys` 脚本等），整块算一条 | `round2/q/<qid>.txt` | 固定代码"需要模型外数据" |
| `inline` | 代码块之外，一行（一个列表项）中第一个词是命令名的行内代码。同一行里有几段，就按出现顺序合成一条查询，例如 `` `set_load …` `` 和 `` `report_checks …` `` 合成一条，`set_load` 才会对报告起作用 | `.tcl` | 执行 |
| `line` | 代码块之外、不含行内代码的行：去掉列表标记（`-`、`*`、`•`、`1.`、`1)`、`1、`、`（1）`、`(1)`），再去掉行首的标签（如 `**确认扇出**：`、`步骤 3:`）后，第一个词是命令名，算一条 | `.tcl` | 执行 |
| `text` | 代码块之外、不含命令的列表项 | `.txt` | 固定代码"未执行：未指明可执行的对象或命令" |

- 不是列表项、也不以命令名开头的普通文字，不算单元。
- **命令名**：`allow_query.txt`、`allow_whatif.txt` 和 `setup_commands.txt` 三张表中全部命令的并集，再加上其他时序工具的常用命令（`extract_queries.OTHER_STA`：`report_timing`、`get_timing_paths`、`report_constraint`、`report_global_timing`、`report_qor`、`all_fanin`、`all_fanout`、`get_attribute`、`report_timing_summary`、`report_design`）。后者在 OpenSTA 中不存在，执行后交还"语法错误"，而不是"未指明命令"；其中 `report_timing` 可按第 3 节 R3 改写。
- 代码块和行内代码中，Tcl 基本命令（`set`、`puts`、`foreach`、`for`、`if`、`while`、`expr`、`llength`、`lindex`、`lsort`、`catch`）后面带参数时也算命令；普通文字行不算，所以 "set the load to 0.1" 这样的句子不会被当成查询。
- 脚本同时写出 `round2/extracted_<代号>.tsv`，列为 `qid kind line file fixed_code`。
- 作者复核抽取结果。认为有误时可以修改，每处修改和理由都记入介入日志，文章中报告修改的处数。
- 一条查询里有多条命令时，整条放进同一个进程逐条执行，前一条出错不影响后一条（`diag_query.tcl`）。不同查询之间不共享变量。

## 2. 执行

- 每个 `.tcl` 单元用 `run_query.py --mode auto` 执行一次。不加 `--strict-log`：模型查询的报错本身就是结果，要原样交还。
- **对照运行**：查询中出现 `allow_whatif.txt` 里的命令时，整条查询自动转入对照运行（`whatif`）。这些命令会改变分析模型，包括改网表（`replace_cell`、`connect_pin` 等）、改约束、改负载、改单位和改分析条件。判断之前先去掉注释行。
- **`create_clock`**：`-period` 后面是字面数值，并且等于 T（27.91）时，按建环境的命令跳过，交还"环境已由冻结环境提供，未执行"；周期是其他数值或变量时，转入对照运行。判断只看周期：周期等于 T、但 waveform、端口或时钟名与冻结的 SDC 不同时，同样跳过。冻结网表中的 33 个寄存器都是上升沿触发的 `dfxtp_1`，所以下降沿的位置不影响本设计的 setup 和 hold 检查。
- **改写**：只有原样执行的输出中出现第 3 节的触发条件时，才改写，并且只改写一次，然后再执行一次。改写用 `rewrite_query.py <qid> <原样执行的运行目录>`，它打印用到的规则编号，没有用到任何规则时打印 `NONE`。
  - 改写前后的两次运行都保留。交还给模型的是改写后那次的输出，并在 `translation.tsv` 的 `rewrites` 一栏写明规则编号（例如 `R2`）。
  - 改写后仍然出错，就交还改写后那次的错误输出，不再改写。
- **工具异常退出**：查询让 OpenSTA 崩溃、超过 600 秒，或者输出超过 50 MB 时，结果代码为"工具异常退出"。交还结束前的输出，末尾附一行说明，例如"工具进程被信号 11 终止"（段错误）。环境核对照常判定，不受影响。

## 3. 机械改写表（只有下列两条）

触发条件是正则表达式，匹配 `query_full.txt` 中 OpenSTA 的原始报错行。

| 编号 | 触发条件 | 改写方式 |
|---|---|---|
| R2 | `^CASE01-ERROR: Error 514: .*'-corners' is not a known keyword or flag\.` | 独立的 `-corners` 选项改为 `-scenes` |
| R3 | `^CASE01-ERROR: invalid command name "report_timing"` | 命令名改为 `report_checks`，选项按下列对应关系替换：`-max_paths N` 改为 `-group_path_count N`；`-nworst N` 改为 `-endpoint_path_count N`；`-delay_type max` 或 `min` 改为 `-path_delay max` 或 `min`。其他选项保持原样 |

- 不在上表中的改写一律不做。需要操作者决定 scene 名、库的绑定，或者挑选对象的改写，都不属于机械改写。
- v0.3 草稿中的 R1（`-corner` 改为 `-scene`）和 R4（裸对象名套上 `get_pins` 等）已删除：OpenSTA 3.1.0 本来就接受 `-corner` 和裸对象名，这两条的触发条件永远不会出现（2026-10-11 核对）。
- 两条规则的触发条件，各用一条故意写错的查询在真实运行中验证过（实现计划的预验证记录）。

## 4. 结果代码

- 由 `run_query.py` 自动给出：已执行；语法错误；对象不存在；改变冻结模型的查询（已在单独运行中执行）；环境已由冻结环境提供，未执行；工具异常退出。
- 由 `extract_queries.py` 自动给出（`.txt` 单元）：未执行：未指明可执行的对象或命令；需要模型外数据。
- 操作者不写其他代码，也不写自由文字。

## 5. 截断

每条查询交还的输出最多 200 行。超过时，保留开头 100 行和结尾 100 行，由 `run_query.py` 自动完成。

## 6. 翻译表

`round2/translation.tsv`，列为 `code qid original executed rewrites collected fixed_code`：

- `original`：模型原文的单元文件；`executed`：实际执行的文件，没有改写时与 `original` 相同；
- `rewrites`：用到的规则编号，没有用到时写 `-`；
- `collected`：交还的那次运行在 `queries/round2/` 下的编号；`.txt` 单元写 `-`；
- `fixed_code`：`.txt` 单元的固定代码，其余写 `-`。

## 7. 复核

`extracted_<代号>.tsv`、`q/` 下的查询文件、`translation.tsv`、`queries/round2/` 和每个代号的 `<代号>_results.md`、`prompts/round2/<代号>.md`，在第 2 轮运行之前由作者复核并提交。`run_round.py --round 2` 会检查这些文件，以及第 1 轮的答复，都已经提交、没有改动，相关目录下也没有未提交的文件。
