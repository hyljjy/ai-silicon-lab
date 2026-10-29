# CASE-02 附录 A 草稿：命令核实与 mutation 预验证结果

> 状态：**第 2 版，2026-10-28，随规程 v0.3 定稿（作者审定）。** 第 1 版写于 2026-10-20；第 2 版按 Codex 外审 `docs/review/CASE02_R3_codex.md` 和操作者自查 `CASE02_R3_claude_selfcheck.md` 修订，处理说明见 `CASE02_R3_claude.md`。改动：补做两项实测（1.7 反例校准、1.8 六 scene 时限），改正三处事实错误，收窄第 3 部分"完整确认"的结论，重写"需要修订的条款"。不改 `protocol.md` 正文。2026-10-28 晚：作者定了 Q1–Q5（Q2 改为按需重定上限并公开），据此出了规程 v0.3；Codex R4 审后"改后合入"，M1–M7、S1–S5 已落实，本附录同步改了 1.7、1.8、3.2 三处措辞；作者 2026-10-28 定 R4 Q1、Q2 后审定合入。本文"需要修订的条款"表记录的是对 v0.2 的修订要求，已全部进入 v0.3（落点见 `docs/review/CASE02_R4_codex.md` 第 2 节的对照表）。
> 环境：WSL Ubuntu-24.04，用户 eda，OpenSTA 3.1.0（commit 7a034b56），`env/snapshot.sh check` 在 2026-10-28 重跑为 `SNAPSHOT OK`（10-20 的实测只核对了工具版本和 `SKY130_KIT` 路径，没有跑快照核对）。
> 实测方式的限制：探针通过 `probe/run_probe.sh` 直接启动 `sta`，安全解释器时限设为 600 s（阶段 A 执行器是 300 s；只有 1.8 节的 q12 用了 300 s），**没有经过**阶段 A `run_query.py` 的进程监督、50 MB 输出上限和 200 行截断交还链。本文的行数是从原始输出按阶段 A 的计数规则算出来的，不是一次"经正式交还链交还成功"的记录；这一步留给 CASE-02 自己的执行器验收（见修订条款 7）。
> 原始输出产生于 `tasks/CASE-02/scratch/`（不进 git；原件整目录归档到 `D:\study\eda_archive\case02\prevalidation\`）；最小证据集和清单在 `tasks/CASE-02/prevalidation/`（进 git，`README.md` 有索引和重跑步骤，`MANIFEST.tsv` 有每个文件的去向和哈希）。下文的路径都相对于 `scratch/`，与 `prevalidation/` 中的同名路径一一对应。
> 全部数值只在固定模型下、std 六个 PVT 点内成立（综合后、理想时钟、不读寄生、只计引脚电容）。

## 0. 先说大白话

把 64 根 `in_b` 输入线的"到达时间要求"从约束里拿掉之后，工具不会报错；这 64 根线仍然接在寄存器上（结构连通性不变），只是普通的受约束时序查询不再返回它们的路径，相当于从时序分析里"隐身"了。隐身的后果有三个，都实测到了：

1. `check_setup` 会直说：**"有 64 个输入端口缺 set_input_delay"**，加 `-verbose` 还会把 64 个名字一个个列出来。它的返回值从 1 变成 0。
2. 任何从 `in_b` 出发的普通时序查询都变成 **"No paths found."**；加 `-unconstrained` 才能看到路径，而且路径头上会明确写 **"Path Group: unconstrained"**、**"(Path is unconstrained)"**，起点也不再写 "clocked by clk"。
3. 六个 PVT 点的最差 setup slack 都**略微变好**（最多好 0.017 ns），最差路径的起点从 `in_b[2]` / `in_b[35]` 换成 `in_a[34]` / `in_a[3]`；hold 这一边六个点**一个数都没变**。

对模型最关键的问题——"只用允许的只读命令，模型能不能自己查出这 64 根线、并且分清 min 和 max 都缺了"——答案是**能，但要两条命令配合**：一条 `check_setup -verbose` 给出"完全没有 set_input_delay"的端口全集（64 个名字，67 行含回显）；再用一个逐端口的循环（每个端口一行 `report_arrival -scene …`）看每个端口有没有参考时钟、min 和 max 到达时间各是多少。两条缺一不可：第 1.7 节的校准表明，`report_arrival` 分不清"完全没设 delay"和"设了不带时钟的 0 delay"，`check_setup` 分不清"min 和 max 都没设"和"只设了一侧"，合起来才能把两种混淆都排除。两条对 130 个输入合计 198 行（按阶段 A 的计数规则算出，没有经正式交还链实跑），刚好不超过 200 行；只对 64 个目标端口做则是 132 行。所以"完整定位"**可以评价**，但门槛和范围要写死，而且要公平地告诉模型执行环境的限制（第 3 部分、修订条款）。

另外发现两件影响实现的事：安全解释器里 `puts` 和 `report_*` 命令的输出会乱序，循环里要加 `flush stdout`；`-format summary` 对无约束路径在 Slack 列印的是**到达时间**（25.96），不是 slack。

## 方法

| 项 | 做法 | 位置 |
|---|---|---|
| 正确版上下文 | 驱动脚本 `sta_run_case02.tcl` = F1 冻结 `scripts/sta_run.tcl`（sha256 `6728b0a4…`）的逐字节复制，只改第 24 行为 `source $::env(SDC_FILE)`；其余顺序（库 → link → scene → SDC → 记录）不变 | `sta_run_case02.tcl`、`driver.diff` |
| 环境变量 | `TOP=dot4sat NETLIST=<F1>/synth/netlist.v T_NS=27.91 CLOAD_PF=0.0024 SCENESET=std CASE_DIR=<F1>/inputs`，与 F1 的 `steps.json` 一致 | `run.sh` |
| 缺失版 SDC | `case02_missing_inb.tcl`（sha256 `04fcba3e…`）：`ins_drive` 130 位、`ins_delay` 66 位 | 同名文件 |
| 每个版本跑两次 | `sta -no_init -no_splash -exit`，独立新进程 | `runs/{correct,missing}_{1,2}/` |
| 安全解释器实测 | `probe/safe_query.tcl` = 阶段 A `diag/scripts/diag_query.tcl` 的复制，只改第 8 行（环境由上面的驱动重建）；命令表原样读 `tasks/CASE-01/diag/rules/`；每条探针跑完都核对重建的记录文件与 `runs/<kind>_1` 逐字节相同（全部 20 次都相同，见各 `cmd.txt` 的 `env_records_identical_to_runs/…=1`） | `probe/`、`probe_out/` |

命令：

```bash
wsl -d Ubuntu-24.04 -u eda --exec bash -lc '/mnt/d/study/ai_native_design/tasks/CASE-02/scratch/run.sh correct_1 correct'
wsl -d Ubuntu-24.04 -u eda --exec bash -lc '/mnt/d/study/ai_native_design/tasks/CASE-02/scratch/probe/run_probe.sh q1_checksetup_missing missing q1_checksetup.tcl'
```

## mutation 预验证（规程第 4.2 节、第 5.2 节 `expanded.sdc` 一行）

| 核对项 | 结果 | 证据 |
|---|---|---|
| 正确版 `expanded.sdc` 与 F1 | sha256 相同，`c4e85ff0…` | `runs/correct_1/expanded.sdc` |
| 正确版全部记录文件与 F1 `sta/` | 除本目录自加的 `cmd.txt` 外，**全部逐字节相同**，包括 `sta_results.tsv`、12 个 `dcalc_*.txt`、24 个 `cat_*.rpt`、12 个 `path_*.rpt`、空的 `sta.log` | `cmp` 逐文件 |
| 缺失版 `expanded.sdc` 与正确版 | `diff` 只有一个块 `141,268d140`：删 128 行、增 0 行；删掉的 128 行与 F1 第 141–268 行逐字节相同；其中 `-min` 64 条、`-max` 64 条，覆盖 `in_b[0]`–`in_b[63]` 64 个不同端口名各一次 | `expanded_correct_vs_missing.diff`（sha256 `5671299f…`） |
| in_b 的 64 条 `set_driving_cell` | 缺失版里仍有 64 条（移到第 313–376 行，内容不变） | `runs/missing_1/expanded.sdc` 379 行 |
| 128 条目标清单草稿 | `mutation_lines_draft.txt` = F1 `expanded.sdc` 第 141–268 行原文，sha256 `49ecff73…`；可直接作为 `rules/mutation_lines.txt` | 同名文件 |

## 第 1 部分：候选命令在缺失版上的实际行为

### 1.1 `check_setup`（`probe_out/q1_checksetup_{missing,correct}/query.txt`）

| 命令 | 缺失版返回值 | 缺失版打印 | 正确版返回值 / 打印 |
|---|---|---|---|
| `check_setup` | 0 | 1 行：`Warning: There are 64 input ports missing set_input_delay.` | 1 / 无 |
| `check_setup -verbose` | 0 | 上面那行 + 64 行端口名（每行两个空格缩进，字典序：`in_b[0]`, `in_b[10]`, `in_b[11]`, …, `in_b[9]`），共 65 行 | 1 / 无 |
| `check_setup -no_input_delay` | 0 | 同 `check_setup`（1 行） | 1 / 无 |
| `check_setup -verbose -no_input_delay` | 0 | 同 `check_setup -verbose`（65 行） | 1 / 无 |
| `check_setup -verbose -unconstrained_endpoints` | **1** | 无 | 1 / 无 |
| `check_setup -unconstrained_endpoints` | 1 | 无 | 1 / 无 |
| `-no_output_delay`、`-no_clock`、`-multiple_clock`、`-loops`、`-generated_clocks`（各带 `-verbose`） | 1 | 无 | 1 / 无 |
| `check_setup -bogus_option` | 报错 | `Error 562: …, check_setup -bogus_option is not a known keyword or flag.` | 同 |

- 返回值语义：1 = 没有任何警告，0 = 至少有一条警告（与合同第 4.5 节"返回 1 表示没有警告"一致）。缺失版 `CHECK_SETUP` 记录为 0。
- `-unconstrained_endpoints` 在缺失版返回 1：这 64 个端口到达的每个寄存器 D 端仍然被别的受约束输入（`in_a`、`rst`、`in_valid`）到达，终点本身都有时钟，所以**没有"无约束终点"**。这个选项对本次缺失不敏感，不能作为证据。
- 警告正文和 64 行端口名由 OpenSTA 写到 stdout，所以同时出现在 `sta.log`（正式运行时由驱动第 30 行的 `check_setup -verbose` 触发，`runs/missing_1/sta.log` 共 65 行）和查询输出里。
- 端口名单：65 行里去掉缩进后恰好是 64 个不同名字，与 `get_ports {in_b[*]}` 的 64 个名字集合相同（排序不同：`get_ports` 返回的顺序是 `in_b[63]` 到 `in_b[0]`，`report_object_full_names` 按字典序）。

### 1.2 `report_checks` / `find_timing_paths`（`probe_out/q2_reportchecks_*`、`q4_perport_*`）

scene 固定为 `ss_n40C_1v60`。"行数"指该命令在查询输出里占的行数（不含命令回显行）。

| 命令 | 缺失版 | 行数 | 正确版 |
|---|---|---|---|
| `report_checks -path_delay max -from [get_ports {in_b[*]}] -scene ss_n40C_1v60` | `No paths found.` | 1 | `in_b[2] → _12026_/D`，slack −4.19 |
| 同上 `-unconstrained` | `Startpoint: in_b[2] (input port)` / `Endpoint: _12026_ (rising edge-triggered flip-flop)` / `Path Group: unconstrained` / `Path Type: max` / `Corner: ss_n40C_1v60`；路径第一行 `0.00 0.00 ^ input external delay`；末尾 `25.96 data arrival time` 和 `(Path is unconstrained)`；**没有** `clock clk (rise edge)`、`data required time`、`slack` 行 | 53 | 与不带 `-unconstrained` 完全相同（`clocked by clk`，`Path Group: clk`，slack −4.19） |
| `report_checks -path_delay min -from [get_ports {in_b[*]}] -scene …` | `No paths found.` | 1 | `in_b[0] → _12026_/D`，slack 0.61 |
| 同上 `-unconstrained` | `in_b[0] → _12026_`，`Path Group: unconstrained`，`Path Type: min`，`0.72 data arrival time`，`(Path is unconstrained)` | 19 | 普通路径 |
| `find_timing_paths -from [get_ports {in_b[*]}] -to [all_registers -data_pins] -path_delay max -scenes … -unconstrained` | 返回 1 个 PathEnd 句柄；`get_property $pe startpoint/endpoint/slack` = `in_b[2]` / `_12026_/D` / **`INF`** | 1 | 1 个，slack −4.189726 |
| 同上不带 `-unconstrained`（max 与 min） | 返回空列表（`llength` = 0） | 0 | 1 个 |
| `report_checks -path_delay max -from [get_ports {in_b[0]}] -scene …` | `No paths found.` | 1 | 普通路径，slack −1.51 |
| 同上 `-unconstrained` | `in_b[0] (input port)` → `_12026_`，无约束格式 | 50 | 普通路径 |
| `-format full_clock_expanded` | 与默认格式输出相同 | 50 | — |
| `-format summary`（无约束路径） | 表格一行，**Slack 列印 25.96**，这个数等于完整报告里的 data arrival time，不是 slack | 4 | Slack 列 −4.19 |

### 1.3 `-unconstrained` 的筛选语义（实测五条）

1. **不是过滤器，是"补集开关"。** 带 `-unconstrained` 时，受约束路径照常返回；只有当结果里没有受约束路径可报时，才用无约束路径填充。证据：正确版所有 130 个输入 `max_c=1 max_u=1`（`q5_enumerate_correct`）；缺失版 `-from {in_a[34] in_b[2]}` 带 `-unconstrained -group_path_count 4` 只给出 4 条 `in_a[34]` 的路径，`in_b[2]` 不出现；不带 `-from` 时缺失版给 `in_a[34]` −4.17，正确版给 `in_b[2]` −4.19（`q2_reportchecks_*`）。
2. **对纯无约束的起点集合，它是唯一能看到路径的办法**：`-from {in_b[*]}` 不带它 `No paths found.`，带它返回路径。
3. **无约束路径的 slack 是 `INF`**（`get_property`），完整报告没有 slack 行；`-format summary` 的 Slack 列会印出到达时间（25.96 / 25.95 / 25.94），不要当 slack 读。
4. **`-group_path_count` / `-endpoint_path_count` 不能枚举起点。** `-from {in_b[*]} -unconstrained -group_path_count 200 -endpoint_path_count 200 -format summary` 给出 200 行，起点只有 `in_b[2]` 和 `in_b[35]` 两个（加 `-unique_paths_to_endpoint` 同样）；`-to _12026_/D -group_path_count 300` 的 300 行里只有 10 个不同起点、没有一个 `in_b`。要覆盖 64 个端口只能逐端口查。
5. **按起点逐位查是可行的，而且 min/max 能分开**：`find_timing_paths -from $p -path_delay max|min -scenes … [-unconstrained]` 对 64 个 `in_b` 给 `max_c=0 max_u=1 min_c=0 min_u=1`，对其余 66 个输入给全 1（`probe_out/q5_enumerate_missing/query.txt`，130 行）。在默认参数（每组一条）下每个 `in_b` 的 max 和 min 各返回一个无约束 PathEnd，终点以 `_12026_/D` 为主（68/128）；返回一个不等于实际只有一条路径。

### 1.4 六点 `worst_slack` 与 TNS（`probe_out/q3_worst_tns_*`）

| scene | 正确版 WS max | 缺失版 WS max | 差 | WS min（两版相同） | 缺失版 TNS max（`total_negative_slack -scene`） |
|---|---|---|---|---|---|
| tt_025C_1v80 | 11.185458 | 11.191043 | +0.005585 | 0.093054 | 0.0 |
| tt_100C_1v80 | 11.317221 | 11.321179 | +0.003958 | 0.089830 | 0.0 |
| ss_100C_1v60 | −0.687278 | −0.679952 | +0.007326 | 0.185679 | −21.004392（正确版 −21.231488） |
| ss_n40C_1v60 | −4.189726 | −4.172595 | +0.017131 | 0.185004 | −129.940649（正确版 −130.488847） |
| ff_n40C_1v95 | 15.871505 | 15.881204 | +0.009699 | 0.063473 | 0.0 |
| ff_100C_1v95 | 15.894229 | 15.902846 | +0.008617 | 0.059113 | 0.0 |

- `worst_slack -scene <c> -max|-min` 六点都能取；`total_negative_slack -scene <c> -max|-min` 也能按 scene 取（TNS min 六点都是 0.0）。
- `report_tns`、`report_wns`、`report_worst_slack` **不接受 `-scene`**（`Error 562: …, report_tns -scene is not a known keyword or flag.`），它们不带 scene 的输出（`tns max -129.94`、`wns max -4.17`、`worst slack max -4.17`）数值等于 ss_n40C_1v60 的值，但输出里不写 scene 名。不带 `-scene` 的 `worst_slack -max`、`total_negative_slack -max` 同样。这些值不得复制成六点。
- `report_check_types -verbose -scene <c>` 在缺失版给出最差 min 路径（`rst → _12058_/D`，0.19）、最差 max 路径（`in_a[34] → _12026_/D`，−4.17）、max slew / max cap 违例和脉宽检查；可读，但一次 90 多行。

### 1.5 选项拼写与 scene 选择（`q2`、`q11_noscene_missing`）

- `report_checks` 接受 `-scene`、`-scenes`，**也接受 `-corner`**（三种写法输出相同）。`find_timing_paths` 接受 `-scenes` 和 `-scene`。与阶段 A 改写表"OpenSTA 3.1.0 本来就接受 `-corner`"一致。
- 不带 scene 选项时，`report_checks` 报告的是 **`Corner: ss_n40C_1v60`**（本网表六点中最差的那个）；`-format summary` 不印 Corner 行，所以 summary 格式下看不出是哪个 scene。
- `report_arrival`、`report_required`、`report_slack` 在多 scene 下**必须带 `-scene`**，否则 `Error 103: …, -scene keyword required with multi-scene analysis.`；一次只接受一个端口或引脚（两个端口时 `Error 128: …, pin must be a single port or pin.`）；没有 `-min_max` 选项。

### 1.6 逐端口的直接证据命令（`probe_out/q4_perport_*`、`q9_arrival_*`、`q10_flush_missing`）

| 命令 | 正确版 / 缺失版里受约束的输入（如 `in_a[0]`） | 缺失版 `in_b[k]` |
|---|---|---|
| `report_arrival -scene ss_n40C_1v60 [get_ports {in_b[0]}]` | `(clk ^) r 0.00:5.58 f 0.00:5.58`（参考时钟 clk、上升沿、rise/fall 各自的 min:max 到达时间） | ` r 0.00:0.00 f 0.00:0.00`（**没有 `(clk ^)` 前缀**，min 和 max 都是 0） |
| `report_required -scene … [get_ports {in_b[0]}]` | `(clk ^) r -1.29:1.92 f -0.86:2.64` | **空输出** |
| `report_slack -scene … [get_ports {in_b[0]}]` | `(clk ^) r 1.29:-3.66 f 0.86:-2.94` | **空输出** |
| `get_property [get_ports {in_b[0]}] slack_max` / `slack_min` | 数值（如 −3.662642 / 0.295775） | `INF` / `INF`（64 个全是） |
| `get_property … input_delay` / `clocks` / `arrival_max_rise` | `Error: port objects do not have a input_delay property.`（另两个同样） | 同 |
| `get_clocks -of_objects …` | `Error 562: …, get_clocks -of_objects is not a known keyword or flag.` | 同 |
| `report_edges -from [get_ports {in_b[0]}]` | 列出 21 条 wire 边（结构信息，不含约束） | 同；不区分有无约束 |
| `report_checks -from [get_ports {in_b[0]}] -scene … -unconstrained` | 普通格式 | 见 1.2：`Path Group: unconstrained`、`(Path is unconstrained)`、起点无 `clocked by clk` |

- **输出顺序问题。** 在安全解释器的一个循环里混用 `puts` 和 `report_arrival`，输出会乱序：`q9_arrival_missing/query.txt` 里 130 行 `report_arrival` 结果先出来，130 个端口名挤在最后一行。原因是 `puts` 走 Tcl 通道缓冲，`report_*` 由 C++ 侧直接写 stdout。在 `puts` 后加 `flush stdout`（安全解释器里可用）就恢复正确顺序（`q10_flush_missing/query.txt`：`in_a[0] (clk ^) r 0.00:5.58 f 0.00:5.58`、`in_b[0]  r 0.00:0.00 f 0.00:0.00`，130 行一一对应）。只用 `puts` 的循环（如 1.3 第 5 条）不受影响。

### 1.7 反例校准：六种约束状态下各命令打印什么（`probe_out/q13_calib_missing/query.txt`，2026-10-28 补做）

在缺失版上下文里用 whatif 模式给六个 `in_b` 端口分别加上不同的约束（真值就是所加的命令），然后用允许的只读命令读回来，看哪条命令能区分哪些状态。scene 为 `ss_n40C_1v60`。

| 端口 | 施加的约束（真值） | `report_arrival -scene` | `find_timing_paths` max_c/max_u/min_c/min_u | `slack_max` / `slack_min` | 在 `check_setup -verbose` 的缺失名单里？ |
|---|---|---|---|---|---|
| `in_a[0]` | 原约束（clk 上升沿，min 0 / max 5.582） | `(clk ^) r 0.00:5.58 f 0.00:5.58` | 1/1/1/1 | 数值 | 否 |
| `in_b[6]` | 什么都没设（本题的缺失状态） | ` r 0.00:0.00 f 0.00:0.00` | 0/1/0/1 | INF / INF | **是** |
| `in_b[0]` | `set_input_delay 0`，不带 `-clock` | ` r 0.00:0.00 f 0.00:0.00`（**与完全缺失一模一样**） | 0/1/0/1（**一模一样**） | INF / INF | **否** |
| `in_b[1]` | 只有 `-max 5.582` | `(clk ^) r ---:5.58 f ---:5.58` | 1/1/**0/0** | 数值 / INF | 否 |
| `in_b[2]` | 只有 `-min 0` | `(clk ^) r 0.00:--- f 0.00:---` | **0/0**/1/1 | INF / 数值 | 否 |
| `in_b[3]` | min 和 max，参考下降沿 | `(clk v) r 13.95:19.54 f 13.95:19.54` | 1/1/1/1 | 数值 | 否 |
| `in_b[4]` | 带时钟的 0（min 和 max 都是 0） | `(clk ^) r 0.00:0.00 f 0.00:0.00` | 1/1/1/1 | 数值 | 否 |
| `in_b[5]` | 只对 rise 设 min/max | `(clk ^) r 0.00:5.58 f ---:---` | 1/1/1/1 | 数值 | 否 |

能得出的结论：

- `report_arrival` 对"完全缺失"和"不带时钟的 0 delay"打印完全相同，所以它**单独不能**证明"没有设过 set_input_delay"；它能证明的是"该端口的到达时间没有相对任何时钟的参考、min 和 max 都是 0"。`---` 表示该侧没有约束，能分清只设一侧的情况；`(clk v)` 能分清参考沿。
- `check_setup -verbose` 的缺失名单只收录"一条 set_input_delay 都没有"的端口：只设一侧、不带时钟的 0 delay 都**不**在名单里（本次 64 减 6 = 58 个）。所以名单在、就排除了"不带时钟的 0 delay"这种混淆；名单本身不逐项展示 min/max、rise/fall 和参考关系（这是"报告没有逐项展示"，不是"工具不能区分"：只设一侧的端口确实不进名单）。
- 只设一侧时，另一侧的 `find_timing_paths` 带不带 `-unconstrained` 都为空（`in_b[1]` 的 min 是 0/0），`report_checks ... -unconstrained` 也打印空表。这正是第 5.3 节第四种状态"两类时序查询都为空，但结构路径存在"会出现的情形，不是工具异常。
- 因此第 5.5 节"完整确认"的证据必须同时有：名单（`check_setup -verbose`）**和**逐端口的 min/max 与时钟参考（`report_arrival -scene` 或等价的逐端口配对查询）。二者缺一都只到"端口名单完整、缺失项未分清"或"逐端口现象一致、但不能排除其他约束状态"。

### 1.8 六 scene 枚举与时限（`probe_out/q12_sixscene_missing/`，安全解释器时限按阶段 A 设为 300 s，2026-10-28 补做）

一个实例里跑六 scene 的 `report_arrival` 循环（780 行）加六 scene 的 `find_timing_paths` 循环（780 行）：进程 292.4 s（`cmd.txt`），查询部分约 270 s（按日志估计，未单独计时），`QUERY END rc=0`，**没有**触发 300 s 时限，但余量只有约 30 s；`query.txt` 原始 1566 行（82109 字节），其中含 BEGIN、END 两行，按阶段 A `split_log` 的计数是 1564 行；按 200 行规则会被截成头 100 尾 100，六个 scene 只剩第一个的开头和最后一个的结尾。注意 q12 只做了六 scene 的 `report_arrival` 和 `find_timing_paths` 枚举，**没有**包含 `check_setup -verbose`，所以它本身不是第 5.5 节要求的完整证据组合，只是目前已测的较长查询输出。单 scene 的 `find_timing_paths` 循环约 75 s（q5），`report_arrival` 循环约 3 s（q10）。只测了缺失版一次。

### 1.9 结构连通性与对象匹配（`probe_out/q6_fanin_*`，两版输出相同）

- `get_ports {in_b[*]}` 匹配 64 个，方向全部 `input`。
- `get_fanin -to [all_registers -data_pins] -startpoints_only -flat -trace_arcs all` 返回 130 个起点，64 个 `in_b` 名字全部在内；每个 `in_b[k]` 的 `get_fanout -from $p -endpoints_only -flat -trace_arcs all` 都是 32 个寄存器 D 端（`_12026_/D` … `_12057_/D`）。这是第 5.3 节第 3 层证据的做法，可直接用。

### 1.10 安全解释器边界与 whatif（`q7_safety_*`、`q8_whatif_*`）

- 查询模式下：`exec`、`write_sdc`、`sta::port_ext_pin_cap`、`source`、`open`、`set_input_delay` 都是 `invalid command name`；`report_checks > /tmp/x.txt` 被包装器拒绝（`CASE01: output redirection is disabled`）；`read_sdc`、`create_clock -period 27.91` 回 `SETUP_SKIPPED`。
- whatif 模式下在缺失版补 `set_input_delay -clock clk -max 5.582 / -min 0 [get_ports {in_b[*]}]`：`in_b[2]` 的路径重新出现、slack −4.19、`worst_slack` 回到 −4.189726、`check_setup -verbose` 回到 1。在正确版做同样的补写，输出不变。符合第 5.5 节的说法：补写后恢复只能支持假设。

## 第 2 部分：第 5.2 节各记录类型在缺失版中的具体输出

比较基线：`runs/correct_1`（与 F1 逐字节相同）。

| 对象 | 缺失版实测（相对正确版） | 稳定性（同一上下文跑两次） |
|---|---|---|
| `expanded.sdc` | 只少第 141–268 行（128 条），其余字节不变；sha256 `c3d62bdc…`，379 行 | 相同 |
| `BIND`（6 行）、`SCENES`、`MODE`（`default`）、`PORT`（164 行）、`LOAD`（33 行，2.4000000934092797e-15）、`OBJECTS`（`130 33 33 33`）、`TOPO`（`in2reg 130`、`reg2reg 0`、`reg2out 33`）、`DONE` | 逐字节相同 | 相同 |
| `LIB`（6 行） | 逐字节相同（同一台机器，路径 `/home/eda/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__<corner>.lib`） | 相同 |
| `CHECK_SETUP` | **`0`**（正确版 `1`） | 相同 |
| `WS … max`（6 行） | 六点都变大 0.0040–0.0171 ns，数值见 1.4 | 相同 |
| `WS … min`（6 行） | 逐字节相同 | 相同 |
| `CAT … in2reg max`（6 行） | slack 变化，起点变化：tt 两点和 ss_100C `in_b[35]`→`in_a[34]`，ss_n40C `in_b[2]`→`in_a[34]`，ff 两点 `in_b[2]`→`in_a[3]`；终点都还是 `_12026_/D` | 相同 |
| `CAT … in2reg min`（6 行） | 逐字节相同：`rst → _12058_/D`，六点数值不变 | 相同 |
| `CAT … reg2reg`（NONE）、`CAT … reg2out`（12 行） | 逐字节相同 | 相同 |
| `cat_<c>_in2reg_max.rpt`（6 个） | 变化：第 1 行起点名和路径体；表头、尾部格式不变 | 相同 |
| 其余 18 个 `cat_*.rpt` | 逐字节相同 | 相同 |
| `path_max_<c>.rpt`（6 个） | 变化（同上） | 相同 |
| `path_min_<c>.rpt`（6 个） | 逐字节相同 | 相同 |
| `dcalc_<c>_<min|max>.txt`（12 个） | 逐字节相同 | 相同 |
| `sta.log` | 正确版空文件；缺失版 65 行 = 警告行 + 64 行端口名（见第 4 部分） | 相同 |

- **稳定性结论**：`runs/correct_1` 与 `correct_2`、`runs/missing_1` 与 `missing_2` 的全部文件逐字节相同（`cmp` 无差异）；另外 20 次经安全解释器重建的环境记录也都与对应的 `runs/<kind>_1` 相同。记录文件在本机上逐字节稳定。
- **hold（规程第 4.2 节末条）**：六点 `WS min` 和 `CAT in2reg min` 都没变，全局最小 hold 仍是 `rst → _12058_/D`（ff_100C_1v95 下 0.059113）。缺 min delay 改变的是 in_b 的 hold **覆盖**，没有改变六点的最小 hold 数值。
- **`LIB` 路径规范化规则（建议写定）**：比较前把第 3 列按 `^.*/lib/(sky130_fd_sc_hd__[A-Za-z0-9_]+\.lib)$` 只保留文件名（等价于去掉 `$SKY130_HD/lib/` 前缀），第 2 列库名和规范化后的文件名必须相同；原始字节另存到 `lib_lines_raw.txt`；在同一台机器上原始字节也必须相同，两种比较分别报告。规范化不动库名、不动数量和顺序。
- **数值型记录的检查**（缺失版允许变化的 `WS max`、`CAT in2reg max`、6 个 `cat_*_in2reg_max.rpt`、6 个 `path_max_*.rpt`）：实测里只需要"文件齐全、scene 名正确、数值有限、`CAT` 的 slack 与同名 `cat_*.rpt` 的 slack 行一致（四位小数）"四项；没有发现表外差异。

## 第 3 部分：模型可见证据的三个层次（第 5.5 节）

前提：安全解释器只有 `rules/allow_query.txt` 的命令和 Tcl 基本命令（`foreach`、`puts`、`llength`、`flush` 等可用，1.10 节列的都不可用）；每个"查询 × 上下文"实例输出超过 200 行时截成头 100 + 尾 100（阶段 A `run_query.py` 第 141–147 行，**命令回显行计入 200 行**）；安全解释器时限 300 s、整个进程 600 s。本节的行数都已实测。

### 3.1 线索层

材料本身（CAT 起点变化、WS 变化、意图说明、"有效约束清单尚未提供"）就够；查询层面任何一条都算：`check_setup` 返回 0 或那行警告（1 行）、`report_checks -from {in_b[*]}` 的 `No paths found.`、六点 `worst_slack` 的差异。允许结论：提出缺失假设。

### 3.2 局部确认（某端口、某项）

下面任意一条对确切端口的输出，都构成该端口该项的直接证据：

| 查询 | 所需输出特征 | 证明的项 | 行数 |
|---|---|---|---|
| `report_arrival -scene <c> [get_ports {in_b[k]}]` | 没有 `(clk ^)` 前缀，`r 0.00:0.00 f 0.00:0.00` | 该端口的到达时间没有相对任何时钟的参考，rise/fall 的 min 和 max 都是 0.00；与本题的缺失一致，但**单独不能**排除"不带时钟的 0 delay"（1.7 节），要和 `check_setup` 名单配对才算该端口 min、max 都缺 | 1 |
| `report_checks -path_delay max -from [get_ports {in_b[k]}] -scene <c> -unconstrained` | `Path Group: unconstrained` 且 `(Path is unconstrained)` | 该端口 max 侧的**覆盖现象**（无受约束路径）；单独不能排除"约束存在但参考关系不同"（1.7 节：不带时钟的 0 delay 四项结果相同），要确认 max delay 项缺失还要名单 | ≈50 |
| 同上 `-path_delay min` | 同上 | 该端口 min 侧的覆盖现象，同上 | ≈19 |
| `find_timing_paths -from [get_ports {in_b[k]}] -path_delay max|min -scenes <c>` 为空而加 `-unconstrained` 非空 | `llength` 0 / 1 | 该端口对应侧的覆盖现象，同上 | 1–2 |
| `get_property [get_ports {in_b[k]}] slack_max` / `slack_min` | `INF` | 支持性证据（不带 scene，`INF` 也可能来自别的原因），单独不够 | 1 |

空输出要配对读：`report_required` / `report_slack` 对 `in_b` 是空输出，只有和同一命令对 `in_a` 的非空输出并列时才有意义。

### 3.3 完整确认（64 个端口名及 min/max 缺失、参考时钟与 rise/fall 语义明确）

**安全解释器内可以取得完整证据，但必须两类命令配合。** 验证过的命令组有三个（每个都可以对 R1、R2 各执行一个实例）：

| 组合 | 查询 | 输出 | 行数（含回显） | 给出什么 |
|---|---|---|---|---|
| I | `check_setup -verbose`（或 `-verbose -no_input_delay`） | 警告行 + 64 行端口名 + 返回值 `0` | 67 | 缺 `set_input_delay` 的端口**全集**（64 个名字）；不分 min/max，不含时钟语义 |
| II | `foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; flush stdout; report_arrival -scene ss_n40C_1v60 $p }`（只枚举 `get_ports {in_b[*]}` 则 64 行） | 130 行，每行 `端口名 [(clk ^)] r min:max f min:max` | 131（64 端口：65） | 每个输入的参考时钟、沿、rise/fall、min 和 max 到达时间；64 个 `in_b` 无时钟且 min/max 都是 0.00，其余 66 个 `(clk ^) r 0.00:5.58 f 0.00:5.58`。单独不能排除"不带时钟的 0 delay"（1.7 节） |
| III | `foreach p [all_inputs -no_clocks] { puts "[get_full_name $p] max_c=[llength [find_timing_paths -from $p -path_delay max -scenes ss_n40C_1v60]] max_u=[llength [find_timing_paths … -unconstrained]] min_c=… min_u=…" }` | 130 行 | 131 | 每个输入 max/min 各自是否受约束；不含时钟语义 |

**核心终点与范围扩展分开**（按 CASE02_R3 M3 改）：第 5.5 节"完整确认"的核心终点是**某一个已标明上下文（R1 或 R2）里全部 64 个目标端口的 min 和 max 缺失**，不要求同时证明另一上下文、其余 66 个输入或非目标配置。后三项是结论范围的扩展，各自另看证据覆盖：其余 66 个输入要靠把枚举范围扩到 130 个输入；另一上下文要靠对它也执行；非目标配置在允许命令里没有找到可读出的直接证据（见本节末）。

达到核心终点的证据条件（建议作为预登记文字；按证据内容判，等价写法同等接受）：

1. **名单**：有一条输出给出"完全没有 set_input_delay"的端口全集，且恰好是 64 个 `in_b`（实测只有 `check_setup -verbose` / `-verbose -no_input_delay` 能给，组合 I）；
2. **逐端口的 min/max 与参考**：对这 64 个端口每个都有一条输出显示 min 和 max 两侧的状态和有无时钟参考（组合 II 的 `report_arrival -scene`，或组合 III 加配对 `report_checks -unconstrained` 之类能分开 min/max 的逐端口查询）；
3. 1 和 2 **都要有**：只有 1 记"端口名单完整、缺失项（min/max）与参考关系未分清"；只有 2 记"逐端口现象与缺失一致，不能排除其他约束状态"（1.7 节）。两者都不是"部分端口"，也都不是完整确认；
4. 输出完整：承载 1 和 2 的实例没有被截断（按 CASE-02 执行器的实际计数方式，阶段 A 规则下 I + II 对 130 个输入是 198 行、对 64 个端口是 132 行，可放在同一实例；跨六 scene 的枚举必然被截断，1.8 节），没有 `ERROR` 行，`QUERY END rc=0`，实例的环境有效性核对通过；
5. 结论只覆盖所查的上下文和 scene：一个 scene 的观察标明 scene，不自动变成六点逐项确认；只查一组只能确认那一组。

`flush stdout` 的问题（1.6 节）是执行器该修的，不作为对模型的要求（修订条款 7）。

是否需要"完整定位不可评价"的声明：按上面的条件，完整证据在安全解释器内**可以取得**，所以倾向不需要；但这要等实现计划把执行契约（可用命令、行数、时限）写进 `context.md` 并经预演验证后才能定（修订条款 6、13），现在保留正文的条件出口。预登记时要写明：没有取得满足条件 1–5 的结果的模型，按"局部确认""名单完整但缺失项未分清"或"查询任务未完成"记，并按修订条款 10 标明未完成的归因，不记为"未利用充分证据"。

**不构成完整确认的例子（实测）：** 警告的数量 64；`-group_path_count 200` 的 200 行只含 `in_b[2]`、`in_b[35]` 两个起点；`-format summary` 里 25.96 那一列；whatif 补写后恢复。另外：第 5.5 节说"某端口报告缺少 'input external delay' 行"——实测无约束报告里**仍然有** `0.00 0.00 ^ input external delay` 这一行，缺的是 `clock clk (rise edge)`、`clock network delay (ideal)` 两行和起点的 `clocked by clk`（见修订条款 3）。

"只有这些项缺失、其他约束都正确"这个结论：组合 II 覆盖 130 个输入的 delay，不覆盖驱动单元、输出 delay、负载和时钟设置；这些在允许命令里没有找到可读出的直接证据（`get_property` 没有相应属性，`report_required` 对输出端口未实测）。所以模型能确认的最多是"所查上下文里 130 个输入的 delay 中只有 in_b 的 64 位缺失"，不能确认非目标配置都正确。建议第 7 节 F4 增加一档"端口集合完整、缺失项未分清"，F7 的"实际完成"附记"局部 / 目标集合完整 / 含其余输入"，范围按模型实际断言和实际证据分别记。

## 第 4 部分：第 5.6 节白名单候选

缺失版 `runs/missing_1/sta.log`（sha256 `59dd9b85…`，65 行）的全部内容由 `check_setup -verbose` 产生，正确版同文件为空。候选条目：

```
Warning: There are 64 input ports missing set_input_delay.
  in_b[0]
  in_b[10]
  …（字典序，共 64 行，每行两个空格缩进，与 sort 后的 get_ports {in_b[*]} 名字集合一致）…
  in_b[9]
```

- 理由：由 64 个 `in_b` 端口缺 `set_input_delay` 直接引起；端口数量和名单与 `rules/mutation_lines.txt` 的端口集合一致；只对缺失版生效。
- `logcheck.py` 的规则格式是 `<tool><TAB><python regex><TAB><reason>`，只对含 `warning` 的行匹配。所以白名单文件里能起作用的只有一条：`sta\t^Warning: There are 64 input ports missing set_input_delay\.$\t<理由>`（整行锚定）。64 行端口名不含 "warning"，logcheck 不会报它们，但也不会检查它们。`sta_results.tsv` 里的 `CHECK_SETUP` 记录只有返回值 `0`，没有名单，所以名单核对要单独写成对建环境日志（QUERY BEGIN 之前的部分）的**整块解析**：恰好一条该警告行，随后恰好 64 个互不相同的端口名，集合精确等于 `rules/mutation_lines.txt` 的端口集合；多块、少行、多行、非目标名都使 `run_valid` 为假。正确版和恢复版：`CHECK_SETUP` 为 1 且没有这一块（见修订条款 4）。模型自己在查询里调用 `check_setup` 再打印一遍，属于查询输出，不算建环境警告重复。
- 安全解释器查询里出现同一条警告时（模型调用 `check_setup`），按阶段 A 规则 `--strict-log` 只用于基础核对，模型查询输出不经 logcheck 判作废；若 CASE-02 执行器对查询输出也跑 logcheck，这条规则同样要生效。

## 需要修订的条款（与正文不符或正文待填的地方；第 2 版按 CASE02_R3 重排）

分三类：**填入**＝正文留白处填实测值，不改规则；**修订**＝改规则，进第 13 节版本记录；**决定**＝要作者先定。

| # | 条款 | 类别 | 内容 |
|---|---|---|---|
| 1 | 第 5.2 节 `CHECK_SETUP` 行、第 5.4 节 | 填入 | 缺失版 `check_setup -verbose` 返回 0。`-unconstrained_endpoints` 返回 1、无输出，对本缺失不敏感：保留为"对照现象"记录（它正好说明"终点都还有时钟"这个区别），不作为必查证据。 |
| 2 | 第 5.4 节 TNS | 填入 | 按 scene 用 `total_negative_slack -scene <c> -max`；`report_tns`、`report_wns`、`report_worst_slack` 不接受 `-scene`，不带 scene 的值只描述本次观察（等于 ss_n40C_1v60 的值），不写成固定规则。 |
| 3 | 第 5.5 节"不构成完整确认"一条 | 修订 | "某端口报告缺少 'input external delay' 行"与实测不符（该行仍在，值 0.00）。改为"某端口的无约束报告（`Path Group: unconstrained`，起点无 `clocked by clk`）只支持该端口该项，不支持集合"。 |
| 4 | 第 5.6 节与第 5.2 节 | 修订 | 两层检查：logcheck 白名单只登记锚定的警告行（规则文件用真实 TAB）；建环境日志的完整警告块另行解析（第 4 部分写法）。正确版、恢复版 `CHECK_SETUP=1` 且无该块；缺失版 `CHECK_SETUP=0` 且块恰好合规。 |
| 5 | 第 5.3 节第 4 层 | 填入 | "附录 A 验证过的完整枚举方法"＝逐端口配对查询（每端口 max/min 各一次、带与不带 `-unconstrained`，1.3 第 5 条、3.3 组合 III）；`report_arrival` 只报到达时间，不替代配对查询。`-group_path_count` 在本次实测里没有枚举出全部起点（只出现 2 个），不写成"任何情况下都不能"。 |
| 6 | 第 5.5 节结尾"完整定位不可评价"的出口 | 决定 | 按 3.3 的条件 1–5，完整证据可取得，倾向不声明；但要等执行契约公开（第 13 条）和预演通过后再定。暂保留正文出口。 |
| 7 | 第 6.4 节 / 实现计划 | 修订 | (a) 执行器包装器在每条 STA 命令前 `flush stdout`，预演用"循环里不写 flush"的假查询验收，不接受"在交还结果旁注明"；(b) 200 行上限的计数方式（含命令回显）写进正文；(c) 缺 `-scene` 的 `report_arrival/report_required/report_slack` 默认原样执行并交还 `Error 103`，若要改写必须预先规定确定性的 scene 选择和实例计数（作者决定，见处理说明 Q3）；(d) 执行器完成后用最终契约重跑一次验收：选定的完整证据组合、无 flush 循环、超 200 行的合法查询、一个超时或输出超限的固定样例，分别保存原始查询、有效上限、退出状态、完整输出、实际交还输出和计数。 |
| 8 | 第 4.2 节末条（hold） | 填入 | 预验证里六点 `WS min` 与最差 hold 路径（`rst → _12058_/D`）不变；保留"缺 min delay 改变的是 in_b 的 hold 覆盖"的限定，不扩写成所有 hold 分析未变。 |
| 9 | 第 4.2 节 WNS | 填入 | 预验证里六点 setup WS 改善 0.004–0.017 ns，最差起点换成 `in_a[34]` / `in_a[3]`；只作本机预验证观察，不升级为正式运行的必须方向或幅度。 |
| 10 | 第 6.4 节实例记录、第 7.1 节 F8、第 7.2 节、第 12 节 | 修订 | 增加独立的**归因**字段：请求本身的问题（已公开语法或对象错误）/ 流程限制（白名单拒绝、截断、时限、输出上限）/ 执行器或环境问题（输出乱序、包装器或环境失败）/ 原因未定。"查询任务未完成"保留，但带归因，不直接当作模型诊断能力不足。F8 补"超时、截断、输出超限、无法对应的输出"。第 12 节"缺失的评分字段记不适用"改为"因未取得有效答复或查询结果而不能评价的字段记'未取得 / 不可评价'并写原因；'不适用'只用于该字段在本轮没有评价对象"。 |
| 11 | 第 7.1 节 F4、F7 | 修订 | F4 增加"端口集合完整、缺失项未分清"一档；F7 的"实际完成"附记范围（局部 / 目标集合完整 / 含其余输入）。 |
| 12 | 第 10 节、第 6.1 节 | 修订 | 作者和操作者在每项工作或检查点结束时当场记本人主动分钟数，等待时间单列；事后补记标"事后估计"，无法恢复标"未记录"。第 6.1 节"残留差异沿用阶段 A 规程 §5.1 的八条"改为逐项标明"已复测 / 尚未复测 / 无法核实 / 仅属历史观察"并引证据。 |
| 13 | 第 6.2 节 `context.md` | 决定 | 是否向三家公开中性的执行契约：可用命令表和 Tcl 控制结构、文件与外部进程限制、建环境命令跳过规则、对照运行规则、每实例行数上限与截断方式、时限、多 scene 下要显式 scene、查询条数上限、第 2 轮新请求不执行。不公开诊断答案和推荐组合。 |
| 14 | 第 5.2 节记录比较 | 修订 | (a) `LIB` 规范化写成"只剥离已登记的库目录前缀，不匹配即拒绝"，库名与文件名分别比较，正则文本单独给出并注意 Markdown 转义；(b) 比较基线写明顺序：正确版对 F1，恢复版对本次正确版，查询重建环境对自己的正式上下文；(c) 比较的文件集合显式列出，F1 的后处理产物 `check.log`、`sta_check.json` 和本目录自加的 `cmd.txt` 排除；(d) 数值型记录除"齐全、scene 正确、数值有限、`CAT` 与 `cat_*.rpt` 一致"外，补核对报告类型、起终点，`WS` 与 `path_max_*.rpt`、`CAT` 与 `cat_*.rpt` 的对应关系，六位与四位打印的舍入规则预先写定。 |
| 15 | 第 8、12 节 | 修订 | 制定规则所依据的最小证据集（驱动差异、缺失版 SDC、128 条清单、关键探针的查询文件与输出摘要、完整哈希）纳入 CASE-02 归档并进第一档登记，不整包提交 scratch；后续运行用不可覆盖的唯一实例目录；第 12 节加"从干净克隆按文档完成离线核验与复现步骤"的要求（F1 基线需先按阶段 B 复现指南重建，因为 `runs/` 不进 git）。 |
| 16 | 第 3 节、第 9 节 | 修订 | 列出作者检查点清单（方法稿、附录 A 合入、实现计划、预演、第一档、三组有效性、第二档、两轮核心表、揭盲、笔记），每个在 `interventions.md` 记原话和时间；第 9 节目录加 `notes/decisions.md` 放看到正式答复之后的裁决。 |

v0.3 的版本记录应按"实测填入 / 证据门槛变化 / 评分状态变化 / 执行契约变化 / 有效性检查变化"分列，不只写"补齐附录 A"；状态行只在第 2 步确实完成后更新。

## 过程记录

- 15:48 跑 `q4_perport_missing` 时 WSL Ubuntu-24.04 被重启（`journalctl -b -1`：15:48:07 用户会话 exit.target，随后非正常关机，15:48:32 重新启动）。scratch 里的脚本没有任何 shutdown / terminate 之类的直接重启命令，原因未查明；q1–q3 结果完好，q4 起重跑，重跑后环境记录核对全部通过。记在这里供作者知悉。
- 2026-10-20 第 1 版：主动工时约 55 分钟（读规程与脚本 ≈15 分钟，搭环境与跑三组 ≈10 分钟，写探针与读结果 ≈15 分钟，写本附录 ≈15 分钟），都是事后估计；等待时间（OpenSTA 进程）约 8 分钟，单列。
- 2026-10-28 第 2 版：补做 q12、q13 并读结果约 15 分钟，写 Codex 请求和自查约 25 分钟，处理评审意见、改本附录约 40 分钟，合计主动约 80 分钟（事后估计）；等待 Codex 评审和两条探针约 30 分钟，单列。
