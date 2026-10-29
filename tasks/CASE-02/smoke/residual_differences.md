# 冒烟复测与残留差异（规程 v0.3 第 8 步；阶段 A 规程 §5.1 的八条逐项复核）

冒烟：2026-10-29 06:01，`python -B tasks/CASE-02/scripts/run_round.py --smoke`，两档标签 `case02-prereg`（53a7c75）、`case02-prereg-round`（71ffc92）下，预登记核验为空。原始记录 `D:\study\diag_sandbox\smoke-case02-20261029-060119\`（不进 git：每次调用的 `.jsonl`、`.meta.json`、`.proc.json`、`.answer.md`、`.err`）。结果 `SMOKE OK`。

## 本次冒烟核对到的

| 项 | 记录字段 | claude | kimi | deepseek |
|---|---|---|---|---|
| 预检四项（可执行文件哈希、`--version` 2.1.296、配置原文件哈希、已登录） | 外壳在任何调用前核对，不符即拒绝 | 通过 | 通过 | 通过 |
| 系统提示 / 题目字节哈希 | `system_sha256` a52d9b03…、`user_sha256` 256d5e40…（与 `rules/copied_from.tsv` 登记的冒烟三文件一致） | 同 | 同 | 同 |
| 两处暗号 | `.answer.md` | 都答对 | 都答对 | 都答对 |
| init 字段 | `claude_code_version`、`tools`、`mcp_servers`、`plugins` | 2.1.296；`[]`；`[]`；两个内置插件 | 同 | 同 |
| 报告的模型名 | `assistant.message.model` | `claude-opus-5-5` | `k3` | `deepseek-v4-pro` |
| `per_turn_effort_active`（不加 `--effort`） | init | true | false | false |
| `modelUsage.maxOutputTokens` | result | 128000 | 32000 | 32000 |
| 上限探针（`CLAUDE_CODE_MAX_OUTPUT_TOKENS=64`，题目"数到 300"） | `num_turns`、`is_error`、答复 | 截停：turns=4，is_error=False，exit 0 | 截停：turns=4，is_error=True，exit 1，答复为 `API Error: … exceeded the 64 output token maximum` | 同 kimi |
| 自动重试 | `api_retries` | 0 | 0 | 0 |
| 答复里是否带出隐藏信息（邮箱等） | `hidden_in_answer` | 0 | 0 | 0 |
| 用时 | `proc.elapsed_seconds` | 3.0 s | 7.5 s | 3.9 s |

## 阶段 A §5.1 八条残留差异的逐项状态

| 条 | 阶段 A 的观察 | 本次状态 | 依据 |
|---|---|---|---|
| 1 | Claude Code 在替换后的系统提示前加一句"基于 Claude Agent SDK 的 agent"身份声明，三个模型都收到 | **尚未复测**（仅属历史观察） | 冒烟题目只要求复述两处暗号，没有要求模型复述系统提示；外壳记录里没有能看到实际系统提示全文的字段 |
| 2 | 三个模型都收到同一段环境信息（工作目录、平台、日期、剩余预算、下载安全提示） | **尚未复测**（仅属历史观察） | 同上。工作目录仍是项目外的空随机目录（`workdir` 字段：run-77abe25a / run-8704ac8c / run-fceaf56f），目录名不带提示 |
| 3 | 只有 Claude（订阅登录）会额外收到带账号邮箱的提醒 | **无法核实**提醒是否仍出现；**已复测**邮箱没有进入任何答复 | `hidden_in_answer=0`（三家）；`privacy_check` 对材料包和题目 0 命中 |
| 4 | `per_turn_effort_active` 依次 true/false/false（当时加了 `--effort high`） | **已复测**：不加 `--effort` 仍是 true / false / false | 本次 init 字段 |
| 5 | Kimi 自述系统提示里有 thinking 模式说明并把"thinking"列成工具 | **尚未复测**（仅属历史观察） | 冒烟题目没有要求 Kimi 自述；三家答复都说"没有可用工具" |
| 6 | `maxOutputTokens` 128000/32000/32000，字段不随环境变量变化；上限设 64 时 Claude 和 Kimi 被截停 | **已复测**：字段仍是 128000/32000/32000；上限 64 时三家都被截停（阶段 A 只测过 Claude 和 Kimi，DeepSeek 这次也截停） | 上限探针六个 `.meta.json`；`CAP_PROBE_TOKENS=64` |
| 7 | Kimi 和 DeepSeek 经兼容层，Claude Code 报"无法识别的模型"、只给估算费用 | **部分复测**：报告的模型名仍是 `k3` / `deepseek-v4-pro`；截停那次的事件流里多出一条 `model=<synthetic>` 的 assistant 事件（Claude Code 自己生成的错误消息，不是模型输出），外壳按"模型名不符"记在 problems 里，正式轮次若出现同样情况按 `void_check` 分类处理 | `kimi-cap64.meta.json`、`deepseek-cap64.meta.json` 的 `problems`；`.jsonl` 里 `"model":"<synthetic>"` 各 1 条 |
| 8 | 冒烟中 DeepSeek 发生过一次 `api_retry` | **已复测**：本次六次调用都没有重试 | `api_retries=0` |

## 结论

冒烟的全部硬性项通过（预检、暗号、字段、上限生效、无重试、无泄露），两档登记状态有效，可以进入第 1 轮。第 1、2、5 条属于"模型收到的隐藏文本"，本次没有设计复述题目去核，仍按阶段 A 的历史观察在笔记里如实写出；第 7 条的 `<synthetic>` 事件是新记录到的形态，写进笔记的外壳说明。

## 2026-10-29 08:44 变更后复测（规程补记 3：输出上限 128000、两档标签重打）

`SMOKE OK`，记录 `D:\study\diag_sandbox\smoke-case02-20261029-084421\`。三家暗号都对、`maxOutputTokens` 仍为 128000/32000/32000（字段不随环境变量变化，与阶段 A 第 6 条一致）、`per_turn_effort_active` true/false/false、无重试、无泄露；上限探针 64 对三家都截停（Claude 这次 `is_error=True, exit 1`，上一次是 `is_error=False, exit 0`，截停形态在 Claude 直连上两种都出现过）。之前 08:36 的一次冒烟 `SMOKE FAIL`：Claude 两次调用都返回 `Failed to refresh OAuth token: another Claude Code process is refreshing it`（本会话自己就是一个 Claude Code 进程，刷新冲突是瞬时的），其余两家正常；那次记录保留在 `smoke-case02-20261029-083658\`，不是外壳或模型问题。
