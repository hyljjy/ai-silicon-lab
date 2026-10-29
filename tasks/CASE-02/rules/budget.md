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

## 2. 探针（待做）

按实现计划 Task 6 Step 2：空白探针（100 B）+ 中文说明文样文（8000 B）+ OpenSTA 报告样文（8000 B），三家各一次；读 stream-json `result` 事件的 `usage.input_tokens + cache_creation_input_tokens + cache_read_input_tokens`，记 `modelUsage` 层对应字段；`overhead_m` = 空白探针的总 token；`ratio_m,type = bytes / (总 token − overhead_m)`；`token_bytes_ratio = min`。原始记录 `D:\study\diag_sandbox\smoke-case02-budget\`。

## 3. 核算（待做）

`total_budget_tokens = min_m( 容量_m − overhead_m − P1 − 32000 − S − 32000 − 0.10×容量_m )`，各项定义见实现计划 Task 6 Step 3。
