# AI Silicon Lab

**AI timing advice, checked by engineering experiments. ｜ AI 提出的时序建议，用工程实验验证。**

[English](#english) · [中文](#中文)

---

## English

This project tests, with reproducible experiments, what large language models say about timing: their diagnosis of a timing report and, next, the RTL changes they propose. The design, constraints, synthesis recipe and analysis setup are frozen first; the models then read the report; every claim they make is checked with open-source tools against pre-written criteria. Negative results are published too.

Tools: Yosys, OpenSTA, Icarus Verilog; standard cells SkyWater Sky130 `sky130_fd_sc_hd`. All conclusions hold only for the fixed analysis model used here — post-synthesis, ideal clocks, no wire parasitics (pin loads only), six PVT corners — and say nothing about silicon or post-route timing.

### Articles

| Article | English | Chinese |
|---|---|---|
| 1. Can LLMs read a timing report? Checking the diagnoses of Claude Opus 5.5, Kimi K3 and DeepSeek V4 Pro with OpenSTA (CASE-01, stage A) | [Summary](docs/posts/article1_summary_en.md) | [WeChat version](docs/posts/article1_public.md) · [Full version, every number sourced](docs/posts/article1_draft.md) |

### Reproduce

To check the conclusions without using the author's results: set up the environment with [`env/SETUP.md`](env/SETUP.md) (Chinese; mostly commands and versions), then follow [`REPRODUCE.en.md`](REPRODUCE.en.md) to regenerate the baseline from RTL, re-run every base check and recheck, and compare each output with the committed one. On the author's machine, from a clean clone, all 24 query outputs matched (`REPLICATION OK`).

### Layout

| Path | Content |
|---|---|
| `docs/posts/` | Articles and figures (`figs/article1/make_figs.js` draws the figures) |
| `env/` | Environment snapshot: install record, checksums, cell-library kit scripts, smoke test |
| `tasks/CASE-01/` | Case 1: contract `spec.md`, RTL, reference model, testbench, synthesis and STA scripts, frozen evidence |
| `tasks/CASE-01/diag/` | Stage A: protocol, the material given to the models, their answers, the claim table `claims.tsv`, raw tool outputs of every check, statistics |
| `tasks/CASE-01/diag/stats_revised.md` | Final label statistics (after the post-unblinding correction); original statistics in `diag/stats.md` |
| `docs/history/` | Commit-id map for the 2026-10-17 history rewrites |

Most documents are in Chinese; scripts, comments and commit messages are in English.

### Not in this repository

Working notes, environment debugging logs, the intervention log and an incident note; the execution and implementation plans with their prototype code; external review records; the item-by-item rulings of the post-unblinding review (so `stats_revised.md` can be read but not recomputed); commercial EDA scripts and outputs; API keys (`diag/models/` holds redacted copies); run directories (only checksums are kept).

### License

Code (scripts, RTL, testbenches, figure generator): Apache-2.0, see [`LICENSE`](LICENSE). Articles, figures and other documents and records: CC BY 4.0, see [`LICENSE-docs.md`](LICENSE-docs.md). Exceptions: third-party license files in `env/licenses/` keep their own licenses; the model answers in `tasks/CASE-01/diag/outputs/` are included verbatim as research records.

### Commit history

The history was rewritten five times on 2026-10-17 before publication, so every commit id changed. Records written before that cite the original ids; see [`docs/history/HISTORY_REWRITE_2026-10-17.md`](docs/history/HISTORY_REWRITE_2026-10-17.md).

---

## 中文

这个项目用可复现的实验，检验大模型给出的时序诊断和 RTL 修改建议：先冻结设计、约束和分析配置，再让模型读报告、下诊断，然后用开源工具逐条核对；下一步让模型改 RTL，再做功能和时序复验。结果不好也照实发表。

工具：Yosys、OpenSTA、Icarus Verilog，单元库 SkyWater Sky130 `sky130_fd_sc_hd`。结论只在综合后、理想时钟、不计布线寄生的固定分析模型和 6 个 PVT 点之内成立，不代表流片后的芯片。

### 文章

| 文章 | 公众号版 | 完整版（每个数字标出处） |
|---|---|---|
| 1. 大模型看时序报告靠谱吗？我用 OpenSTA 核对了 Claude Opus 5.5、Kimi K3、DeepSeek V4 Pro 的诊断 | [`docs/posts/article1_public.md`](docs/posts/article1_public.md) | [`docs/posts/article1_draft.md`](docs/posts/article1_draft.md) |

### 复现

想自己验证结论，不用作者跑出的结果：先按 [`env/SETUP.md`](env/SETUP.md) 搭好环境，再按 [`REPRODUCE.md`](REPRODUCE.md) 从 RTL 重新生成基线、重跑全部基础核对和重查，并与仓库里的输出逐份比对；判断和标签也可以按规程独立重做。

### 目录

| 位置 | 内容 |
|---|---|
| `docs/posts/` | 文章和配图（`figs/article1/make_figs.js` 生成配图） |
| `env/` | 开源 EDA 环境的安装记录、校验和、单元库套件、冒烟测试 |
| `tasks/CASE-01/` | 第一个案例：合同 `spec.md`、RTL、参考模型、测试平台、综合和 STA 脚本、冻结证据 |
| `tasks/CASE-01/diag/` | 阶段 A：三个模型的诊断规程、材料包、答复、判断记录 `claims.tsv`、工具重查的原始输出、统计 |
| `tasks/CASE-01/diag/stats_revised.md` | 最终标签的统计（揭盲后复核修订后）；原始统计见 `diag/stats.md` |
| `docs/history/` | 2026-10-17 历史改写的新旧提交号对照 |

### 不在仓库里的东西

- 作者本地的工作记录（会话交接笔记）、环境调试记录（原 `docs/env/`）、介入日志和事故说明。仓库里有些文件提到 `docs/env/` 下的问题编号，这些文件不在公开仓库里。
- 执行计划、实现计划和预先验证的原型代码；对计划、规程和文章的外部评审记录；揭盲后复核的逐条裁定。`stats_revised.md` 由裁定表生成，脚本 `diag/scripts/claims_stats_revised.py` 在仓库里，但没有裁定表无法重算。
- 商业 EDA 工具的调用脚本和任何商业工具的输出。
- 模型调用所用的密钥配置；仓库里 `tasks/CASE-01/diag/models/` 是去掉密钥后的副本。
- 运行目录 `tasks/*/runs/` 和归档副本，只保留校验和。

### 许可

- 代码（脚本、RTL、测试平台、配图生成脚本等）：Apache-2.0，见 [`LICENSE`](LICENSE)。
- 文章和图，以及其他说明文档和实验记录：CC BY 4.0，见 [`LICENSE-docs.md`](LICENSE-docs.md)。
- 例外：`env/licenses/` 中第三方单元库和 PDK 的许可文件按其原许可；`tasks/CASE-01/diag/outputs/` 中的模型答复原文作为研究记录原样收录。

### 关于提交历史

2026-10-17 公开之前改写过五次历史，提交号全部变了。改写之前写成的记录里引用的是原始提交号，对照表见 [`docs/history/HISTORY_REWRITE_2026-10-17.md`](docs/history/HISTORY_REWRITE_2026-10-17.md)。
