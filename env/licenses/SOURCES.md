# 许可来源

> 落实执行计划修订记录 R1 第 5 条第 2 项中的"适用的许可来源"。2026-10-04 取得并核对。
> 这里只记录事实和出处，不构成法律意见。

## 1. 工艺库（项目结果依赖的数据）

| 本目录文件 | 组件 | 版本 | 许可 | 取自 | sha256 |
|---|---|---|---|---|---|
| `sky130_fd_sc_hd.LICENSE` | `sky130_fd_sc_hd` 标准单元库 | 源码 commit `9cb2d7cb8ed4619094263614039a61b6b2d22a88` | Apache-2.0 | https://raw.githubusercontent.com/fossi-foundation/skywater-pdk-libs-sky130_fd_sc_hd/9cb2d7cb8ed4619094263614039a61b6b2d22a88/LICENSE | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| `open_pdks.LICENSE` | open_pdks（把上面的源码构建成 `.lib` 等文件） | `1689ac3f2dc763876eaf967227c7dfe831b031ae` | Apache-2.0 | https://raw.githubusercontent.com/RTimothyEdwards/open_pdks/1689ac3f2dc763876eaf967227c7dfe831b031ae/LICENSE | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |

核对记录：

- 单元库的源码 commit 取自安装目录 `sky130A/.config/nodeinfo.json`。对应的上游仓库是 `fossi-foundation/skywater-pdk-libs-sky130_fd_sc_hd`，GitHub API 给出的许可标识是 Apache-2.0。注意：在 `google/skywater-pdk-libs-sky130_fd_sc_hd` 里找不到这个 commit（API 返回 404）。
- 该 commit 的仓库根目录只有 `LICENSE`、`README.rst`、`cells`、`models`、`tech`、`timing`，**没有 NOTICE 文件**（`NOTICE` 返回 404）。
- 两份 LICENSE 逐字节相同，都是 Apache License 2.0 标准全文。
- 已安装的 18 个 `.lib` 文件里都没有版权或许可声明：第 1 行就是 `library (...)`，全文搜索 `copyright` 和 `license` 都是 0 处。门级仿真用到的 Verilog 模型（例如 `verilog/sky130_fd_sc_hd.v`）带有 Apache-2.0 声明头："Copyright 2020 The SkyWater PDK Authors"。
- `synth.tcl` 在综合时会读取 `libs.tech/librelane/sky130_fd_sc_hd/synth_excluded.cells`，这个文件随 open_pdks 安装。

项目目前**不分发**任何 PDK 文件，只公开它们的 sha256（见 `../sky130hd_kit/MANIFEST.txt`）。R1 第 5 条第 3 项的落实方式是在项目外做一份作者本机的私有备份（`D:\study\eda_archive\`），不是分发。将来如果要分发，按 Apache-2.0 第 4 条的要求，需要附上许可全文、保留原有的版权声明，并标明修改过的地方。还要注意，ciel 的 `common` 包里另有 xschem、klayout、ngspice 等组件的配置，各自带有许可（例如 `libs.tech/xschem/LICENSE`），需要逐个核对。

## 2. 工具（只在本机使用，不随项目分发）

下面的许可写的是本机许可文件中的内容，供参考：

| 工具 | 许可 | 本机依据 |
|---|---|---|
| Yosys | ISC | `~/tools/oss-cad-suite/license/LICENSE.yosys` |
| ABC（yosys-abc） | UC Berkeley 的 ABC 许可 | `~/tools/oss-cad-suite/license/LICENSE.abc` |
| Icarus Verilog | GPL v2 | `~/tools/oss-cad-suite/license/LICENSE.iverilog` |
| Verilator | LGPL v3 | `~/tools/oss-cad-suite/license/LICENSE.verilator` |
| OpenSTA | GPL v3 | `~/src/OpenSTA/LICENSE` |
| CUDD | BSD 风格，Regents of the University of Colorado | `~/src/cudd/LICENSE` |
| ciel | Apache-2.0 | `ciel-3.0.0.dist-info/METADATA` |

OSS CAD Suite 其余组件的许可都在 `~/tools/oss-cad-suite/license/` 下，共 57 个文件。

## 3. 项目自己的文件

`env/` 下的脚本（`open_eda_env.sh`、`sky130hd_kit/*`、`smoke/sky130/*`、`snapshot.sh`）是本项目自己写的，**采用什么许可还没有决定**，由作者决定。
