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

## 作者检查点 1 的措辞修改（不涉及规程条文，记录备查）

作者 2026-10-21 决定全部采纳 Codex `CASE01_BC2_codex.md` §2.3 的措辞建议：删除 `round1_template.md` 附件前"这份答复只供参考，其中的判断不一定正确"；删除 `constraints.md` 末尾结果字段清单，第 83 行收敛为简短的阶段 A 查询语境说明；`round1_template.md` 失败条件提示收敛为"尽量写成可以用评估结果直接检查的条件"；演练题"只做格式检查"改为"交付结果将用于抽取和提交门槛检查，不运行 `grade.py`"；补充纯格式说明（不先复述模板、竖线写 `\|`、每条失败条件一个顶层 `- ` 项、表头用原始列名、声明行保持精确格式）；反馈日志标题改"日志末尾摘要（最多 40 个物理行）"；`unavailable` 的第 2 轮拼题顺序统一为"第 1 轮完整题目 → 自己的有效答复（若有）→ 第 2 轮规则 → 机械反馈 → 对应固定结尾"，第 1 轮题目只出现一次。这些属于计划 Task 9 Step 5 的正常定稿（介入日志记"人工修改"）。

## 待定

- **Task 2 上限证据的范围**：作者 2026-10-21 决定先按 `CASE01_BC2_codex.md` §2.2 的步骤核对阶段 A 三家 `cap64` 原始记录，再按核实到的事件类型、字段路径和句式收窄 `classify.py` 的文本证据，届时另立 RV-04。
