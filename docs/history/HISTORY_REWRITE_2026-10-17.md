# 2026-10-17 历史改写：新旧提交号对照

2026-10-17 公开仓库之前，改写过一次全部历史：提交者邮箱换成公开邮箱；本地工作记录 `docs/sessions/` 和商业 EDA 工具的调用脚本 `scripts/` 从所有提交中移除。提交内容的其他部分、提交时间和提交说明都没有变。

仓库里改写之前写成的记录（评审记录、介入日志、查询结果 `result.json` 中的 `repo_commit`、封存导出的 `heads.log` 等）引用的是**旧**提交号。这些记录被哈希清单锁定或属于当时的原始记录，没有改。按下表把旧编号换成新编号即可找到对应提交。文章完整版和 `build_package.py` 已改用新编号。

| 旧提交 | 新提交 | 说明 |
| `1a9fb02` | `8104ae6` | Baseline: plan v1.0 + R1/R2, env snapshot, CASE-01 contract v1.2 and plan v2.1 |
| `efe631c` | `054c3ac` | CASE-01: reference model f(a,b) |
| `bd83b89` | `ff3338c` | CASE-01: valid/reset timeline (spec 2.3) |
| `7d7c060` | `57579c7` | CASE-01: vectors and per-scenario coverage (spec 3.2-3.4) |
| `94e3f9c` | `cfe70cd` | CASE-01: simulation log check and shared log checker |
| `9e408bd` | `03c9dfa` | CASE-01: logcheck closes its files and flags Python warning categories (task review fix) |
| `76fde5c` | `e36116d` | CASE-01: strict testbench, self-test mutants and fixture |
| `b00009e` | `728928f` | CASE-01: baseline RTL (L=1); dev self-test passes |
| `f970dae` | `acf874d` | CASE-01: C_load extraction (0.0024 pF) |
| `b89c638` | `8e35caf` | CASE-01: SDC, STA run and checker; 18/18 fault cases |
| `ff68a30` | `fdb100b` | CASE-01: grader; warning whitelist approved by author |
| `20fcf94` | `d40a03a` | CASE-01: grader kills hung steps after a per-step wall-clock limit (task review fix) |
| `2cd7e59` | `df3ff50` | CASE-01: calibration script |
| `e542fc2` | `d7a1351` | CASE-01: calibration kills hung or interrupted steps; pristine tests (task review fix) |
| `eb734b1` | `13afb6b` | CASE-01: pre-F1 grader hardening — pin top, lint RTL, re-verify frozen inputs, enforce F1 freeze, record timing target and area cap (final review fix) |
| `6880be7` | `31ff286` | CASE-01: F1 freeze |
| `982b9fb` | `79e5f59` | Keep archived run copies out of git; only archive/SHA256SUMS is tracked |
| `5c549ba` | `b344d39` | CASE-01: F1 README records the archive decision and its backup location |
| `4304729` | `16206c1` | Terminology: use 执行计划 consistently (contract v1.2 wording fix) |
| `48690be` | `9267ab6` | CASE-01: F1 README wording fixes (read-only scope, empty stafaults dir, model qualifiers, latch condition, stage-B baseline tables, two explanations) |
| `f418866` | `d4fc0e0` | CASE-01: F1 README notes the branch was merged into main |
| `b676ba9` | `4facd81` | Session record 2026-10-04..10-09: CASE-01 F0 to F1 |
| `a8c3598` | `8e8b1ac` | CASE-01 diag: stage-A steps 2-5 protocol v0.1 (for review) |
| `65c4e5a` | `4a999f8` | CASE-01 diag: protocol v0.2 after method review D1 (M1-M8, S1-S12 adopted; Q1-Q8 decided) |
| `504af7b` | `6104252` | CASE-01 diag: protocol v0.3 after targeted re-review D2 (N1-N11) |
| `24a99a0` | `ee9fe09` | CASE-01 diag: implementation plan v1.0 with pre-validated prototype (43 files) |
| `513069b` | `3595079` | CASE-01 diag: protocol v0.4 and implementation plan v1.1 after plan review DP1 (P1-P10, Q1-Q14, D1-D6); prototype re-validated (49 files) |
| `49bc5ca` | `68f7204` | CASE-01 diag: protocol v0.5 and implementation plan v1.2 after targeted re-review DP2 (R1-R3, 7 suggestions); prototype re-validated |
| `129b8f9` | `da1f7fe` | CASE-01 diag: privacy check of staged content and commit wrapper |
| `21fa7d7` | `f205819` | CASE-01 diag: query sandbox with byte-exact F1 environment check; 17/17 self-test |
| `cda1ac8` | `5f11b96` | CASE-01 diag: collect query runs; assemble round-2 results |
| `acb08b1` | `c36cfa2` | CASE-01 diag: claims table checker, counts and round-2 transitions |
| `13fff28` | `cea03c7` | CASE-01 diag: materials package and prompts (wording confirmed by the author) |
| `f7d7df6` | `b5d8eef` | CASE-01 diag: run shell with preflight, sealed blinding, void check, rerun and resume |
| `d819016` | `bdd39a8` | CASE-01 diag: round-2 extraction and rewrite rules, base checks and the pre-registration list |
| `8b812db` | `20fabe5` | CASE-01 diag: author's reference answer (before any model run) |
| `33cddd3` | `2965637` | CASE-01 diag: key-free copies of the model settings (made by the author) |
| `a610a4e` | `4f41ffb` | CASE-01 diag: protocol v0.6 and plan v1.3 after the failed smoke retest (output-cap field is not the effective cap; smoke gains a cap probe) |
| `26ed7e8` | `bd40fe7` | CASE-01 diag: smoke retest passed (protocol step 4) |
| `4ffd9c2` | `7a2a7f4` | CASE-01 diag: base checks and the code-mapping commitment (before any model run) |
| `774494c` | `dfd45bb` | CASE-01 diag: reference answer checked against the base checks (answer unchanged) |
| `d4f673a` | `c59405f` | CASE-01 diag: round 1 answers by code |
| `501cae4` | `bbdcc3a` | CASE-01 diag: round-1 claims split (reviewed by the author, before any recheck) |
| `c8327e6` | `3c28fd7` | CASE-01 diag: decision rules for hypotheses (before running them) |
| `0cde6e8` | `8bbd3ee` | CASE-01 diag: round-1 rechecks and labels (blind-reviewed by the author) |
| `f69f9c8` | `69af811` | CASE-01 diag: round-2 query results (reviewed by the author; B1/B5 extraction errors dropped) |
| `4b38cf7` | `aeca68a` | CASE-01 diag: round 2 answers by code |
| `998966e` | `710c241` | CASE-01 diag: round-2 claims split with round-1 refs and actions (reviewed by the author); citation rows are not transitions |
| `604a16e` | `0f011e3` | CASE-01 diag: round-2 decision rules (before running them; reviewed by the author); claims checker accepts own returned results and keeps leading quotes |
| `ad39ccc` | `5c1b0dc` | CASE-01 diag: round-2 rechecks and labels (blind-reviewed by the author) |
| `25dd61c` | `a503439` | CASE-01 diag: unblinding (commitment verified), publishable sealed records, per-model stats |
| `ae4a4a6` | `12cdb74` | CASE-01: article 1 draft (reviewed by a Claude subagent, confirmed by the author) |
| `5131ea4` | `8666098` | CASE-01 diag: after the final review: disclose post-prereg changes (G12), round-2 coverage of round-1 judgments |
| `264048e` | `065316b` | CASE-01: article 1 final touches after the final review; session record 2026-10-12 |
| `10b81b5` | `cd36f23` | Merge diag-stageA: CASE-01 stage A steps 2-5 |
| `3339d65` | `a072e7a` | PRJ-004: kill the whole process tree on Windows too in run_limited (run_query, calibrate); self-bounded test children |
| `3c8a2a6` | `2284858` | PRJ-004: grade.py kills the process tree on Windows too (F1 freeze revision, contract v1.3, config/f1.sha256); build_package reads the pinned spec.md; incident note |
| `a0806cf` | `30f028c` | Merge fix-run-limited-windows: PRJ-004 (kill process trees on Windows too; contract v1.3) |
| `31c83a2` | `2a33fee` | Merge session-record-prj004: session record with PRJ-004 |
| `8fbd12b` | `71e1d53` | Session record 2026-10-12: add the PRJ-004 incident and the updated next steps |
| `696bd8f` | `84a4403` | CASE-01 stage A: post-unblinding review (Codex-assisted, two rounds); author decisions overlay, revised stats; A2 review records |
| `9c3c352` | `deacfff` | Article 1: revise for the post-unblinding review (author review gap, revised labels and transitions); dated corrections in the intervention log and session record |
| `3970c2c` | `e00c7ee` | Article 1: drop the author-review and post-unblinding review sections from the article body (kept as one pointer in §8); final labels unchanged |
| `53a2b8e` | `b16634e` | Article 1: plain-language sample (opening five sections, incl. why this plan and its framework); A3 review request to Codex |
| `a56cbcb` | `60c6091` | Article 1 plain sample: drop the author-background sentence |
| `f64d7c9` | `6382dcc` | Article 1 full version: fix stale A-2-068 label and qualify the pre-unblinding timeline (Codex A3 F3, F4); archive the A3 review |
| `c10fdcf` | `3b09923` | Article 1: plain-language public version (~5400 chars) following the Codex A3 outline and fixes |
| `ffdabc9` | `5bb2522` | Article 1: new title naming Claude Opus 5.5, Kimi K3, DeepSeek V4 Pro; note how model versions are identified |
| `f3e0f56` | `6de8eeb` | A4 review request to Codex: the plain-language public version of article 1 |
| `ed5865f` | `33ac2dd` | Article 1: apply Codex A4 (round-2 coverage wording, 33.15 ns control incl. IO delay, setup slack, 未判定 meaning, analysis simplifications; readability edits); sync full version; archive A4 review |
| `c8fecf6` | `265998d` | Article 1 public version: 7 figures (series, circuit, timing budget, corners, pipeline cuts, local vs global, constraint vs circuit controls) with generator script; trim text the figures replace |
| `5e3c1f0` | `f92ee6d` | A5 review request to Codex: figures and post-A4 edits of the public version |
| `f5199c4` | `ddc966a` | Merge postblind-review: post-unblinding review, revised stats, article 1 full and public versions with figures, A2-A5 review records |
| `69e9575` | `920a3ba` | Article 1 public version: apply Codex A5 (L=3 candidate redrawn as product+sum registers; circuit figure marked as RTL functional sketch, X/Y removed; all figures re-laid out for phone width 720/1440 px; near-zero value as marker; text carries details moved out of figures); archive A5 review |
