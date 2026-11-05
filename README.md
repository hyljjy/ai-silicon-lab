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
| 2. Letting LLMs edit the RTL: Claude Opus 5.5, Kimi K3 and DeepSeek V4 Pro handed in 6 candidates; in the frozen flow only 1 got a valid timing result (CASE-01, stage B) | — | [WeChat version](docs/posts/article2_public.md) · [Full version, every number sourced](docs/posts/article2_draft.md) |
| 3. 128 constraints missing, yet the slack got better: how Claude Opus 5.5, DeepSeek V4 Pro and Kimi K3 tracked it down (CASE-02) | — | [WeChat version](docs/posts/article3_public.md) · [Full version, every number sourced](docs/posts/article3_draft.md) |
| 4. Slower when the chip is cold? Running temperature inversion by hand in OpenSTA, and asking three LLMs (STA learning note) | — | [WeChat version](docs/posts/article4_public.md) (single version; raw OpenSTA output and figure scripts in [`docs/posts/figs/article4/`](docs/posts/figs/article4/)) |
| 5. Setting a timing task for AI: how to prove the injected bug is exactly this one (how the tests were built, 1 of 7; CASE-02) | — | [WeChat version](docs/posts/article5_public.md) · [Short version, numbers sourced](docs/posts/retro/01_making_the_task.md) |
| 6. Judging an AI timing diagnosis: right, wrong, and the ones that cannot be judged (how the tests were built, 2 of 7; CASE-01, stage A) | — | [WeChat version](docs/posts/article6_public.md) · [Short version, numbers sourced](docs/posts/retro/02_judging_a_sentence.md) |
| 7. How setup slack is really computed: changing six conditions in OpenSTA and checking the account line by line (STA learning note) | — | [WeChat version](docs/posts/article7_public.md) (single version; raw OpenSTA output and figure scripts in [`docs/posts/figs/article7/`](docs/posts/figs/article7/)) |

CASE-02 experiment notes: [`tasks/CASE-02/NOTES.md`](tasks/CASE-02/NOTES.md) (Chinese).

### Reproduce

To check the conclusions without using the author's results: set up the environment with [`env/SETUP.md`](env/SETUP.md) (Chinese; mostly commands and versions), then follow [`REPRODUCE.en.md`](REPRODUCE.en.md) to regenerate the baseline from RTL, re-run every base check and recheck, and compare each output with the committed one. On the author's machine, from a clean clone, all 24 query outputs matched (`REPLICATION OK`).

Stage B (article 2): [`REPRODUCE_stageB.md`](REPRODUCE_stageB.md) (Chinese) re-grades the six candidate RTLs and recomputes the archived results; from a clean clone all six compared `same` with the archive. CASE-02: [`REPRODUCE_case02.md`](REPRODUCE_case02.md) (Chinese) covers the offline hash checks, the three frozen STA context runs, the round-2 queries and the execution-contract acceptance; from a clean clone the context runs matched the records byte for byte (apart from the absolute-path library lines) and all acceptance samples passed. Each guide states what it does not cover.

### Layout

| Path | Content |
|---|---|
| `docs/posts/` | Articles and figures (`figs/article{1,2,3}/make_figs.js` draw the figures, `make_cover.js` the covers; `wechat/make_wechat.py` renders the WeChat pages) |
| `env/` | Environment snapshot: install record, checksums, cell-library kit scripts, smoke test |
| `tasks/CASE-01/` | Case 1: contract `spec.md`, RTL, reference model, testbench, synthesis and STA scripts, frozen evidence |
| `tasks/CASE-01/diag/` | Stage A: protocol, the material given to the models, their answers, the claim table `claims.tsv`, raw tool outputs of every check, statistics |
| `tasks/CASE-01/diag/stats_revised.md` | Final label statistics (after the post-unblinding correction); original statistics in `diag/stats.md` |
| `tasks/CASE-01/revise/` | Stage B: protocol, prompts and material package, the models' answers, the grading results of the six candidate RTLs, criteria judgments, netlist-compatibility diagnosis, tests; the candidates' RTL and synthesis configs are `tasks/CASE-01/rtl/dot4sat_cand_*.v` and `config/impl.cand_*.cfg` |
| `tasks/CASE-02/` | Case 2: protocol, pre-validation, the three frozen STA context records, material packages, the models' answers of both rounds, round-2 queries with per-command records, claim table `claims.tsv`, evidence map, statistics `stats.md`, notes `NOTES.md` |
| `docs/history/` | Commit-id map for the 2026-10-17 history rewrites |

Most documents are in Chinese; scripts, comments and commit messages are in English.

### Not in this repository

Working notes, environment debugging logs, the intervention logs and an incident note; the execution and implementation plans with their prototype code; external review records; the item-by-item rulings of the post-unblinding review of stage A (so `stats_revised.md` can be read but not recomputed); commercial EDA scripts and outputs; API keys (`diag/models/`, `revise/models/` and `tasks/CASE-02/models/` hold redacted copies); run directories (only checksums are kept). For CASE-02 also: the pre-validation scratch directory, the self-test runs of the three contexts, and the sealed raw model-call records (their checksums are in `tasks/CASE-02/outputs/sealed_SHA256SUMS`).

### License

Code (scripts, RTL, testbenches, figure generator): Apache-2.0, see [`LICENSE`](LICENSE). Articles, figures and other documents and records: CC BY 4.0, see [`LICENSE-docs.md`](LICENSE-docs.md). Exceptions: third-party license files in `env/licenses/` keep their own licenses; the model answers in `tasks/CASE-01/diag/outputs/`, `tasks/CASE-01/revise/outputs/` and `tasks/CASE-02/outputs/` are included verbatim as research records.

### Commit history

The history was rewritten five times on 2026-10-17 before publication, so every commit id changed. Records written before that cite the original ids; see [`docs/history/HISTORY_REWRITE_2026-10-17.md`](docs/history/HISTORY_REWRITE_2026-10-17.md).

The nine `yosys.log` files under `tasks/CASE-01/evidence/F0_v1.1_synth_recipe/` still contain the local scratch-directory path (a Windows user directory) of the machine they were generated on in 2026-10-09. They are frozen evidence locked by that directory's `SHA256SUMS`, so they are left unchanged; noted here on 2026-10-30.

---

## 中文

这个项目用可复现的实验，检验大模型给出的时序诊断和 RTL 修改建议：先冻结设计、约束和分析配置，再让模型读报告、下诊断，然后用开源工具逐条核对；下一步让模型改 RTL，再做功能和时序复验。结果不好也照实发表。

工具：Yosys、OpenSTA、Icarus Verilog，单元库 SkyWater Sky130 `sky130_fd_sc_hd`。结论只在综合后、理想时钟、不计布线寄生的固定分析模型和 6 个 PVT 点之内成立，不代表流片后的芯片。

### 文章

| 文章 | 公众号版 | 完整版（每个数字标出处） |
|---|---|---|
| 1. 大模型看时序报告靠谱吗？我用 OpenSTA 核对了 Claude Opus 5.5、Kimi K3、DeepSeek V4 Pro 的诊断（CASE-01 阶段 A） | [`docs/posts/article1_public.md`](docs/posts/article1_public.md) | [`docs/posts/article1_draft.md`](docs/posts/article1_draft.md) |
| 2. 让大模型动手改 RTL：Claude Opus 5.5、Kimi K3、DeepSeek V4 Pro 交了 6 份，冻结流程里只有 1 份拿到有效时序结果（CASE-01 阶段 B） | [`docs/posts/article2_public.md`](docs/posts/article2_public.md) | [`docs/posts/article2_draft.md`](docs/posts/article2_draft.md) |
| 3. 约束漏了 128 条，slack 反而变好：Claude Opus 5.5、DeepSeek V4 Pro、Kimi K3 怎么查出来（CASE-02） | [`docs/posts/article3_public.md`](docs/posts/article3_public.md) | [`docs/posts/article3_draft.md`](docs/posts/article3_draft.md) |
| 4. 芯片冷的时候反而更慢？我用 OpenSTA 亲手跑了一遍温度反转，也问了三个大模型（STA 学习笔记） | [`docs/posts/article4_public.md`](docs/posts/article4_public.md) | 只有一个版本；OpenSTA 原样输出和出图脚本在 [`docs/posts/figs/article4/`](docs/posts/figs/article4/) |
| 5. 给 AI 出时序题：怎样证明埋进去的恰好是这一个 bug（测 AI 的方法 1/7，CASE-02） | [`docs/posts/article5_public.md`](docs/posts/article5_public.md) | [`docs/posts/retro/01_making_the_task.md`](docs/posts/retro/01_making_the_task.md)（短文版，文末有数字出处） |
| 6. AI 的时序诊断怎么判：对、错，和判不了的那些（测 AI 的方法 2/7，CASE-01 阶段 A） | [`docs/posts/article6_public.md`](docs/posts/article6_public.md) | [`docs/posts/retro/02_judging_a_sentence.md`](docs/posts/retro/02_judging_a_sentence.md)（短文版，文末有数字出处） |
| 7. setup slack 到底是怎么算出来的？我在 OpenSTA 里改了 6 个条件，一笔一笔对账（STA 学习笔记） | [`docs/posts/article7_public.md`](docs/posts/article7_public.md) | 只有一个版本；OpenSTA 原样输出和出图脚本在 [`docs/posts/figs/article7/`](docs/posts/figs/article7/) |

CASE-02 的实验笔记见 [`tasks/CASE-02/NOTES.md`](tasks/CASE-02/NOTES.md)。

### 复现

想自己验证结论，不用作者跑出的结果：先按 [`env/SETUP.md`](env/SETUP.md) 搭好环境，再按 [`REPRODUCE.md`](REPRODUCE.md) 从 RTL 重新生成基线、重跑全部基础核对和重查，并与仓库里的输出逐份比对；判断和标签也可以按规程独立重做。

阶段 B（文章 2）按 [`REPRODUCE_stageB.md`](REPRODUCE_stageB.md) 重新评估 6 份候选 RTL、从存档重算；作者从干净克隆实测，6 份与存档比对都是 `same`。CASE-02 按 [`REPRODUCE_case02.md`](REPRODUCE_case02.md) 做离线核验、三组冻结的 STA 运行、第 2 轮查询和执行契约验收；作者从干净克隆实测，三组运行与记录逐字节相同（含绝对路径的库文件行除外），验收样例全部通过。每份说明都写明了没有覆盖的部分。

### 目录

| 位置 | 内容 |
|---|---|
| `docs/posts/` | 文章和配图（`figs/article{1,2,3}/make_figs.js` 生成配图，`make_cover.js` 生成封面，`wechat/make_wechat.py` 生成公众号页面） |
| `env/` | 开源 EDA 环境的安装记录、校验和、单元库套件、冒烟测试 |
| `tasks/CASE-01/` | 第一个案例：合同 `spec.md`、RTL、参考模型、测试平台、综合和 STA 脚本、冻结证据 |
| `tasks/CASE-01/diag/` | 阶段 A：三个模型的诊断规程、材料包、答复、判断记录 `claims.tsv`、工具重查的原始输出、统计 |
| `tasks/CASE-01/diag/stats_revised.md` | 最终标签的统计（揭盲后复核修订后）；原始统计见 `diag/stats.md` |
| `tasks/CASE-01/revise/` | 阶段 B：规程、题目和材料包、模型答复、6 份候选 RTL 的评估结果、判据判定、网表兼容性诊断、测试；候选的 RTL 和综合配置在 `tasks/CASE-01/rtl/dot4sat_cand_*.v` 和 `config/impl.cand_*.cfg` |
| `tasks/CASE-02/` | 第二个案例：规程、预验证、三组冻结的 STA 记录、材料包、两轮模型答复、第 2 轮查询及逐命令记录、判断记录 `claims.tsv`、证据对应表、统计 `stats.md`、实验笔记 `NOTES.md` |
| `docs/history/` | 2026-10-17 历史改写的新旧提交号对照 |

### 不在仓库里的东西

- 作者本地的工作记录（会话交接笔记）、环境调试记录（原 `docs/env/`）、三个实验各自的介入日志和事故说明。仓库里有些文件提到 `docs/env/` 下的问题编号，这些文件不在公开仓库里。
- 执行计划、实现计划和预先验证的原型代码；对计划、规程、文章和实验笔记的外部评审记录及其处理说明；阶段 A 揭盲后复核的逐条裁定。`stats_revised.md` 由裁定表生成，脚本 `diag/scripts/claims_stats_revised.py` 在仓库里，但没有裁定表无法重算。
- CASE-02 的预验证草稿目录、三组运行的自测副本、模型调用的封存原始记录（校验和在 `tasks/CASE-02/outputs/sealed_SHA256SUMS`）。
- 商业 EDA 工具的调用脚本和任何商业工具的输出。
- 模型调用所用的密钥配置；仓库里 `tasks/CASE-01/diag/models/`、`tasks/CASE-01/revise/models/`、`tasks/CASE-02/models/` 是去掉密钥后的副本。
- 运行目录 `tasks/*/runs/` 和归档副本，只保留校验和。

### 许可

- 代码（脚本、RTL、测试平台、配图生成脚本等）：Apache-2.0，见 [`LICENSE`](LICENSE)。
- 文章和图，以及其他说明文档和实验记录：CC BY 4.0，见 [`LICENSE-docs.md`](LICENSE-docs.md)。
- 例外：`env/licenses/` 中第三方单元库和 PDK 的许可文件按其原许可；`tasks/CASE-01/diag/outputs/`、`tasks/CASE-01/revise/outputs/`、`tasks/CASE-02/outputs/` 中的模型答复原文作为研究记录原样收录。

### 关于提交历史

2026-10-17 公开之前改写过五次历史，提交号全部变了。改写之前写成的记录里引用的是原始提交号，对照表见 [`docs/history/HISTORY_REWRITE_2026-10-17.md`](docs/history/HISTORY_REWRITE_2026-10-17.md)。

`tasks/CASE-01/evidence/F0_v1.1_synth_recipe/` 下的 9 个 `yosys.log` 保留了 2026-10-09 生成时所在机器的本机临时目录路径（一个 Windows 用户目录）。它们是被该目录 `SHA256SUMS` 锁定的冻结证据，不再改动；2026-10-30 在此登记。
