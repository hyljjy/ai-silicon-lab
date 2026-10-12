# 冒烟复测汇总（规程第 4 步）

- CLI：Claude Code 2.1.296（固定副本，sha256 见 `rules/cli.sha256`），每次运行前的预检全部通过。
- 冒烟不是盲评，下面出现模型名是允许的。原始记录在项目外的 `D:\study\diag_sandbox\smoke-<时间>\`，不进 git。

## 第一次：2026-10-12 08:57，HEAD `33cddd3`（规程 v0.5），未通过

```
claude: valid=False canaries=True per_turn_effort_active=True maxOutputTokens=128000 exit=0 retries=0
  输出上限不符: maxOutputTokens=128000
kimi: valid=True canaries=True per_turn_effort_active=False maxOutputTokens=32000 exit=0 retries=0
deepseek: valid=True canaries=True per_turn_effort_active=False maxOutputTokens=32000 exit=0 retries=0
SMOKE FAIL
```

诊断（介入日志 2026-10-12）：`modelUsage.maxOutputTokens` 字段不随 `CLAUDE_CODE_MAX_OUTPUT_TOKENS` 变化；把上限设为 64 时 Claude 和 Kimi 都被截停。作者决定修订为规程 v0.6：这个字段按实测值核对，冒烟复测增加上限探针。

## 第二次：2026-10-12 09:08，HEAD `a610a4e`（规程 v0.6），通过

```
claude: valid=True canaries=True per_turn_effort_active=True maxOutputTokens=128000 exit=0 retries=0
kimi: valid=True canaries=True per_turn_effort_active=False maxOutputTokens=32000 exit=0 retries=0
deepseek: valid=True canaries=True per_turn_effort_active=False maxOutputTokens=32000 exit=0 retries=0
claude: cap_probe capped=True turns=4 is_error=True exit=1
kimi: cap_probe capped=True turns=4 is_error=True exit=1
deepseek: cap_probe capped=True turns=4 is_error=True exit=1
SMOKE OK
```

- 第 5.3 节的作废判据三家都满足；系统提示（命令行参数）和题目（stdin）里的中文暗号都读到了。
- 上限探针：上限设为 64、题目是"从 1 数到 300"，三家都被截停（自动续写 4 轮后报"超过输出上限"），说明正式运行的 32000 上限对三家都生效。
- 不加 `--effort` 时，`per_turn_effort_active` 依次为 true、false、false。
