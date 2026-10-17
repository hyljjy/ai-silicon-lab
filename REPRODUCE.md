# 复现 CASE-01 阶段 A

[English](REPRODUCE.en.md)

这份说明写给想自己验证文章 1 结论的人：不用作者跑出来的结果，从公开的材料出发重新跑一遍，再和仓库里的记录比对。

实验分三层，能复现的程度不同：

| 层 | 内容 | 复现后应得到什么 |
|---|---|---|
| 工具层 | 综合、STA、6 个基础核对、18 个重查和对照 | 环境版本一致时**逐字节相同**的网表和查询输出 |
| 判定层 | 把答复拆成判断、按规则打标签 | 你自己的判断表，和 `claims.tsv` 比对 |
| 模型层 | 让三个模型重新读材料、写答复 | **不会逐字相同**；是一次新的实验，比较结论是否相似 |

## 1. 准备环境

按 [env/SETUP.md](env/SETUP.md) 在 Ubuntu 24.04（或 WSL2 里的 Ubuntu 24.04）装好 OSS CAD Suite、OpenSTA、Sky130 PDK，跑通冒烟测试。版本必须和 [env/INSTALL_RECORD.md](env/INSTALL_RECORD.md) 一致。

**用户必须是 `eda`，HOME 必须是 `/home/eda`。** F1 的证据 `evidence/F1/sta_results.tsv` 里记着 liberty 文件的绝对路径 `/home/eda/pdk/...`，复现时要求逐字节相同。用别的用户运行，这一项必然不同。

以下命令都在 login shell 里、从 `tasks/CASE-01/` 目录执行。

## 2. 工具层

**第一步：重新生成 F1 基线。** 用冻结的评估脚本，从 RTL 开始做 RTL 仿真、综合、门级仿真和 6 个 PVT 点的 STA：

```bash
python3 scripts/grade.py --impl config/impl.base.cfg
# 另一台机器上，OpenSTA 是自己编译的，加：--allow-tool-drift
```

第一行打印 `RUN_ID=<id>`，最后一行应为 `GRADE OK`，其中 `worst_setup` 的 slack 是 `-4.189726…`（ss_n40C_1v60），`worst_hold` 是 `0.059112…`（ff_100C_1v95），面积 `45383.5264`。结果写在 `runs/<id>/`，这个目录不进 git。

**第二步：重跑全部基础核对和重查，与仓库里的输出比对。**

```bash
python3 -B diag/scripts/replicate.py --f1-run runs/<id>
# 另一台机器上，OpenSTA 是自己编译的，加：--allow-tool-drift
```

[diag/scripts/replicate.py](tasks/CASE-01/diag/scripts/replicate.py) 做三件事：

1. 核对重新生成的基线：网表的 sha256 必须等于实验时的 F1 网表；`sta_results.tsv` 和给模型看的那份最差路径报告，必须与 `evidence/F1/` 里的副本逐字节相同。
2. 把仓库里 `diag/queries/base/` 的 6 个基础核对和 `diag/queries/recheck/` 的 18 个重查，用当时实际运行的 `query.tcl`、同样的模式和 `--strict-log`，在新基线上各跑一遍。
3. 把每个新的 `query_full.txt` 与仓库里的比对，结果为三种之一：`identical`（逐字节相同）、`identical-masked`（OpenSTA 打印的对象内存地址每次运行都不同，屏蔽这些地址后相同）、`different`。

全部通过时打印 `REPLICATION OK`，报告写在 `runs/<时间>-replicate.md`。

**关于 `--allow-tool-drift`。** 评估脚本和查询执行器开始运行前，都会执行 `env/snapshot.sh check`，它会把工具二进制与 `env/tools.sha256` 比对。OpenSTA 和 CUDD 是从源码编译的，换一台机器后，即使 commit 相同，二进制也会不同。

两个脚本都有这个开关，但放宽的程度不同：

- `grade.py` 只放过 `opensta/bin/sta` 的指纹不同，快照日志的其他任何一行都不放过，包括 OSS CAD Suite 预编译包里的工具不一致、kit 脚本不一致、liberty 文件不一致和快照文件本身不一致。漂移的二进制及其 sha256 记在 `verdict.json` 的 `env_snapshot` 字段里。这是合同的 v1.4 冻结修订（`tasks/CASE-01/spec.md` 版本记录）。
- `replicate.py` 对每个查询用同一条规则，放过时在报告里注明"tool drift"。

工具是否真的等价，最终看网表哈希和查询输出。

**与预登记的关系。** 查询执行器 `run_query.py` 在实验结束后改过一次（修复在 Windows 上杀不掉子进程的问题，不影响 Linux 上的行为），已经和预登记时的执行器清单不一致，直接运行会被它的自检拦下。`replicate.py` 只跳过这一项自检，其余环境检查全部照常：环境快照、网表哈希、冻结输入、STA 记录与基线逐字节比对、日志检查。复现运行的每个 `result.json` 都标有 `"replication"` 字段。

**作者的实测（2026-10-17）。** 在作者的机器上，从一份干净的克隆出发跑完上面两步：见文末"实测记录"。

## 3. 判定层

这一层检验"判断拆得对不对、标签打得对不对"，不需要用作者的任何结果：

1. 读材料包 `diag/package/` 和三份答复原文 `diag/outputs/round1/{A,B,C}.md`、`diag/outputs/round2/{A,B,C}.md`。代号与模型的对应在 `diag/outputs/mapping.json`；想保持盲评，就先别打开它。
2. 按规程 [diag/protocol.md](tasks/CASE-01/diag/protocol.md) 第 6 节拆分判断，按第 7.3 节打标签。拆分粒度的补充规则 G1–G12 写在 [diag/claims.tsv](tasks/CASE-01/diag/claims.tsv) 开头的注释里。
3. 事实对照材料原文或工具层的输出；假设按你自己事先写下的条件，用工具层的查询或对照去检验。需要新的查询时，写成 `.tcl`，可以用 `diag/scripts/run_query.py` 的同一套执行方式运行。
4. 把你的判断表和 `diag/claims.tsv` 比对。`claims.tsv` 的 `label` 列是打标签时的原始标签，统计见 `diag/stats.md`；文章用的是揭盲后更正过的最终标签，统计见 `diag/stats_revised.md`。

如果你的判断表也按 `claims.tsv` 的列格式写，可以直接用 `diag/scripts/claims_stats.py --claims <你的表>` 得到同样格式的统计。

## 4. 模型层

材料包、两轮题目（`diag/prompts/`）、系统提示、去掉密钥后的模型配置（`diag/models/`）都在仓库里。重跑得到的答复不会和原答复逐字相同：模型有随机性，服务端的模型也可能更新。这样的重跑是一次新的实验，适合比较"结论是否相似、是否犯同类错误"。

运行脚本 `diag/scripts/run_round.py` 写死了作者本机的命令行工具路径，需要先改成你的路径；密钥配置也要自己准备。这一层作者没有做过复现验证。

## 5. 不在仓库里的东西

执行计划、实现计划和原型代码、评审记录、介入日志、揭盲后复核的逐条裁定，以及作者本地的环境调试记录都没有公开。所以：

- 最终统计 `diag/stats_revised.md` 只能读，不能从公开文件重算；
- 预登记清单 `diag/rules/preregistered.txt` 里的 `diag/impl_plan.md` 查不到。

## 实测记录

2026-10-17，作者的机器（WSL2 Ubuntu 24.04，环境与 `env/` 快照一致），从仓库的一份干净克隆出发，按第 2 节运行：

| 步骤 | 结果 |
|---|---|
| `env/snapshot.sh check` | `SNAPSHOT OK` |
| `grade.py --impl config/impl.base.cfg` | `GRADE OK`；worst setup −4.189726 ns（ss_n40C_1v60，in2reg），worst hold +0.059113 ns（ff_100C_1v95），面积 45383.5264 |
| F1 基线比对 | 网表 sha256、`sta_results.tsv`、最差路径报告与实验时逐字节相同 |
| 6 个基础核对 | 6 个 `identical` |
| 18 个重查和对照 | 17 个 `identical`，`rc_A-1-093` 为 `identical-masked`（它打印了对象内存地址） |
| 总结 | `REPLICATION OK`，从生成基线到比对完成约 6 分钟 |

这次实测**没有**覆盖的：

- 另一台机器、从零安装的环境。`--allow-tool-drift` 这条路径在作者机器上用不到（快照完全一致），没有实际走过。
- 判定层由其他人独立重做。
- 模型层的重跑。
