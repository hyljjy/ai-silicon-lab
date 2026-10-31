# 复现 CASE-02（IO 约束缺失的覆盖诊断）

这份说明写给想从干净克隆、只用公开文件核验或重跑 `tasks/CASE-02/` 的人。实验笔记在 `tasks/CASE-02/NOTES.md`，规程在 `tasks/CASE-02/protocol.md`（v0.3，含补记 1–3）。阶段 A 的复现见 [REPRODUCE.md](REPRODUCE.md)，阶段 B 见 [REPRODUCE_stageB.md](REPRODUCE_stageB.md)。

和前两份一样分层，能复现的程度不同：

| 层 | 内容 | 复现后应得到什么 |
|---|---|---|
| 离线核验 | 两档预登记标签、哈希清单、评分表与统计、揭盲承诺 | 不需要 EDA 环境；公开文件之间互相对得上 |
| 工具层 | mutation 预验证、13 条探针、三组正式运行、必查项、执行契约验收 | 环境版本一致时与 `queries/formal/` 和 `prevalidation/` 里的记录**逐字节相同**（时间、路径行除外） |
| 第 2 轮查询层 | 把三家第 1 轮的 31 次查询重新在两份记录的环境里执行 | 交还文本与 `queries/round2/*/query_return.txt` 相同（句柄名可能不同） |
| 判定层 | 按 `rules/scoring.md` 重新给六份答复打标签 | 你自己的 `claims.tsv`，和仓库里作者复核过的那份比对 |
| 模型层 | 让三个模型重新读材料、写两轮答复 | **不会逐字相同**；是一次新的实验 |

## 1. 离线核验（任何机器，只要有 git 和 sha256sum）

```bash
git clone <仓库> && cd ai_native_design
git tag -l 'case02*'                                  # case02-prereg、case02-prereg-round 都指向 f1cf2e6；*-old1 是补记 3 前的登记
git rev-list -n1 case02-prereg && git rev-list -n1 case02-prereg-round
cd tasks/CASE-02
grep -v '^#' rules/preregistered.txt                  # 两档清单：每个路径在标签所指提交之后不得改动
(cd package && sha256sum -c SHA256SUMS)               # 材料包 8 个文件（清单里是相对路径，要在目录内跑）
(cd prevalidation && sed '/^$/q' SHA256SUMS | grep -v '^#' | grep . | sha256sum -c)   # 预验证第一段（仓库内 78 个文件）
(cd queries/round2 && sha256sum -c SHA256SUMS)        # 31 个第 2 轮实例目录，248 个文件
for v in correct missing restored; do (cd queries/formal/$v && sha256sum -c SHA256SUMS); done
sha256sum outputs/mapping.json | cut -c1-64; cut -c1-64 outputs/mapping.sha256     # 揭盲：承诺与对应表一致
sha256sum outputs/assign.json  | cut -c1-64; cut -c1-64 outputs/assign.sha256
python3 -B scripts/claims_stats.py --claims claims.tsv --evidence evidence_map.tsv --mapping outputs/mapping.json \
  --codes A,B,C --budgets round2/A_budget.json round2/B_budget.json round2/C_budget.json --out /tmp/stats.md && diff /tmp/stats.md stats.md
python3 -B scripts/label_check.py package/context.md prompts/round1_user.md prompts/round2/*.md round2/*_results.md   # LABEL OK
# 不需要 EDA 的测试（Windows 或 WSL 都可以）。两个前提：runs/ 目录不进 git，先建；外壳的隐私自检要求 git user.email 非空
mkdir -p runs && git config user.email you@example.com
python3 -B -m unittest scripts.test_claims_stats scripts.test_label_check scripts.test_run_round
```

`claims_stats.py` 校验字段取值、引用的调用是否成功完整、交还行号是否在调用范围内、F7 层次与证据行是否相符，并重算 `stats.md`；`diff` 应为空。`outputs/sealed_SHA256SUMS` 列的是作者本机封存目录的 56 个文件（模型调用的原始事件流、元数据、答复），它们**不在仓库里**；`outputs/calls_meta.tsv` 是从其中九个 `*.meta.json` 摘的字段，每行带原件的 sha256。

## 2. 工具层（WSL Ubuntu-24.04，OpenSTA 3.1.0 commit 7a034b56，`env/snapshot.sh check` 通过）

前提：**F1 基线归档** `tasks/CASE-01/evidence/F1/archive/20261009-092827-base-T27.91/`（86 个文件：`synth/netlist.v`、`inputs/`、`sta/` 等）**不进 git**，仓库只跟踪它的哈希清单 `tasks/CASE-01/evidence/F1/archive/SHA256SUMS`；三组运行（`run_context.py`）从这里读网表、输入和 F1 的比较基线。干净克隆里没有它，要先按 `REPRODUCE_stageB.md` 重建 F1 基线、把运行目录放到这个路径，再核对：

```bash
cd tasks/CASE-01/evidence/F1/archive && grep '20261009-092827-base-T27.91/' SHA256SUMS | sha256sum -c   # 86 / 86 OK 才继续
```

预验证脚本 `prevalidation/run.sh` 另外要 `tasks/CASE-01/runs/20261009-092827-base-T27.91/`（同一份运行目录在 `runs/` 下的位置）。CASE-02 的正确版按哈希引用 F1 冻结的 SDC（`b8d1aab6…`），缺失版是 `tasks/CASE-02/sdc/case02_missing_inb.tcl`。

```bash
cd tasks/CASE-02
# (a) mutation 预验证与 13 条探针：按 prevalidation/README.md，输出到 prevalidation/rerun/（不进 git）
# (b) 三组正式运行（每个一个新 OpenSTA 进程，拒绝覆盖已有目录；先把 queries/formal/<版本> 移开或改用 --selftest 写到 queries/selftest/）
python3 -B scripts/run_context.py correct  --selftest
python3 -B scripts/run_context.py missing  --selftest
python3 -B scripts/run_context.py restored --selftest
for v in correct missing restored; do
  diff <(grep -v '^LIB' queries/selftest/$v/sta_results.tsv) <(grep -v '^LIB' queries/formal/$v/sta_results.tsv)   # LIB 行含绝对路径，按 rules/lib_normalize.txt 规范化后比较
  cmp queries/selftest/$v/expanded.sdc queries/formal/$v/expanded.sdc
done
# (c) 自测分配表（固定 R1=正确版、R2=缺失版，与正式分配无关；run_query --selftest 和验收都要它，不进 git）
python3 -B -c "import sys; sys.path.insert(0,'scripts'); import contexts; print(contexts.commit(selftest=True))"
# (d) 执行契约验收（七个样例，约 25 分钟；(v) 会真的跑满 600 s 时限）。注意：某个样例没跑成时 report 仍会从已有记录出报告，先看 run 的输出
python3 -B scripts/acceptance.py run && python3 -B scripts/acceptance.py report && head -3 prevalidation/acceptance/RESULT.md
# (e) 预演（不需要 EDA）
python3 -B scripts/rehearse.py run | tail -2
# (f) WSL 侧单元测试（test_run_round、test_label_check 是 Windows 侧的一对，在 Windows 跑）
python3 -B -m unittest $(for f in scripts/test_*.py; do b=$(basename $f .py); case $b in test_run_round|test_label_check) ;; *) echo scripts.$b;; esac; done)
```

应得到：三个版本的 `valid.json` 都是 `run_valid=true`、`mutation_verified=true`；缺失版 `expanded.sdc` 相对正确版恰好少 `rules/mutation_lines.txt` 的 128 条；`ACCEPTANCE OK`；`RESULT: PASS`。

## 3. 第 2 轮查询层（同上环境）

```bash
cd tasks/CASE-02
# 自测分配里 R2 才是缺失版，所以要和正式的 R1（缺失版）实例比；先做第 2 节 (c)
python3 -B scripts/run_query.py --id A2_R2 --ctx R2 --query round2/q/A2.tcl --selftest --uncommitted-ok   # 任一单位
diff <(sed 1d runs/<新目录>/query_return.txt) <(sed 1d queries/round2/A2_R1_R1/query_return.txt)
```

31 次执行的清单在 `round2/translation.tsv`（哪一单位对哪一上下文），五项状态在 `round2/instances.tsv`。对象句柄（`_xxxx_p_Port` 之类）每次进程不同，含句柄的行（DeepSeek 的 B1）会有差异，其余应相同。

## 4. 判定层与模型层

判定层：读 `outputs/round1/<代号>.md`、`outputs/round2/<代号>.md`（只看前 120 行核心窗口）和 `round2/<代号>_results.md`，按 `rules/scoring.md` 填一份自己的 `claims.tsv`，用第 1 节的 `claims_stats.py` 校验，再和仓库里的比。模型层：材料包 `package/`、题目 `prompts/round1_user.md`、`prompts/round2/<代号>.md`、系统提示 `prompts/system.md`、去密钥的模型配置 `models/*.json` 都在仓库里；外壳 `scripts/run_round.py` 写死了作者本机的 Claude Code 副本路径和封存目录，需要改成你的；重跑是一次新实验。

## 5. 不在仓库里的东西

`interventions.md`（介入与工时）、`impl_plan.md`（实现计划，哈希在 `rules/impl_plan.sha256`）、`runs/`（运行目录、执行日志、复核说明、生成两张表的脚本）、封存目录 `D:\study\diag_sandbox\sealed-case02\`（模型调用原始记录）、归档 `D:\study\eda_archive\case02\`（验收与预验证的完整运行目录，`prevalidation/acceptance/ARCHIVE.md` 和 `prevalidation/SHA256SUMS` 第二段给出哈希）、Codex 外审的原文和处理说明（都在本机 `docs/review/`，整个目录不进仓库）。

## 实测记录

**2026-10-30，五层里能"复现"的三层（离线核验、工具层、第 2 轮查询层）都已从干净克隆跑过。** 作者的 Windows 机器；`git clone --branch revise-stageB`（本地仓库）到 `D:\study\case02_replication\clone-20261030-091606\`，HEAD `061a4c9`；离线核验在 Git Bash，工具层与查询层在 WSL Ubuntu-24.04（用户 eda，OpenSTA 3.1.0，`env/snapshot.sh check` = `SNAPSHOT OK`）。

离线核验（第 1 节）：

| 步骤 | 结果 |
|---|---|
| 标签 | `case02-prereg`、`case02-prereg-round` → `f1cf2e6`；`*-old1` → `53a7c75`、`71ffc92` |
| `rules/preregistered.txt` | 33 条非注释行 |
| `package/SHA256SUMS` | 8 / 8 OK |
| `queries/round2/SHA256SUMS` | 248 / 248 OK |
| `queries/formal/{correct,missing,restored}/SHA256SUMS` | 各 72 / 72 OK |
| 揭盲承诺 | `mapping.json`、`assign.json`、`mapping_old1.json` 的 sha256 与三份承诺文件一致 |
| `prevalidation/SHA256SUMS` 第一段 | 78 / 78 OK（第二段是仓库外归档，未核） |
| `outputs/calls_meta.tsv` | 9 行的 `source_sha256` 与 `outputs/sealed_SHA256SUMS` 一致 |
| `claims_stats.py` 重算 | rc=0，输出与 `stats.md` 逐字节相同 |
| `label_check.py` | `LABEL OK` |
| Windows 侧测试（`test_claims_stats`、`test_label_check`、`test_run_round`） | 52 项 OK（第一遍 28 个错误是 `runs/` 不存在，2 个是克隆没有 `git user.email`；都是前提，已写进第 1 节的命令） |

工具层与查询层（第 2–3 节；日志在克隆的 `tasks/CASE-02/runs/replication_wsl.log`、`replication_wsl2.log`，不进 git）：

| 步骤 | 结果 |
|---|---|
| F1 基线归档 | 克隆里没有；从作者本机原件复制 86 个文件到 `tasks/CASE-01/evidence/F1/archive/20261009-092827-base-T27.91/`，按跟踪的 `SHA256SUMS` 核对 86 / 86 OK。**第三方要按 `REPRODUCE_stageB.md` 重建**，这一步没有在本次实测里走 |
| WSL 侧单元测试 | 206 项 OK（1 项 skipped） |
| 三组运行（`run_context.py` 自测模式） | 三个版本 `run_valid=true`、`mutation_verified=true`；与 `queries/formal/` 比：`sta_results.tsv`（去掉含绝对路径的 LIB 行）、`expanded.sdc` 逐字节相同，`valid.json` 的判定字段相同，24 个 `cat_*`、12 个 `path_*`、12 个 `dcalc_*` 各 48 / 48 逐字节相同；缺失版 `allowed_changes=24` |
| 预演 | 19 组 PASS，70 个覆盖目标全部命中 |
| 查询层抽查（自测 R2 = 缺失版，对正式 R1） | A2（130 端口到达，261 行）、C4（`check_setup`，3 行）、C6（130 端口配对计数，131 行）的交还文本与 `queries/round2/{A2,C4,C6}_R1_R1/query_return.txt` 逐字节相同 |
| 执行契约验收 | 七个样例全部 OK，`ACCEPTANCE OK`；与记录的 `RESULT.md` 比，(i)(ii)(iii)(iv)(ctrl)(vii) 的行数、调用数、结果、归因相同（只有 elapsed 不同），(v) 超时样例 600 s 内跑到 5630 次调用 / 7507 行（记录为 3400 / 4535），(vi) 输出超限样例 132036 行（记录 131365）——这两项按构造随机器速度变化，预期只约束状态、结果代码、归因和交还行数，均一致 |
| 第一遍的两个坑 | 查询抽查和验收都要 `runs/selftest_assign.json`（第 2 节 (c)），克隆里没有时验收一个样例都没跑、`report` 却照旧从已有记录出报告；自测分配是 R2=缺失版，和正式分配相反 |

这次实测**没有**覆盖的：`prevalidation/` 的预验证重跑与 13 条探针（要 `tasks/CASE-01/runs/` 下的 F1 运行目录，本次没有重建）；F1 基线本身的重建；判定层、模型层按定义不是"复现"。总结：**离线核验、三组运行、预演、查询层抽查、执行契约验收 REPLICATION OK；F1 基线重建与预验证重跑未做。**
