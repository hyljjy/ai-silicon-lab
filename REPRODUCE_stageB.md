# 复现 CASE-01 阶段 B

这份说明写给想自己验证文章 2 结论的人：不用作者跑出来的结果，从公开的材料出发，重新评估三家模型交来的 6 份候选 RTL，再和仓库里的存档比对。阶段 A 的复现见 [REPRODUCE.md](REPRODUCE.md)。

阶段 B 的实验分四层，能复现的程度不同：

| 层 | 内容 | 复现后应得到什么 |
|---|---|---|
| 工具层 | 用冻结的评估脚本重新评估 6 份候选 | 结果和存档相同；只差仓库所在路径和运行编号里的时间戳 |
| 计算层 | 从存档重算对照矩阵、候选状态、预测判定和跨轮覆盖 | 每个重算结果与仓库里的文件**逐字节相同** |
| 判定层 | 把答复里的预测和失败条件转写成可判定的行 | 你自己的转写表，和仓库里的比对 |
| 模型层 | 让三个模型重新读材料、交候选 | **不会逐字相同**；是一次新的实验 |

## 1. 准备环境

和阶段 A 相同：按 [env/SETUP.md](env/SETUP.md) 在 Ubuntu 24.04（或 WSL2 里的 Ubuntu 24.04）装好环境，用户必须是 `eda`，HOME 必须是 `/home/eda`（理由见 REPRODUCE.md 第 1 节）。以下命令都在 login shell 里、从 `tasks/CASE-01/` 目录执行。

## 2. 补上 F1 基线原件

阶段 B 的所有对照都以 F1 基线为准。对照脚本读的是基线运行目录里的原件：`verdict.json`、`sta/sta_results.tsv` 和 12 份最差路径报告 `sta/path_{max,min}_<角>.rpt`，并先用 `evidence/F1/archive/SHA256SUMS` 逐个核对。这个运行目录的完整拷贝没有放进仓库，需要自己补上：

```bash
out=$(python3 scripts/grade.py --impl config/impl.base.cfg); echo "$out" | tail -1
id=$(echo "$out" | sed -n 's/^RUN_ID=//p')
A=evidence/F1/archive/20261009-092827-base-T27.91
mkdir -p $A/sta
cp runs/$id/sta/sta_results.tsv runs/$id/sta/path_*.rpt $A/sta/
cp evidence/F1/f1_run_verdict.json $A/verdict.json
(cd evidence/F1/archive && grep -E '20261009-092827-base-T27.91/(verdict\.json|sta/sta_results\.tsv|sta/path_)' SHA256SUMS | sha256sum -c --quiet) && echo "SHA256 OK"
python3 -B -c "import sys; sys.path.insert(0, 'revise/scripts'); import baseline; p = baseline.verify(); print('\n'.join(p) if p else 'BASELINE OK')"
```

第一行应以 `GRADE OK` 结尾，数值和 REPRODUCE.md 第 2 节相同（另一台机器上自己编译的 OpenSTA 加 `--allow-tool-drift`）。重新生成的 STA 文件与实验时逐字节相同；`verdict.json` 只有运行编号不同，所以用仓库里已有的逐字节副本 `evidence/F1/f1_run_verdict.json`。最后两行应打印 `SHA256 OK` 和 `BASELINE OK`。

不补这一步，第 4 节的重算和第 5 节的一部分测试会因为读不到原件而拒绝运行。

## 3. 工具层：重新评估 6 份候选

候选 RTL 在 `rtl/dot4sat_cand_<编号>.v`，评估配置在 `config/impl.cand_<编号>.cfg`，编号与模型的对应在 `revise/outputs/mapping_r1.json`、`mapping_r2.json`。实验时的评估结果存档在 `revise/results/r<轮>/cand_<编号>/attempt1/`。

正式评估时，评估脚本外面还套了一层包装 `revise/scripts/run_grade.py`，负责监督进程、记录尝试和存档；两轮已经关闭，它会拒绝再运行。包装不改变评估结果，复现时直接调用冻结的评估脚本：

```bash
for d in revise/results/r*/cand_*; do
  code=$(basename $d)
  out=$(python3 scripts/grade.py --impl config/impl.$code.cfg 2>&1)
  echo "$code  $(echo "$out" | tail -1 | cut -c1-100)"
  echo "$out" | sed -n 's/^RUN_ID=//p' > runs/last_$code.txt
done
```

应得到：`cand_u2pe`（Claude 第 2 轮）为 `GRADE OK`，最差 setup slack +6.104896 ns（ss_n40C_1v60），最小 hold slack +0.023094 ns（ff_n40C_1v95），面积 48666.6752；其余 5 份都是 `GRADE FAIL`，停在 STA 读网表这一步（`sta failed`，网表里的 `wire signed` 声明，见文章 2 第 5 节）。

然后和存档比对。存档里的日志和 `verdict.json` 记着作者机器上的仓库路径和运行编号，比对前要把这两样替换掉：

```bash
for d in revise/results/r*/cand_*; do
  code=$(basename $d); new=runs/$(cat runs/last_$code.txt)
  python3 - $d/attempt1 $new <<'EOF'
import json, os, re, sys
old, new = sys.argv[1], sys.argv[2]
ROOT, STAMP = re.compile(r"/[^\"\s]*?/tasks/CASE-01"), re.compile(r"\d{8}-\d{6}-")
mask = lambda s: STAMP.sub("<STAMP>-", ROOT.sub("<CASE>", s))
def norm(x):
    if isinstance(x, dict): return {k: norm(v) for k, v in x.items()}
    if isinstance(x, list): return [norm(v) for v in x]
    return mask(x) if isinstance(x, str) else x
load = lambda p: norm(json.load(open(p, encoding="utf-8")))
bad = [] if load(f"{old}/verdict.json") == load(f"{new}/verdict.json") else ["verdict.json"]
for f in sorted(os.listdir(f"{old}/sta")):
    a, b = open(f"{old}/sta/{f}", "rb").read(), open(f"{new}/sta/{f}", "rb").read()
    if a != b and mask(a.decode()) != mask(b.decode()):
        bad.append(f"sta/{f}")
print(os.path.basename(os.path.dirname(old)), "same" if not bad else "DIFF " + " ".join(bad))
EOF
done
```

6 行都应为 `same`。`cand_u2pe` 的 50 份 STA 文件逐字节相同；另外 5 份只有一个 `sta/sta.log`，替换路径后相同，报错的网表行号也相同。

## 4. 计算层：从存档重算

对照矩阵、候选状态、预测判定、跨轮覆盖都由脚本从存档计算出来。每个脚本都有 `--check` 模式：重算一遍，与仓库里的文件逐字节比较，不写任何文件。

```bash
for c in "judge.py run 1" "judge.py views 1" "judge.py run 2" "judge.py views 2" \
         "coverage.py compute" "status.py finalize 1" "status.py finalize 2" "compare.py matrix cand_u2pe 2"; do
  python3 -B revise/scripts/$c --check && echo "OK   $c" || echo "FAIL $c"
done
```

8 行都应为 `OK`。对照矩阵只有 `cand_u2pe` 一份：只有 STA 通过的候选才有矩阵。

这一层只检验"从存档到结论的计算没有错"，输入是作者的存档；工具层检验的是存档本身能不能重新得到。

## 5. 测试

脚本的单元测试分两边跑，不用 `discover`：

```bash
# WSL（从 tasks/CASE-01）
python3 -B -m unittest revise/diag_netlist/test_diag_netlist.py
cd revise/scripts && python3 -B -m unittest test_revpaths test_limits test_stops test_mapping test_prereg test_baseline test_classify test_extract test_gate test_run_grade test_status test_compare test_judge test_coverage test_feedback test_build test_round
```

```bash
# Windows（从 tasks/CASE-01，Windows 上的 Python）
python -B -m unittest revise/diag_netlist/test_diag_netlist.py
cd revise/scripts && python -B -m unittest test_revpaths test_limits test_stops test_mapping test_prereg test_baseline test_classify test_extract test_status test_compare test_judge test_coverage test_feedback test_build test_run_revise
```

两边都需要先做第 2 节。作者的结果见文末实测记录。

## 6. 判定层

这一层检验"预测和失败条件转写得对不对"：

1. 读三份公开答复 `revise/outputs/r1/cand_*.md`、`revise/outputs/r2/cand_*.md`。答复里的预测表已由脚本抽取为 `revise/predictions/r<轮>_extracted.jsonl`，抽取规则见规程 [revise/protocol.md](tasks/CASE-01/revise/protocol.md) 第 10.1 节。
2. 按第 10.1、10.2 节把每条预测和失败条件转写成可判定的行，与 `revise/predictions/r<轮>_criteria.jsonl`（阅读版 `.tsv`）比对。第 2 轮的跨轮对应按第 10.4 节，与 `r2_coverage.jsonl` 比对。
3. 用你的转写表跑 `judge.py run <轮>`，得到你自己的判定，与 `r<轮>_judgments.md` 比对。

## 7. 模型层

材料包（`revise/package/`）、两轮题目和反馈模板（`revise/prompts/`）、系统提示、去掉密钥后的模型配置（`revise/models/`）都在仓库里。运行脚本 `revise/scripts/run_revise.py` 写死了作者本机的命令行工具路径（`CLI_PATH`），需要先改成你的路径；密钥配置要自己准备。重跑得到的候选不会和原来逐字相同。这一层作者没有做过复现验证。

## 8. 预登记

规程第 3 节规定了两档预登记，用 git 标签固定：

| 标签 | 提交 | 内容 |
|---|---|---|
| `revise-prereg-smoke` | `122761f` | 第一档（冒烟之前）：规程、题目、材料包、全部脚本和测试、门槛规则、暂定期望值 |
| `revise-prereg` | `9c35afe` | 第二档（冒烟之后）：冒烟记录、最终期望值、全部预登记文件的 sha256 |
| `revise-prereg-old1` | `8c2a67d` | 第二档的第一版。清单里 `tests_tier1.txt` 的哈希按 Windows 工作区的 CRLF 换行算错了，修正后重打 `revise-prereg`，旧标签按规程保留 |

核对预登记文件之后有没有被改过（`impl_plan.md` 不公开，要去掉那一行）：

```bash
cd ../..   # 仓库根目录
for t in 1 2; do grep -v 'impl_plan.md' tasks/CASE-01/revise/rules/prereg_tier$t.sha256 | sha256sum -c --quiet && echo "tier$t OK"; done
```

## 9. 不在仓库里的东西

- 实现计划 `revise/impl_plan.md`（预登记清单里有它的哈希，但文件不公开）、介入日志 `revise/interventions.md`、对规程和文章的外部评审记录。
- 模型调用的原始记录（原始 stream-json、命令行、时间，含账号信息）和加盐对应表的原文。公开的是脱敏后的答复和揭盲后的对应表；对应表的哈希承诺在每轮开始前就已提交（`revise/outputs/mapping_r<轮>.sha256`）。
- 运行目录 `tasks/*/runs/` 和 F1 归档副本，只保留校验和。所以网表兼容性诊断（`revise/diag_netlist/`）的结果记录 `revise/notes/netlist_diagnosis_results.md` 可以读；要重跑诊断，需要先按第 3 节重新评估、再把脚本里查找运行目录的方式改成你的运行编号，这一步作者没有验证过。

## 实测记录

2026-10-27，作者的机器（WSL2 Ubuntu 24.04，环境与 `env/` 快照一致），从仓库的一份干净克隆出发，把本说明第 2、3、4、8 节的命令块原样执行：

| 步骤 | 结果 |
|---|---|
| 第 2 节：补 F1 基线原件 | `GRADE OK`（数值与 F1 相同），`SHA256 OK`（14 个文件），`BASELINE OK` |
| 第 3 节：重新评估 6 份候选 | `cand_u2pe` 为 `GRADE OK`，其余 5 份为 `GRADE FAIL`（STA 读网表报错）；与存档比对 6 份都是 `same` |
| 第 4 节：从存档重算 | 8 项都是 `OK` |
| 第 5 节：测试（另一份按第 2 节补过原件的干净克隆） | WSL：网表诊断 12 个 OK，其余 478 个 OK（跳过 1 个）；Windows：12 个 OK，405 个 OK（跳过 15 个） |
| 第 8 节：预登记文件 | `tier1 OK`、`tier2 OK` |

另做了一次反向检查：故意改动重新生成的一份路径报告里的一个词，第 3 节的比对随即报 `DIFF`，说明比对确实会发现差异。

这次实测**没有**覆盖的：

- 判定层由其他人独立重做。
- 模型层的重跑。
- 网表兼容性诊断的重跑。
