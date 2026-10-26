# 网表兼容性诊断结果（D-01 的 B 方案；事后补充诊断，不是预登记）

状态：**作者 2026-10-26 复核同意**（原话："诊断结果记录我看过，同意。提交 netlist_diagnosis_results.md。"）。依据：`revise/notes/netlist_diagnosis_plan.md`（作者 2026-10-25 确认，§9 补充 2026-10-26 确认）；脚本 `revise/diag_netlist/diag_netlist.py`（提交 f3cbd9e，sha256 3c587045e008b2937b1d6c35d0ae3010021cf34fde7b52522f797a9a5a12b642）。

**口径（计划 §7）**：以下数值是对已交付候选的综合网表实施已披露的兼容性处理（删去纯连线声明中的 `signed` 限定词）后，在冻结分析模型下测得的结果；不回填正式判定、状态或覆盖表，不计入改善或预测判定，不能写成"候选第一次交付即达到/未达到目标"。正式结果见 `outputs/r1/round_complete.json`、`outputs/r2/round_complete.json`。

## 1. 运行

- 时间：2026-10-26 07:53–07:56（WSL），两轮均已关闭（`round_complete.json` 已提交）之后；对应表未打开。
- 运行目录：`tasks/CASE-01/runs/revise-diag-netlist/`（不进 git）；备份 `D:\study\eda_archive\case01\revise\diag_netlist\`（逐字节一致，SHA256SUMS 488 行）。
evise\diag_netlist\`（逐字节一致，SHA256SUMS 488 行）。
- 运行记录：脚本已提交且未修改（git HEAD f3cbd9e）；返回码 0；无 STOP；无遗留进程。
- 纳入对象：F1 归档基线 + 第 1 轮 3 个 + 第 2 轮 3 个正式尝试（全部完成综合）；无未纳入对象。每个对象只运行一次。

## 2. 基线对照

基线（F1 归档原网表，无 `signed` 声明，转换为空操作）重放后，门级回归 `checked=2856`，`sta_check.json` 与 `sta_results.tsv` 与 F1 归档完全一致 → 重放流程本身无偏差（BASELINE CONTROL OK）。另外，第 2 轮 cand_u2pe 的网表同样无 `signed` 声明，其诊断 `sta_check.json` 与正式运行的完全相同，可作为第二个对照。

## 3. 转换记录

| 对象 | 删去 signed 的声明行 | 原网表 sha256（前 12 位） | 转换后 sha256（前 12 位） | 实例数（前/后） | 语义核对 | check_sta |
|---|---|---|---|---|---|---|
| baseline | 0 | 1fa89c975162 | 1fa89c975162 | 6046/6046 | pass | 原样重放 |
| r1_cand_983p_attempt1 | 8 | 2d7de9958169 | 09f0df039e97 | 6196/6196 | pass | derived（正式运行在 sta 失败，按 grade.py 补出） |
| r1_cand_9pbi_attempt1 | 16 | 12988caae38f | a1071e4fd324 | 6503/6503 | pass | derived（正式运行在 sta 失败，按 grade.py 补出） |
| r1_cand_wpml_attempt1 | 8 | b6f333b69a4c | 807458caa08b | 6380/6380 | pass | derived（正式运行在 sta 失败，按 grade.py 补出） |
| r2_cand_3yvg_attempt1 | 8 | d4c1227eb549 | 832edad86ae9 | 6198/6198 | pass | derived（正式运行在 sta 失败，按 grade.py 补出） |
| r2_cand_c1dx_attempt1 | 8 | 0098e13e1431 | 19ec0394d322 | 6196/6196 | pass | derived（正式运行在 sta 失败，按 grade.py 补出） |
| r2_cand_u2pe_attempt1 | 0 | c5fb0216bcee | c5fb0216bcee | 6523/6523 | pass | 原样重放 |

每个对象的冻结输入（`inputs.sha256`）、原网表（与 `verdict.json` 的 `netlist_sha256`）和门级模型哈希均核对通过；完整 diff 与哈希见各对象目录 `netlist.diff`、`result.json`。日志检查无问题。

## 4. 诊断结果（理想时钟、综合后、只计引脚电容）

| 对象 | 门级回归 | 六点全局最差 setup（ns；corner，类别） | 最差 setup 路径 | 最差 hold（ns；理想时钟、综合后模型下的最小 hold slack） | 达到 F1 目标（六点 setup ≥ 0） | 面积（µm²，正式值） |
|---|---|---|---|---|---|---|
| baseline | 通过（checked=2856） | -4.189726（ss_n40C_1v60，in2reg） | in_b[2] → _12026_/D | 0.059113（ff_100C_1v95） | 否 | 45383.5264 |
| r1_cand_983p_attempt1 | 通过（checked=2835） | 1.557034（ss_n40C_1v60，reg2reg） | _12134_/Q → _12081_/D | 0.023094（ff_n40C_1v95） | 是 | 47983.52 |
| r1_cand_9pbi_attempt1 | 通过（checked=2816） | 8.708432（ss_n40C_1v60，reg2reg） | _12364_/Q → _12554_/D | 0.023094（ff_n40C_1v95） | 是 | 48790.544 |
| r1_cand_wpml_attempt1 | 通过（checked=2835） | 5.004687（ss_n40C_1v60，in2reg） | in_b[17] → _12405_/D | 0.068576（ff_100C_1v95） | 是 | 46336.9408 |
| r2_cand_3yvg_attempt1 | 通过（checked=2835） | 1.542086（ss_n40C_1v60，reg2reg） | _12138_/Q → _12076_/D | 0.023094（ff_n40C_1v95） | 是 | 48169.9488 |
| r2_cand_c1dx_attempt1 | 通过（checked=2835） | 1.557034（ss_n40C_1v60，reg2reg） | _12134_/Q → _12081_/D | 0.023094（ff_n40C_1v95） | 是 | 47983.52 |
| r2_cand_u2pe_attempt1 | 通过（checked=2816） | 6.104896（ss_n40C_1v60，reg2reg） | _12500_/Q → _12338_/D | 0.023094（ff_n40C_1v95） | 是 | 48666.6752 |

## 5. 观察（操作者起草，作者复核同意）

1. 六个候选在兼容性处理后全部门级回归通过、STA 与有效性检查通过，全部达到 F1 目标（六点 setup ≥ 0）；基线为 −4.19 ns。
2. 按计划 §7 的固定口径："诊断显示存在时序改善的可能，但正式流程未能确认"，并说明评估器局限（冻结配方写出的 `wire signed` 声明不被 OpenSTA 网表读取器接受）。
3. 第 2 轮 cand_c1dx 与第 1 轮 cand_983p 的诊断时序、路径和面积完全相同（RTL 文件哈希不同，综合网表不同）；只作记录，不作解释，也不推测编号与模型的对应。
4. 最差 hold 多为 +0.023 ns（ff_n40C_1v95），低于基线 +0.059 ns；hold 只观察、不计入目标。

## 6. 没有做的事

- 没有修改任何正式运行目录、F1 归档或冻结文件；诊断结果没有交还任何模型。
- 没有对任何对象追加别的转换或重跑。
