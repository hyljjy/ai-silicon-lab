# CASE-02 第 2 步预验证：最小证据集（进 git）

规程 v0.3 第 9 节规定的 `prevalidation/`。结论在 `../appendix_A.md`；本目录是它引用的原始输出里**足以重跑并核对结论**的最小集合。工作目录 `../scratch/`（不进 git）的全部原件已整目录复制到 `D:\study\eda_archive\case02\prevalidation\`（仓库外）。

## 目录

| 路径 | 内容 |
|---|---|
| `sta_run_case02.tcl`、`driver.diff` | F1 冻结 `tasks/CASE-01/scripts/sta_run.tcl` 的复制，只改第 24 行（SDC 从 `SDC_FILE` 读） |
| `case02_missing_inb.tcl` | 缺失版 SDC（`ins_drive` 130 位 / `ins_delay` 66 位） |
| `mutation_lines_draft.txt` | 128 条目标清单 = F1 `expanded.sdc` 第 141–268 行 |
| `expanded_correct_vs_missing.diff` | `diff runs/correct_1/expanded.sdc runs/missing_1/expanded.sdc`：`141,268d140` |
| `run.sh` | 跑一次完整记录（适配件，见下） |
| `probe/safe_query.diff` | 阶段 A `diag/scripts/diag_query.tcl` 的唯一改动（第 8 行） |
| `probe/q1…q13*.tcl` | 13 条探针查询，每个文件头有说明 |
| `probe/run_probe.sh`、`run_probe300.sh`、`run_all.sh` | 跑探针（适配件，见下） |
| `probe_out/<探针>_<版本>/query.txt`、`cmd.txt` | 每条探针的查询部分原始输出和运行参数（`env/`、`full.log` 在归档） |
| `runs/<版本>_<次>/sta_results.tsv`、`expanded.sdc`；`runs/missing_1/sta.log` | 四次运行的记录文件；缺失版日志 65 行 = 警告块 |
| `MANIFEST.tsv` | `scratch/` 全部 1421 个文件的去向（git / archive）、类别、原始 sha256、适配后 sha256、用途、来源关系 |
| `SHA256SUMS` | 两段：第一段仓库内文件（路径基准：本目录），第二段归档件（路径基准：归档根目录） |

## 原件与适配件

`run.sh`、`probe/run_probe.sh`、`probe/run_probe300.sh` 的原件写死了 `/mnt/d/study/ai_native_design/...` 绝对路径；仓库里的是改为仓库相对路径、输出改到 `rerun/`（不进 git）的适配件，`MANIFEST.tsv` 的 `original_sha256` / `adapted_sha256` 两列分别是原件和适配件的哈希。`probe/run_all.sh` 的原件只覆盖 q1–q8，适配件扩展到 q1–q13，并按历史运行选择运行器和模式。历史输出（`probe_out/`、`runs/`）由原件产生；重跑由适配件产生，两者不混放。

`probe/safe_query.tcl`（阶段 A 安全解释器复制件）不入库，重跑时由 `run_probe.sh` 用 `patch` 从 `tasks/CASE-01/diag/scripts/diag_query.tcl` 和 `probe/safe_query.diff` 生成到 `rerun/`。

`probe_out/*/cmd.txt` 保留历史的绝对路径原文。路径迁移映射：`/mnt/d/study/ai_native_design/tasks/CASE-02/scratch/` → 本目录；`/mnt/d/study/ai_native_design/tasks/CASE-01/...` → 仓库 `tasks/CASE-01/...`。复现不依赖这些路径。

## 重跑步骤（WSL Ubuntu-24.04，用户 eda，OpenSTA 3.1.0 commit 7a034b56）

前提：F1 基线运行目录 `tasks/CASE-01/runs/20261009-092827-base-T27.91/`（不进 git）已按 `tasks/CASE-01/revise/REPRODUCE.md` 重建；`env/snapshot.sh check` 通过。

```bash
cd tasks/CASE-02/prevalidation
./run.sh correct_1 correct && ./run.sh missing_1 missing      # -> rerun/runs/
cmp rerun/runs/correct_1/expanded.sdc runs/correct_1/expanded.sdc
cmp rerun/runs/missing_1/sta_results.tsv runs/missing_1/sta_results.tsv
./probe/run_all.sh                                             # 全部 13 条探针 -> rerun/probe_out/（q12 约 5 分钟）
```

单条探针：`./probe/run_probe.sh q13_calib_missing missing q13_calib.tcl whatif`；q12 用 `./probe/run_probe300.sh q12_sixscene_missing missing q12_sixscene.tcl`。每条探针的 `cmd.txt` 里 `env_records_identical_to_ref=1` 表示重建的记录与参考运行逐字节相同（先跑过 `run.sh <kind>_1` 时参考是完整文件集，否则只是仓库里的 `sta_results.tsv` 和 `expanded.sdc`）。`q*.txt` 的时间和路径行会不同，其余内容应相同。

## 核验哈希

```bash
cd tasks/CASE-02/prevalidation && sed '/^$/q' SHA256SUMS | grep -v '^#' | grep . | sha256sum -c   # 第一段
cd /d/study/eda_archive/case02/prevalidation && sha256sum -c SHA256SUMS                           # 第二段（原件）
```

## 说明

- 文件里带 `correct` / `missing` 字样。这是操作者一侧的预验证证据，不给被测模型；规程第 6.2 节禁止的是模型可见材料里出现内部标签。
- `runs/correct_2`、`missing_2` 只是同版本的重复运行，用来核对记录文件逐字节稳定，不是规程第 4.2 节的恢复版。
- 数值只在固定模型下、std 六个 PVT 点内成立。
- 探针用 600 s 时限（q12 300 s）直接启动 `sta`，没有经过正式交还链；正式交还链的验收记录将放在本目录 `acceptance/`（规程第 6.4 节末条）。
