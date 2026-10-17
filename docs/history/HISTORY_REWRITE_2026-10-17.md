# 2026-10-17 历史改写：新旧提交号对照

2026-10-17 公开仓库之前，改写过三次全部历史：

1. 提交者邮箱换成公开邮箱；本地工作记录 `docs/sessions/` 和商业 EDA 工具的调用脚本 `scripts/` 从所有提交中移除。
2. 执行计划 `docs/PLAN_*.md`、评审记录 `docs/review/`、实现计划和原型代码（`tasks/CASE-01/impl_plan.md`、`tasks/CASE-01/plan/`、`tasks/CASE-01/diag/impl_plan.md`、`tasks/CASE-01/diag/plan/`）、揭盲后复核记录 `tasks/CASE-01/diag/review/` 从所有提交中移除。
3. 环境调试记录 `docs/env/` 从所有提交中移除。

提交内容的其他部分、提交时间和提交说明都没有变；只改动了被移除文件的提交保留为空提交。

仓库里改写之前写成的记录（介入日志、查询结果 `result.json` 中的 `repo_commit`、封存导出的 `heads.log`、冒烟总结、F1 说明等）引用的是**原始**提交号。这些记录被哈希清单锁定或属于当时的原始记录，没有改。按下表把原始编号换成新编号即可找到对应提交。文章完整版和 `build_package.py` 已改用新编号。预登记清单中的 `diag/impl_plan.md` 已不在公开仓库里。

| 原始提交 | 新提交 | 说明 |
|---|---|---|
| `1a9fb02` | `6257b8c` | Baseline: plan v1.0 + R1/R2, env snapshot, CASE-01 contract v1.2 and plan v2.1 |
| `efe631c` | `a867a68` | CASE-01: reference model f(a,b) |
| `bd83b89` | `fe7eea0` | CASE-01: valid/reset timeline (spec 2.3) |
| `7d7c060` | `542388a` | CASE-01: vectors and per-scenario coverage (spec 3.2-3.4) |
| `94e3f9c` | `ab8c72a` | CASE-01: simulation log check and shared log checker |
| `9e408bd` | `8dac50b` | CASE-01: logcheck closes its files and flags Python warning categories (task review fix) |
| `76fde5c` | `d536b7c` | CASE-01: strict testbench, self-test mutants and fixture |
| `b00009e` | `f0f2846` | CASE-01: baseline RTL (L=1); dev self-test passes |
| `f970dae` | `e0a02b4` | CASE-01: C_load extraction (0.0024 pF) |
| `b89c638` | `c9c70d0` | CASE-01: SDC, STA run and checker; 18/18 fault cases |
| `ff68a30` | `e18fc7e` | CASE-01: grader; warning whitelist approved by author |
| `20fcf94` | `3328cfc` | CASE-01: grader kills hung steps after a per-step wall-clock limit (task review fix) |
| `2cd7e59` | `f600410` | CASE-01: calibration script |
| `e542fc2` | `3be35bf` | CASE-01: calibration kills hung or interrupted steps; pristine tests (task review fix) |
| `eb734b1` | `cab6599` | CASE-01: pre-F1 grader hardening — pin top, lint RTL, re-verify frozen inputs, enforce F1 freeze, record timing target and area cap (final review fix) |
| `6880be7` | `43715a8` | CASE-01: F1 freeze |
| `982b9fb` | `e47027a` | Keep archived run copies out of git; only archive/SHA256SUMS is tracked |
| `5c549ba` | `991712b` | CASE-01: F1 README records the archive decision and its backup location |
| `4304729` | `3628434` | Terminology: use 执行计划 consistently (contract v1.2 wording fix) |
| `48690be` | `b31ee71` | CASE-01: F1 README wording fixes (read-only scope, empty stafaults dir, model qualifiers, latch condition, stage-B baseline tables, two explanations) |
| `f418866` | `3e19773` | CASE-01: F1 README notes the branch was merged into main |
| `b676ba9` | `f110357` | Session record 2026-10-04..10-09: CASE-01 F0 to F1 |
| `a8c3598` | `1015b02` | CASE-01 diag: stage-A steps 2-5 protocol v0.1 (for review) |
| `65c4e5a` | `1e6ef15` | CASE-01 diag: protocol v0.2 after method review D1 (M1-M8, S1-S12 adopted; Q1-Q8 decided) |
| `504af7b` | `60ade12` | CASE-01 diag: protocol v0.3 after targeted re-review D2 (N1-N11) |
| `24a99a0` | `e48cd61` | CASE-01 diag: implementation plan v1.0 with pre-validated prototype (43 files) |
| `513069b` | `538ef6d` | CASE-01 diag: protocol v0.4 and implementation plan v1.1 after plan review DP1 (P1-P10, Q1-Q14, D1-D6); prototype re-validated (49 files) |
| `49bc5ca` | `035ad83` | CASE-01 diag: protocol v0.5 and implementation plan v1.2 after targeted re-review DP2 (R1-R3, 7 suggestions); prototype re-validated |
| `129b8f9` | `8c3b483` | CASE-01 diag: privacy check of staged content and commit wrapper |
| `21fa7d7` | `d6eb94f` | CASE-01 diag: query sandbox with byte-exact F1 environment check; 17/17 self-test |
| `cda1ac8` | `cb03b75` | CASE-01 diag: collect query runs; assemble round-2 results |
| `acb08b1` | `8c0d33d` | CASE-01 diag: claims table checker, counts and round-2 transitions |
| `13fff28` | `f967948` | CASE-01 diag: materials package and prompts (wording confirmed by the author) |
| `f7d7df6` | `0d0d511` | CASE-01 diag: run shell with preflight, sealed blinding, void check, rerun and resume |
| `d819016` | `0406ff7` | CASE-01 diag: round-2 extraction and rewrite rules, base checks and the pre-registration list |
| `8b812db` | `ead8f83` | CASE-01 diag: author's reference answer (before any model run) |
| `33cddd3` | `e1d39b9` | CASE-01 diag: key-free copies of the model settings (made by the author) |
| `a610a4e` | `592c1b3` | CASE-01 diag: protocol v0.6 and plan v1.3 after the failed smoke retest (output-cap field is not the effective cap; smoke gains a cap probe) |
| `26ed7e8` | `79fe256` | CASE-01 diag: smoke retest passed (protocol step 4) |
| `4ffd9c2` | `08d30f2` | CASE-01 diag: base checks and the code-mapping commitment (before any model run) |
| `774494c` | `1bfc968` | CASE-01 diag: reference answer checked against the base checks (answer unchanged) |
| `d4f673a` | `05207bd` | CASE-01 diag: round 1 answers by code |
| `501cae4` | `4d23404` | CASE-01 diag: round-1 claims split (reviewed by the author, before any recheck) |
| `c8327e6` | `4091689` | CASE-01 diag: decision rules for hypotheses (before running them) |
| `0cde6e8` | `ed85df6` | CASE-01 diag: round-1 rechecks and labels (blind-reviewed by the author) |
| `f69f9c8` | `6b0a12b` | CASE-01 diag: round-2 query results (reviewed by the author; B1/B5 extraction errors dropped) |
| `4b38cf7` | `d7910fc` | CASE-01 diag: round 2 answers by code |
| `998966e` | `13802b9` | CASE-01 diag: round-2 claims split with round-1 refs and actions (reviewed by the author); citation rows are not transitions |
| `604a16e` | `2cc9441` | CASE-01 diag: round-2 decision rules (before running them; reviewed by the author); claims checker accepts own returned results and keeps leading quotes |
| `ad39ccc` | `99e5c0a` | CASE-01 diag: round-2 rechecks and labels (blind-reviewed by the author) |
| `25dd61c` | `31ef97b` | CASE-01 diag: unblinding (commitment verified), publishable sealed records, per-model stats |
| `ae4a4a6` | `8573401` | CASE-01: article 1 draft (reviewed by a Claude subagent, confirmed by the author) |
| `5131ea4` | `4b29a5c` | CASE-01 diag: after the final review: disclose post-prereg changes (G12), round-2 coverage of round-1 judgments |
| `264048e` | `223f426` | CASE-01: article 1 final touches after the final review; session record 2026-10-12 |
| `10b81b5` | `0ddf384` | Merge diag-stageA: CASE-01 stage A steps 2-5 |
| `3339d65` | `7a9e351` | PRJ-004: kill the whole process tree on Windows too in run_limited (run_query, calibrate); self-bounded test children |
| `3c8a2a6` | `16e2baa` | PRJ-004: grade.py kills the process tree on Windows too (F1 freeze revision, contract v1.3, config/f1.sha256); build_package reads the pinned spec.md; incident note |
| `a0806cf` | `ccc2859` | Merge fix-run-limited-windows: PRJ-004 (kill process trees on Windows too; contract v1.3) |
| `31c83a2` | `5aa7e61` | Merge session-record-prj004: session record with PRJ-004 |
| `8fbd12b` | `9a6f70e` | Session record 2026-10-12: add the PRJ-004 incident and the updated next steps |
| `696bd8f` | `84ebf8f` | CASE-01 stage A: post-unblinding review (Codex-assisted, two rounds); author decisions overlay, revised stats; A2 review records |
| `9c3c352` | `6e4f223` | Article 1: revise for the post-unblinding review (author review gap, revised labels and transitions); dated corrections in the intervention log and session record |
| `3970c2c` | `8b93857` | Article 1: drop the author-review and post-unblinding review sections from the article body (kept as one pointer in §8); final labels unchanged |
| `53a2b8e` | `8c55100` | Article 1: plain-language sample (opening five sections, incl. why this plan and its framework); A3 review request to Codex |
| `a56cbcb` | `dfdd0be` | Article 1 plain sample: drop the author-background sentence |
| `f64d7c9` | `6714682` | Article 1 full version: fix stale A-2-068 label and qualify the pre-unblinding timeline (Codex A3 F3, F4); archive the A3 review |
| `c10fdcf` | `340e82e` | Article 1: plain-language public version (~5400 chars) following the Codex A3 outline and fixes |
| `ffdabc9` | `a3ebaf8` | Article 1: new title naming Claude Opus 5.5, Kimi K3, DeepSeek V4 Pro; note how model versions are identified |
| `f3e0f56` | `7095955` | A4 review request to Codex: the plain-language public version of article 1 |
| `ed5865f` | `e244425` | Article 1: apply Codex A4 (round-2 coverage wording, 33.15 ns control incl. IO delay, setup slack, 未判定 meaning, analysis simplifications; readability edits); sync full version; archive A4 review |
| `c8fecf6` | `72a027d` | Article 1 public version: 7 figures (series, circuit, timing budget, corners, pipeline cuts, local vs global, constraint vs circuit controls) with generator script; trim text the figures replace |
| `5e3c1f0` | `0c77821` | A5 review request to Codex: figures and post-A4 edits of the public version |
| `f5199c4` | `af652bb` | Merge postblind-review: post-unblinding review, revised stats, article 1 full and public versions with figures, A2-A5 review records |
| `69e9575` | `5cf9900` | Article 1 public version: apply Codex A5 (L=3 candidate redrawn as product+sum registers; circuit figure marked as RTL functional sketch, X/Y removed; all figures re-laid out for phone width 720/1440 px; near-zero value as marker; text carries details moved out of figures); archive A5 review |
| `—` | `135e508` | Prepare for publication: Apache-2.0 LICENSE, CC BY 4.0 for articles and docs, root README, commit-id map for the 2026-10-17 history rewrite; build_package pins the rewritten spec commit; article uses new commit ids; private notes and commercial-tool scripts ignored |
| `—` | `db30e06` | Article 1: link to the GitHub repository (hyljjy/ai-silicon-lab) |
| `—` | `569e3f8` | Second history rewrite before publication: plans, reviews, prototypes and post-unblinding review records kept local; update build_package spec pin, article commit ids and references, README, commit-id map |
