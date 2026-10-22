# 冒烟第 2 部分：CASE-01 形态演练（规程 §6.3；计划 Task 13 Step 2）

日期 2026-10-21，作者在场。`run_revise.py --smoke rehearsal`（`20261021-202916-efcb-rehearsal`），三家各调用一次；演练候选经 `write_candidate(..., dest_root="runs/revise-smoke/<时间>/candidates/")` 写出，不运行 `grade.py`，门槛在 WSL 单独运行（`gate.py`，两阶段 Yosys 读取，`--stop-round 1`）。

## 题目

| 文件 | sha256 |
|---|---|
| rehearsal_claude.md | `38edf38a943373a57816a5ca2a0010985bf112e406a978f152a416444f76005c` |
| rehearsal_kimi.md | `47ae65e7766c0da609c38146a6f54c62d24f579652de86f799afb485b7367247` |
| rehearsal_deepseek.md | `dc5c6840520f272354f3ff04e404471a7004498c54c3d6bacf34f6dbf39b1d84` |

系统提示与冒烟标签一致，stdin 与重建字节一致（`prompt_ok` 三家为真）。

## 调用与抽取

```
claude: rehearsal ok=True delivery=parse categories=无
kimi: rehearsal ok=True delivery=parse categories=无
deepseek: rehearsal ok=True delivery=parse categories=无
SMOKE rehearsal CALL/EXTRACT OK (gate not run here)
```

| 模型 | 抽取状态 | DECLARED_L | 预测表行数 | 预测表问题 | 失败条件 | L 不一致 | 候选与第一个 verilog 块逐字节相同 |
|---|---|---|---|---|---|---|---|
| claude | ok | 1 | 10 | 无 | 0 | 否 | 是 |
| kimi | ok | 1 | 6 | 无 | 0 | 否 | 是 |
| deepseek | ok | 1 | 7 | 无 | 0 | 否 | 是 |

无截断、无续写（三家 `num_turns` 均为 1，`is_error` 为假）。演练题只要求预测表、声明行和与基线功能相同的完整模块，因此失败条件为 0 符合预期。Claude 与 DeepSeek 的候选与基线 `rtl/dot4sat.v` 逐字节相同（sha256 `422ba000…c802`）；Kimi 的候选只改了两行注释（sha256 `3b004776…33c7`）。

## 门槛（WSL）

| 模型 | L | 结果 |
|---|---|---|
| claude | 1 | GATE PASS |
| kimi | 1 | GATE PASS |
| deepseek | 1 | GATE PASS |

运行后无遗留 yosys 进程。

## 三家实测的期望值字段

与 `revise/rules/expected_tentative.json` 全部一致：

| 字段 | claude | kimi | deepseek |
|---|---|---|---|
| init 模型 | claude-opus-5-5 | k3[1m] | deepseek-v4-pro[1m] |
| assistant 模型 | claude-opus-5-5 | k3 | deepseek-v4-pro |
| CLI 版本 | 2.1.296 | 2.1.296 | 2.1.296 |
| maxOutputTokens | 128000 | 32000 | 32000 |
| 插件 | cc-plugin-agents-md、cc-plugin-plugin-authoring（内置） | 同左 | 同左 |

（canary 与 rehearsal 两次调用实测相同。）

## 证据范围

`summary.json` 不保存预测表行数、预测表问题和 L 不一致标记；这些以及 `num_turns`、`is_error`、实测期望值字段由操作者从仓库外原始记录重新抽取核对（`extract.parse_answer` 作用于 `void_check.answer_text` 解码后的答复）。Codex 只读审查（`docs/review/CASE01_SM1_codex.md`）没有打开原始记录。

## 结论

第 2 部分通过（Codex SM1 同意）；暂定期望值与实测一致，第二档 `expected.json` 可以直接取暂定值（规程第 3 节第 5 步）。
