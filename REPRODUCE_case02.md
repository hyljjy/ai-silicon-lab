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
sha256sum -c package/SHA256SUMS                       # 材料包 8 个文件
sha256sum -c queries/round2/SHA256SUMS                # 31 个第 2 轮实例目录
for v in correct missing restored; do (cd queries/formal/$v && sha256sum -c SHA256SUMS); done
sha256sum outputs/mapping.json | cut -c1-64; cut -c1-64 outputs/mapping.sha256     # 揭盲：承诺与对应表一致
sha256sum outputs/assign.json  | cut -c1-64; cut -c1-64 outputs/assign.sha256
python3 -B scripts/claims_stats.py --claims claims.tsv --evidence evidence_map.tsv --mapping outputs/mapping.json \
  --codes A,B,C --budgets round2/A_budget.json round2/B_budget.json round2/C_budget.json --out /tmp/stats.md && diff /tmp/stats.md stats.md
```

`claims_stats.py` 校验字段取值、引用的调用是否成功完整、交还行号是否在调用范围内、F7 层次与证据行是否相符，并重算 `stats.md`；`diff` 应为空。`outputs/sealed_SHA256SUMS` 列的是作者本机封存目录的 56 个文件（模型调用的原始事件流、元数据、答复），它们**不在仓库里**；`outputs/calls_meta.tsv` 是从其中九个 `*.meta.json` 摘的字段，每行带原件的 sha256。

## 2. 工具层（WSL Ubuntu-24.04，OpenSTA 3.1.0 commit 7a034b56，`env/snapshot.sh check` 通过）

前提：F1 基线运行目录 `tasks/CASE-01/runs/20261009-092827-base-T27.91/`（不进 git）先按 `tasks/CASE-01/revise/REPRODUCE.md` 重建。CASE-02 的正确版按哈希引用 F1 冻结的 SDC（`b8d1aab6…`），缺失版是 `tasks/CASE-02/sdc/case02_missing_inb.tcl`。

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
# (c) 执行契约验收（七个样例，约 25 分钟；(v) 会真的跑满 600 s 时限）
python3 -B scripts/acceptance.py run && python3 -B scripts/acceptance.py report && head -3 prevalidation/acceptance/RESULT.md
# (d) 预演（不需要 EDA）
python3 -B scripts/rehearse.py run | tail -2
```

应得到：三个版本的 `valid.json` 都是 `run_valid=true`、`mutation_verified=true`；缺失版 `expanded.sdc` 相对正确版恰好少 `rules/mutation_lines.txt` 的 128 条；`ACCEPTANCE OK`；`RESULT: PASS`。

## 3. 第 2 轮查询层（同上环境）

```bash
cd tasks/CASE-02
python3 -B scripts/run_query.py --id A2_R1 --ctx R1 --query round2/q/A2.tcl --selftest --uncommitted-ok   # 任一单位；R2 同理
diff <(sed 1d runs/<新目录>/query_return.txt) <(sed 1d queries/round2/A2_R1_R1/query_return.txt)
```

31 次执行的清单在 `round2/translation.tsv`（哪一单位对哪一上下文），五项状态在 `round2/instances.tsv`。对象句柄（`_xxxx_p_Port` 之类）每次进程不同，含句柄的行（DeepSeek 的 B1）会有差异，其余应相同。

## 4. 判定层与模型层

判定层：读 `outputs/round1/<代号>.md`、`outputs/round2/<代号>.md`（只看前 120 行核心窗口）和 `round2/<代号>_results.md`，按 `rules/scoring.md` 填一份自己的 `claims.tsv`，用第 1 节的 `claims_stats.py` 校验，再和仓库里的比。模型层：材料包 `package/`、题目 `prompts/round1_user.md`、`prompts/round2/<代号>.md`、系统提示 `prompts/system.md`、去密钥的模型配置 `models/*.json` 都在仓库里；外壳 `scripts/run_round.py` 写死了作者本机的 Claude Code 副本路径和封存目录，需要改成你的；重跑是一次新实验。

## 5. 不在仓库里的东西

`interventions.md`（介入与工时）、`impl_plan.md`（实现计划，哈希在 `rules/impl_plan.sha256`）、`runs/`（运行目录、执行日志、复核说明、生成两张表的脚本）、封存目录 `D:\study\diag_sandbox\sealed-case02\`（模型调用原始记录）、归档 `D:\study\eda_archive\case02\`（验收与预验证的完整运行目录，`prevalidation/acceptance/ARCHIVE.md` 和 `prevalidation/SHA256SUMS` 第二段给出哈希）、Codex 外审的原文（处理说明 `docs/review/CASE02_R*_claude.md` 在仓库里）。

## 实测记录

**尚未做。** 作者定稿笔记之前，没有从干净克隆按本文件跑过；第 1 节的离线核验命令是作者本机工作区里跑通的，第 2–3 节的命令是实验期间实际用过的调用形式，但"干净克隆 + 本文件"这条路还没有走一遍。做过之后在这里写日期、机器、每一步的结果（`REPLICATION OK` 或未复现项）。
