# 冒烟第 3、4 部分（规程 §6.3；计划 Task 13 Step 3）

日期 2026-10-21，作者在场。

## 第 3 部分：抽取、门槛正反例与否决对照样例

- **抽取和门槛的正反例**：由第一档冻结的测试覆盖（`test_extract`、`test_gate`，以及 `round.py` 接入真实门槛的 `test_round` 用例），结果见 `revise/smoke/tests_tier1.txt`（全套测试，两边 `rc=0`）。规程 §6.3 第 3 部分"抽取""门槛"两组所列情况各有对应夹具和测试（`revise/scripts/fixtures/answers/`、`revise/scripts/fixtures/gate/`）；门槛的识别方法按规程 v0.5 RV-01、RV-06、RV-07。
- **七个否决对照样例**：作者对照 `revise/review/samples/README.md` 逐个看过 `s1`～`s7`，2026-10-21 记录：**七个样例的预期判断全部同意**。

  | 样例 | 情况 | 预期（V1 / V2） | 作者 |
  |---|---|---|---|
  | s1_v1_default_then_override | 组合块先给默认值再在分支中覆盖 | 不命中 / 不命中 | 同意 |
  | s2_v1_missing_assignment | 真正缺赋值的组合块 | 命中 / 不命中 | 同意 |
  | s3_v1_unreachable_branch | 只有不可达分支缺赋值 | 不命中 / 不命中 | 同意 |
  | s4_v2_data_not_reset | 数据寄存器不复位 | 不命中 / 不命中 | 同意 |
  | s5_v2_equivalent_boolean | 等价布尔表达式清 valid | 不命中 / 不命中 | 同意 |
  | s6_v2_inverted_valid | 反相编码 valid | 不命中 / 不命中 | 同意 |
  | s7_v2_stage_not_cleared | 某一级逻辑有效状态复位时未清空 | 不命中 / 命中 | 同意 |

  作者作答前，Codex 只读审查 `docs/review/CASE01_SM1_codex.md` 给出独立意见：七个预期判断均可同意、覆盖规程 §6.3 列出的全部七种情况、README 无需修订；该意见不替代作者判断。

## 第 4 部分：脚本单元测试

第一档冻结的全部脚本测试两边通过（`revise/smoke/tests_tier1.txt`）：WSL 17 个模块 478 项 OK（跳过 1），Windows 15 个模块 405 项 OK（跳过 15，均为 Linux 专用），两边 `rc=0`、无遗留进程。

## 冒烟判定（计划 Task 13 Step 4）

- 第 1、2 部分通过（`part1.md`、`part2.md`）；第 3、4 部分无不符。
- 没有模型在第 1、2 部分耗尽尝试。
- 暂定期望值与实测一致，不触发规程第 3 节第 5 步的修订流程。
- **冒烟通过**，进入第二档预登记（规程第 5 步）。冒烟共 9 次模型调用，已记入介入日志。
