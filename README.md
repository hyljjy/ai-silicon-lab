# AI Silicon Lab

**AI 提出的时序建议，用工程实验验证。**

这个项目用可复现的实验，检验大模型给出的时序诊断和 RTL 修改建议：先冻结设计、约束和分析配置，再让模型读报告、下诊断，然后用开源工具逐条核对；下一步让模型改 RTL，再做功能和时序复验。结果不好也照实发表。

工具：Yosys、OpenSTA、Icarus Verilog，单元库 SkyWater Sky130 `sky130_fd_sc_hd`。结论只在综合后、理想时钟、不计布线寄生的固定分析模型和 6 个 PVT 点之内成立，不代表流片后的芯片。

## 文章

| 文章 | 公众号版 | 完整版（每个数字标出处） |
|---|---|---|
| 1. 大模型看时序报告靠谱吗？我用 OpenSTA 核对了 Claude Opus 5.5、Kimi K3、DeepSeek V4 Pro 的诊断 | [`docs/posts/article1_public.md`](docs/posts/article1_public.md) | [`docs/posts/article1_draft.md`](docs/posts/article1_draft.md) |

## 目录

| 位置 | 内容 |
|---|---|
| `docs/PLAN_v1.0.md` | 执行计划：目标、案例、预算 |
| `docs/posts/` | 文章和配图（`figs/article1/make_figs.js` 生成配图） |
| `docs/review/` | 规程、计划和文章的外部评审记录 |
| `docs/env/` | 环境搭建记录和问题日志 |
| `env/` | 开源 EDA 环境的安装记录、校验和、单元库套件 |
| `tasks/CASE-01/` | 第一个案例：合同 `spec.md`、RTL、参考模型、测试平台、综合和 STA 脚本、冻结证据 |
| `tasks/CASE-01/diag/` | 阶段 A：三个模型的诊断规程、材料包、答复、判断记录 `claims.tsv`、工具重查的原始输出、统计 |
| `tasks/CASE-01/diag/review/postblind/` | 揭盲后复核的规程、外审核对和作者裁定；最终统计见 `diag/stats_revised.md` |
| `docs/history/` | 2026-10-17 历史改写的新旧提交号对照 |

## 不在仓库里的东西

- 作者本地的工作记录（会话交接笔记）。
- 商业 EDA 工具的调用脚本和任何商业工具的输出。
- 模型调用所用的密钥配置；仓库里 `tasks/CASE-01/diag/models/` 是去掉密钥后的副本。
- 运行目录 `tasks/*/runs/` 和归档副本，只保留校验和。

## 许可

- 代码（脚本、RTL、测试平台、配图生成脚本等）：Apache-2.0，见 [`LICENSE`](LICENSE)。
- 文章和图，以及其他说明文档和实验记录：CC BY 4.0，见 [`LICENSE-docs.md`](LICENSE-docs.md)。
- 例外：`env/licenses/` 中第三方单元库和 PDK 的许可文件按其原许可；`tasks/CASE-01/diag/outputs/` 中的模型答复原文和 `docs/review/` 中外部模型的评审原文，作为研究记录原样收录。

## 关于提交历史

2026-10-17 公开之前改写过一次历史，提交号全部变了。改写之前写成的记录里引用的是旧提交号，对照表见 [`docs/history/HISTORY_REWRITE_2026-10-17.md`](docs/history/HISTORY_REWRITE_2026-10-17.md)。
