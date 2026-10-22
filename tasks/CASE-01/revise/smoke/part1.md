# 冒烟第 1 部分：外壳检查（规程 §6.3；计划 Task 13 Step 1）

日期 2026-10-21，作者在场。第一档标签 `revise-prereg-smoke`（`122761f`），外壳以冒烟模式运行，核对第一档标签与暂定期望值 `revise/rules/expected_tentative.json`。CLI 固定副本 2.1.296（sha256 见 `revise/rules/cli.sha256`）。原始记录在仓库外 `D:\study\revise_sandbox\raw\smoke\<时间>\`，汇总在 `tasks/CASE-01/runs/revise-smoke/<时间>/summary.json`（均不进 git）。

## 题目

由 `build_prompt.py` 生成于 `runs/revise-smoke/prompts/`：

| 文件 | sha256 |
|---|---|
| cap_probe_user.md | `0e1eb3ecc59441cbfc970037c61ad60817fc0bea475dce010653b08e3a3924e8` |
| canary_user.md | `4da5858477e865fee65bcd2d138cfa9ab73a198fe1e459a5d54263d7b6ca285a` |

系统提示与冒烟标签中的 `revise/prompts/smoke_system.md` 一致（`system_check: tag revise-prereg-smoke`），stdin 与重建的期望字节一致。

## 上限探针 `--smoke probe`（`20261021-202525-e84b-probe`）

`CLAUDE_CODE_MAX_OUTPUT_TOKENS=64`，题目"从 1 数到 300"。

```
claude: probe ok=True delivery=delivery_fail categories=输出上限、退出码非 0、模型不符、stop_reason 异常
kimi: probe ok=True delivery=delivery_fail categories=输出上限、退出码非 0、模型不符、stop_reason 异常
deepseek: probe ok=True delivery=delivery_fail categories=输出上限、退出码非 0、模型不符、stop_reason 异常
SMOKE probe OK
```

三家都被截停，判为交付失败（上限证据为 RV-05 规定的 CLI 报错原句）。同时出现的异常标记按规程 §6.2 全部保留，不改变交付分类："模型不符"来自 CLI 截停时插入的报错消息——该 `assistant` 事件的 `message.model` 为 `<synthetic>`（`message.stop_reason` 为 `stop_sequence`）；"stop_reason 异常"来自分类器对 `result` 事件 `stop_reason` 的检查——三家 `result.stop_reason` 均为 `stop_sequence`（`subtype=success`、`is_error=true`、`num_turns=4`），不是 `end_turn` 或 `max_tokens`；"退出码非 0"来自 CLI 退出码 1 与 `is_error=true`。以上字段值由操作者从原始记录核对（Codex `CASE01_SM1_codex.md` §4.1 建议分别说明两个字段来源）。

## 暗号与预检 `--smoke canary`（`20261021-202751-0e26-canary`）

```
claude: canary ok=True delivery=parse categories=无
kimi: canary ok=True delivery=parse categories=无
deepseek: canary ok=True delivery=parse categories=无
SMOKE canary OK
```

- 中文暗号两路（系统提示、stdin）三家都读到（`canaries: [True, True]`）。
- 预检全部通过：CLI sha256、`--version`、配置原文件 sha256 等于 `revise/models/originals.sha256`、`auth status` 已登录；预检命令退出码均为 0。
- 配置副本无覆盖项（`revise/models/` 为 `diag/models/` 的逐字节副本，作者 2026-10-21 比较三个配置原文件哈希全部一致）。
- init 中工具为空、MCP 为空，插件只有两个内置插件；没有 auto memory 异常；`api_retries` 为 0。

## 证据范围

仓库内汇总（`summary.json`）只保存部分结果。预检原始输出、各事件的具体字段、暗号原文由操作者从仓库外原始记录核对；Codex 只读审查（`docs/review/CASE01_SM1_codex.md`）看的是仓库内的记录和汇总，没有打开原始记录。

## 结论

第 1 部分通过（Codex SM1 同意）。
