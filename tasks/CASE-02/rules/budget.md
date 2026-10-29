# 总预算的推导（规程 v0.3 第 6.4 节 (b)；实现计划 Task 6）

状态：第 1 节（容量查证）2026-10-28 完成；第 2 节（探针）和第 3 节（核算）待 Task 11 的外壳 `--probe` 模式完成后做；作者检查点 A 在第 3 节之后。

## 1. 三家的上下文容量（来源与日期）

查证日期：2026-10-28。只记厂商自己的页面；第三方聚合站的数字不作依据。

| 模型（接入方式） | 容量 | 最大输出 | 来源 | 备注 |
|---|---|---|---|---|
| `claude-opus-5-5`（Claude Code 2.1.296 直连 Anthropic） | 1M token | 128K token | https://platform.claude.com/docs/en/docs/about-claude/models/overview（docs.anthropic.com 301 到此） | 页面未提到需要 beta 标志 |
| `k3[1M]`（Claude Code 经兼容层调 Moonshot `kimi-k3`） | 1,048,576 token（"All K3 series models support a 1,048,576-token context window."） | 页面上该行没有抓到 | https://platform.kimi.ai/docs/pricing/chat、https://platform.kimi.ai/docs/api/models-overview.md（platform.moonshot.ai 301 到此） | 阶段 A 用 `[1M]` 后缀告诉 Claude Code 该模型是 1M 窗口 |
| `deepseek-v4-pro[1M]`（Claude Code 经兼容层调 DeepSeek） | 1M（"上下文长度 1M"） | 最大 384K | https://api-docs.deepseek.com/zh-cn/quick_start/pricing | **列归属有歧义**：表里 `deepseek-flash` 和 `deepseek-v4-pro` 两列，上下文长度一行只显示一个值，无法从抓取的文本确定是否两列相同；英文页 `/quick_start/pricing` 抓到的是"Your First API Call"页，没有数字 |

**结论（待作者在检查点 A 确认）**：三家厂商页面给出的容量都是 1M 量级，`ctx_min` 取 1,000,000 token。两个保留项：(1) DeepSeek 的列归属歧义；(2) Kimi 和 DeepSeek 经兼容层接入，兼容层是否原样提供整个窗口无法从文档确认，阶段 A 的运行记录里没有能证实窗口大小的字段。所以 `ctx_min = 1,000,000` 是**文档值**，不是实测值；预算按它算出来后，第 3 节会同时给出按 128,000（最常见的保守窗口）核算的对照列，让作者看到如果兼容层把窗口限在 128k 会怎样。

## 2. 探针（2026-10-28 完成）

调用：`python -B tasks/CASE-02/scripts/run_round.py --probe`（外壳 `--probe` 模式：非盲、固定题目、只保存 usage；原始记录 `D:\study\diag_sandbox\smoke-case02-budget-20261028-225242\`，每次调用的 `.jsonl`、`.meta.json`、`.proc.json` 保留，`.answer.md` 已删）。系统提示用 CASE-02 的 `prompts/system.md`。字段语义：stream-json `result` 事件的 `usage.input_tokens + cache_creation_input_tokens + cache_read_input_tokens` 记为"输入总 token"（Claude 直连把绝大部分输入计入 `cache_creation_input_tokens`，`input_tokens` 只有 2；两家兼容层只填 `input_tokens`）；`modelUsage` 层的 `inputTokens` 等字段与之一致。空白探针（100 B）的总 token 记为固定开销 `overhead_m`。

| 模型 | 样文 | 字节 | 输入总 token | overhead | 样文 token | 字节/token |
|---|---|---|---|---|---|---|
| claude | prose | 8000 | 3567 | 699 | 2868 | 2.79 |
| claude | report | 8000 | 4881 | 699 | 4182 | 1.91 |
| kimi | prose | 8000 | 1921 | 418 | 1503 | 5.32 |
| kimi | report | 8000 | 3247 | 418 | 2829 | 2.83 |
| deepseek | prose | 8000 | 1946 | 413 | 1533 | 5.22 |
| deepseek | report | 8000 | 3424 | 413 | 3011 | 2.66 |

`token_bytes_ratio = min = 1.91`（Claude 读 OpenSTA 报告文本时最费 token；保守方向取最小）。

## 3. 核算（2026-10-28；作者检查点 A）

公式：`total_budget_tokens = ctx_min − overhead − P1 − 32000 − S − 32000 − 0.10 × ctx_min`。

| 项 | 值 | 来源 |
|---|---|---|
| `ctx_min` | 1,000,000 | 第 1 节的文档值（三家都是 1M 量级） |
| `overhead` | 699 | 三家空白探针的最大值 |
| `P1`（第 1 轮完整题目） | 上界 40000 token（估算 21183 token：材料约 40458 字节 ÷ 1.91；含 dot4sat.v 1495 B、两份 summary 各 2352 B、两份 path 报告各 7937 B、context 正文 2621 B + 契约段约 9000 B、行号前缀 8%） | `build_prompt.py round1` 生成后回填实测值；实测超过上界时本表重算 |
| 第 1 轮答复上界 | 32,000 | `CLAUDE_CODE_MAX_OUTPUT_TOKENS`；条件：冒烟上限探针证明 cap 生效 |
| `S`（第 2 轮拼接文本） | 2,000 | 模板 + 最多 24 个实例标题行，保守 |
| 第 2 轮输出预留 | 32,000 | 同上 |
| 安全余量 | 10% × `ctx_min` | |
| **按 1M 算** | **793301 → 取整 790000 token** | ≈ 1.44 MiB 交还文本 ≈ 28740 行（按 W05 的 52.5 B/行） |
| 对照：按 128,000 算 | 8501 token ≈ 15 KiB ≈ 309 行 | 如果兼容层把窗口限在 128k，连一个满实例（2000 行 / 256 KiB）都放不下 |

两个满实例（2 × 256 KiB = 512 KiB）相当于 274497 token，在 790000 之内；72 个实例全部顶满（18 MiB）会超出，这时按 keep_order 保留并出预算账单。

**写入 `rules/contract.json`**：`total_budget_tokens = 790000`、`token_bytes_ratio = 1.91`、`budget_table`（本表）。

**请作者在检查点 A 确认**：(1) 接受 `ctx_min = 1,000,000` 这个文档值（DeepSeek 列归属歧义、兼容层是否原样提供窗口都未实测；对照列说明若实际是 128k 会怎样）；(2) 接受上表各项预留和 790000 这个数。改任何一项，重算后同步改 `contract.json` 并重新生成 `package_src/context.md`（第一档前都可以改，不留痕迹以外的代价）。
