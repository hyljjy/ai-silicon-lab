# CASE-01 阶段 B 修订记录（规程第 3 节"修订"）

所有修订都发生在第一档预登记标签之前、任何正式答复出现之前（规程第 3 节"修订"第一种情况）。实现计划 `revise/impl_plan.md` 只在本机、其 sha256 将登记进预登记清单，所以**不改动计划文件本身**；计划受影响的条文在这里逐条写明替换内容，实现以本文件为准。

## RV-01 门槛的 Yosys 读取方式（规程 §7.2；计划 Task 4）

- **发现**：2026-10-20 执行计划 Task 4 Step 1 核实。计划命令 `yosys -q -p "read_verilog rtl/dot4sat.v; write_json <out>"` 在 Yosys 0.69+187（git sha1 2f08661dd，WSL Ubuntu-24.04）上 rc=1、JSON 0 字节，报错 `ERROR: Module dot4sat contains processes, which are not supported by JSON backend (run `proc` first).` 按计划停下。
- **备选与审查**：(a) 中间加 `proc`；(b) `read_verilog -lib`。两种只读探测都得到与合同 §1 一致的 7 个端口（`runs/revise-yosys-probe*.json`，不进 git）。Codex 只读审查 `docs/review/CASE01_BC2_codex.md` §2.1 认为 `proc` 超出"只读入"、会让门槛依赖过程降低阶段的警告；`-lib` 单独使用会丢掉模块体的前端检查；推荐两阶段。
- **作者决定**（2026-10-21）：采用两阶段。
- **修订后的规则**：规程 §7.2"识别方法"已改（v0.5）。实现要求：
  1. 对原始候选执行一次普通 `read_verilog`（不接 `proc`、不接 `write_json`），只检查前端读取是否成功；
  2. 成功后在**另一个全新 Yosys 进程**中执行 `read_verilog -lib <rtl>; write_json <out>`；
  3. 不运行 `hierarchy -top`、`synth`、`flatten` 或清理未使用模块的操作；用 JSON 的完整模块集合和分词器的 `module` 个数核对 G3，唯一模块名为 `dot4sat`；G1 按端口名、方向和 `len(bits)` 判定，不比较 `bits` 编号；
  4. 任一步非零退出、超时、输出不完整或 JSON 无法识别：记 `yosys_problem`，按"门槛无法识别"处理，不用旧 JSON；两次调用都经 `limits.run_limited(kind="yosys")`，各自保存退出状态和诊断；
  5. 普通读取中的警告保留为证据，不新增"有 warning 即拒绝"的规则；不根据候选内容切换读取方案；
  6. 分词器确认的 G3 违规照常记录，JSON 数量不一致另记 `unrecognized`，不互相掩盖。
- **计划条文替换**：Tech Stack"只用 `read_verilog` 和 `write_json`，不综合"→"普通 `read_verilog` 做前端读取检查，独立进程的 `read_verilog -lib` 与 `write_json` 提取接口；不运行综合处理 passes"。Task 4 `yosys_ports` 的单次命令 → 上面的两阶段流程。Task 4 `structure_rules` 增加"核对完整模块集合，不做顶层选择或删除未使用模块"。Task 4 Step 2 夹具补：ANSI/非 ANSI 与 `wire`/`reg` 声明、端口位宽引用 `localparam` 表达式（正确、错误、无法求值）、`parameter` 由 G4 拒绝、未使用第二模块、空第二模块、第二模块在前、重复模块名、转义模块名、语法错误。Task 4 Step 1 改为对这些边界样例先跑两阶段流程验收，结果写进台账；任何合法写法不能被可靠读取时停下重新选方案。
- **影响范围**：Task 4（尚未实现）、`gate_rules.md`、Task 11 `round.py` 的门槛接线（真实门槛落地后补测）。不影响已提交的其他脚本。
- **验证**：上述验收样例与 Task 4 测试，WSL 跑通后记入台账。

## RV-02 `L`、`function` 预测行的字段（规程 §10.1；计划 Task 9 模板）

- **发现**：Codex `CASE01_BC2_codex.md` §2.3 指出规程 v0.4"其余字段留空"有歧义：若模型把 `id`、`metric` 也留空，预测对象无法识别（`judge.py` 依赖 `metric`）。
- **作者决定**（2026-10-21）：采纳澄清。
- **修订后的规则**：规程 §10.1 已改（v0.5）：每行保留 `id`、`metric`，填写适用的 `action`、`basis`；`L` 只填整数 `point`，`function` 只填 `point` = `pass`/`fail`；`check corner category value_kind direction low high unit` 留空。`constraints.md`、`round1_template.md` 同步。
- **影响范围**：Task 9 模板（未提交，随作者检查点 1 定稿）。抽取和判定代码不变。

## RV-03 `grade_fail` 缺少最终判定行时的反馈标题（规程 §11；计划 Task 8）

- **发现**：Codex `CASE01_BC2_codex.md` §2.3 指出 `grade_fail` 也覆盖"没有最终判定行且无外部故障证据"的情况，此时反馈首行写"GRADE FAIL"与事实不符。
- **作者决定**（2026-10-21）：采纳。
- **修订后的规则**：规程 §11 已改（v0.5）：有最终 `GRADE FAIL:` 行时反馈"GRADE FAIL"；缺少最终判定行时反馈"未取得最终判定行"并保留 `grade_status=indeterminate`；两者都提供失败位置、日志摘要和已有结果字段。候选状态名不变，缺少最终行不因此获得重试资格。
- **计划条文替换**：Task 8 状态到模板映射中 `grade_fail` 一行，按有无最终行选择标题（同一模板文件，标题由渲染逻辑按 `final_line_missing` 决定）。
- **影响范围**：`revise/prompts/feedback/grade_fail.md`、`feedback.py` 及其测试。

## RV-04 判据行与抽取行逐条对应（规程 §10.1；计划 Task 7）

- **发现**：Codex `CASE01_BC1_codex.md` BC1-05：判据核验只查"已填判据能否找到抽取原文"，不查漏录和重复转写；重复编号的"只判第一条"会受判据行顺序影响。修复（提交 b27c85e）新增判据字段 `extract_index`，并要求一一对应、按抽取顺序。
- **作者决定**：2026-10-21 要求按 BC1 意见全部修复；本条是该修复所需的栏目补充。
- **修订后的规则**：规程 §10.1 判据表栏目补 `row_type`、`extract_index`、`comparator`，失败条件行 `fc_id`、`text`、`expr`（前三个之外的几项此前代码已在用、规程未列）；每条抽取的预测和失败条件恰有一行判据，按抽取顺序，预测按 `extract_index`、失败条件按 `fc_id` 对应。
- **计划条文替换**：Task 7"判据行"字段清单在 `prediction_id` 之后加 `extract_index`；`round.preflight` 的 evaluate 核验从"每个有预测或失败条件的编号都有判据行"改为"判据与抽取行一一对应"。
- **影响范围**：`judge.py`、`round.py`、`coverage.py`（只改文档）及测试。第 2 轮 `same_as` 行先按 `extract_index` 绑定本轮抽取行，再解析到第 1 轮 X（RV 之前的 R16 不变）。

## RV-05 输出上限报错证据的句式和位置（规程 §6.2；计划 Task 2）

- **发现**：计划 Task 2 Step 1 要求作者核对阶段 A 原始冒烟记录中上限报错的英文原文；Codex `CASE01_BC2_codex.md` §2.2 指出 `classify.py` 在任何事件的任何字符串字段里找 `output token maximum`，正常答复引用这句话就会被判交付失败、失去重试。
- **位置更正**：计划写的"封存的原始冒烟记录"有误。阶段 A 冒烟原始记录在 `D:\study\diag_sandbox\smoke-<时间>\`（见 `tasks/CASE-01/diag/smoke/summary.md`、`diag/scripts/run_round.py:406`），不在封存目录 `sealed\`。计划 Task 2 Step 1 条文以此为准。
- **作者核对结果**（2026-10-21，作者在本机运行只打印命中位置的脚本，操作者未打开原始记录）：2026-10-12 09:08 那次冒烟的 `claude-cap64.jsonl` 第 16、17 行，`deepseek-cap64.jsonl` 第 175、176 行，`kimi-cap64.jsonl` 第 116、117 行，三家相同：倒数第二个事件 `type=assistant` 的 `$.message.content[0].text` 与最后一个事件 `type=result` 的 `$.result`，原文以 `API Error: Claude's response exceeded the 64 output token maximum. To configure this behavior, set the CLAUDE_CODE_MAX_OUTPUT_TOKENS` 开头；大小写一致地包含 `output token maximum`；三家的 `*-cap64.err` 均不含该短语；三家记录中均没有 `max_tokens`。
- **作者决定**（2026-10-21）：核对后收窄（AskUserQuestion 选项"等我核对后收窄"）。
- **修订后的规则**（规程 §6.2 已改，v0.5）：
  1. 继续在全部可读事件中收集上限证据，不因记录不完整提前返回；
  2. 证据一：任一事件的 `stop_reason == "max_tokens"`（含 `message.stop_reason`），照规程保留；
  3. 证据二：`type == "result"` 事件的 `result` 字段，或 `type == "assistant"` 事件 `message.content[i].text` 字段，**以** `API Error: Claude's response exceeded the <一个或多个数字> output token maximum.` **开头**（区分大小写，按上面原句的固定前缀匹配）；
  4. 其他位置、正文中间出现的同一短语都不算上限证据；坏行（`_unparsed`）中的文字也不算（阶段 A 解析器只保留前 200 字符，无法确认归属）；
  5. 多轮本身不是上限证据（照旧）。
- **计划条文替换**：Task 2 `classify` 的"任一事件的任何字符串字段中出现 `CAP_HIT`"改为上面第 3 条；`CAP_HIT` 常量改为固定前缀的正则。
- **影响范围**：`classify.py`、`test_classify.py`、`fake_claude_b.py`（假 CLI 的上限场景须产生上面的事件形态），以及可能引用 `CAP_HIT` 的 `run_revise.py` 测试。

## RV-06 `translate_off` 类综合注释（规程 §7.2；计划 Task 4）

- **发现**：Task 4 审查（2026-10-21）用探针复现：非 ANSI 模块头写 `, dbg`、把 `output dbg;` 包在 `// synopsys translate_off … translate_on` 里，`gate.py` 给出 `GATE PASS`——Yosys 只看到 7 个端口，仿真器看到 8 个；G1"不多不少"被绕过。分词器按规程把综合控制注释当注释丢弃，Yosys 却遵守它。其余规则（G2、G4–G7）不受影响，因为分词器仍看得到其间的代码。
- **作者决定**（2026-10-21）：记为"门槛无法识别"；暂不在 `constraints.md` 里告知模型。
- **修订后的规则**：分词器丢弃的注释（`//` 或 `/* */`）去掉前导空白后以 `synopsys` 或 `synthesis` 开头、随后是 `translate_off` 或 `translate_on`（不区分大小写）时，记 `Hit("unrecognized", 行号, "extra")`；该注释照常按注释丢弃。不根据 Yosys 的警告文字判断（RV-01 第 5 条）。`gate_rules.md` 的 `unrecognized` 一行同步写明。
- **影响范围**：`gate.py`、`test_gate.py`、`gate_rules.md`。

## RV-07 G7 允许对端口 `clk` 的线网声明（规程 §7.2；计划 Task 4）

- **发现**：Task 4 实现按 G7 字面把非 ANSI 写法中单独的 `wire clk;` 判为违规；按 IEEE 1364-2005 这是对端口的线网声明，不是端口声明，但 G7 的目的是"不把时钟用作数据或条件"。
- **作者决定**（2026-10-21）：允许。
- **修订后的规则**：G7 允许位置增加"对模块头端口 `clk` 的不带赋值、不在括号内的线网声明（只限 `wire clk;` 这一形式，可带空白和注释；只在模块顶层，不在 generate、begin/end、function、task 等块内——块内的 `wire clk;` 声明的是遮蔽端口的新局部线网，Task 4 第 3 轮审查后补，提交 b68dfbb）"；带赋值（`wire clk = …;`）或出现在其他位置仍按 G7 拒绝。
- **影响范围**：`gate.py`、`test_gate.py`、`gate_rules.md`。

## 实现中补充的外部故障证据规则（计划 Task 5；记录备查，Codex `CASE01_BC3_codex.md` BC3-S2）

- **包装器中断（计划外部证据第 5 条）的收窄**：恢复时只有生命周期记录没有 `ended_at`，或记录因包装器自身被中断而结束（`abort_error == "interrupted"`），才计为 `wrapper_interrupted`；正常结束（有 `ended_at`、未中止）但 stdout 没有最终行的尝试不算外部证据（Codex BC1-03 对 R17 的意见，提交 c0be537）。
- **包装器监督失败**：`grade.py` 启动之后包装器自身的监督失败（`SupervisionError`：生命周期记录或输出文件写入失败、包装器内部异常）计为外部故障证据，与"启动 `grade.py` 本身失败"同类；清理失败或无法确认时仍写停止记录（控制会话裁决 R24，Codex BC3 无异议）。
- **记录中缺少包装器信号信息**（旧格式或 `launching` 记录）时，不把退出码或步骤的 `interrupted` 当作外部中断证据（裁决 R13）。
- **计划条文替换**：Task 5 `run_grade.attribution` 证据清单第 4、5 条按上述三点理解；第 2 条"`launch_error` 非空"只指 `Popen` 本身失败，启动后的失败归入监督失败。

## 作者检查点 1 的措辞修改（不涉及规程条文，记录备查）

作者 2026-10-21 决定全部采纳 Codex `CASE01_BC2_codex.md` §2.3 的措辞建议：删除 `round1_template.md` 附件前"这份答复只供参考，其中的判断不一定正确"；删除 `constraints.md` 末尾结果字段清单，第 83 行收敛为简短的阶段 A 查询语境说明；`round1_template.md` 失败条件提示收敛为"尽量写成可以用评估结果直接检查的条件"；演练题"只做格式检查"改为"交付结果将用于抽取和提交门槛检查，不运行 `grade.py`"；补充纯格式说明（不先复述模板、竖线写 `\|`、每条失败条件一个顶层 `- ` 项、表头用原始列名、声明行保持精确格式）；反馈日志标题改"日志末尾摘要（最多 40 个物理行）"；`unavailable` 的第 2 轮拼题顺序统一为"第 1 轮完整题目 → 自己的有效答复（若有）→ 第 2 轮规则 → 机械反馈 → 对应固定结尾"，第 1 轮题目只出现一次。这些属于计划 Task 9 Step 5 的正常定稿（介入日志记"人工修改"）。

## Task 4 命令行扩展（记录备查）

`gate.py` 命令行在计划写明的 `GATE PASS`/`GATE FAIL …`、退出码 0/1 之外增加：`--work-dir`、`YOSYS PROBLEM:` 行、基础设施故障（`KILL FAIL:`/`GATE ERROR:`）退出码 2 且不写 `--json`。基础设施故障抛 `GateInfraError`，永不写入 `gate.json`；`round.py` 遇 KILL FAIL 写评估侧停止记录（提交 1e98410）。

## 待定

- （无。Task 2 已核对并立 RV-05。）
