# 证据：CASE-01 F1 冻结（作者检查点 C）

- 日期：2026-10-09。分支 `case01-impl`，冻结之前的代码提交为 `eb734b1`。
- **性质**：本目录记录 F1 冻结时的评估配置、校准依据、F1 之后的基线参考运行、自检和单元测试。F1 冻结之后，`config/f1.sha256` 列出的 14 个文件，以及 `config/f1.cfg` 和 `config/f1.sha256` 本身，任何改动都是评估修订（spec 8），要按评估修订流程记录。
- **基线参考运行不是优化结果**：`F1_RUN` 是未改动的基线 RTL 在冻结参数下的一次 grader 评估，是阶段 B 候选的对比基准。它没有达到时序目标、在面积上限之内，这是记录，不是失败。
- 下面的数值都是从文件里原样抄出来的，没有重新取整。表中带 `sha256` 的文件，哈希都是 `sha256sum` 对本目录或 `runs/` 下文件的实测值。

## 1. 冻结的评估值：`config/f1.cfg`

文件全文（LF 换行）：

```text
# CASE-01 F1 frozen evaluation values (spec 8, 9). Changing any of these is an evaluation revision.
T_ns          = 27.91
C_load_pF     = 0.0024
L_max         = 3
area_cap      = 56729.408
timing_target = setup_ge_0_std
seed          = 1
calib_session = runs/20261009-080227-calib-20261009-073842-base-T20
```

`sha256sum config/f1.cfg`：

```text
652c1f1f25be0e0996b841ba371fef5bb667d1609eb92c8e4691c9df4a63bf89  config/f1.cfg
```

- `T_ns` 取自校准记录 `calib_record.json` 的 `chosen.T_ns`；`C_load_pF` 等于 `evidence/cload_extract.json` 的 `value_pf`（见第 5 节）。
- `area_cap` 单位是 µm²，等于 1.25 × 基线面积 45383.5264 µm²（= 56729.408）。
- `timing_target = setup_ge_0_std`：在冻结的 T 下，std 六个点（tt_025C_1v80、tt_100C_1v80、ss_100C_1v60、ss_n40C_1v60、ff_n40C_1v95、ff_100C_1v95）的最差 setup slack 大于等于 0，就算 spec 6 的第三种状态"达到预定的时序目标"；hold 只做观察。
- `seed` 是 F1 之后每次评估生成向量用的种子。
- grader 逐项核对这个文件：7 个键必须齐全、不能有别的键；`T_ns` 为大于 0 的有限数；`C_load_pF` 必须等于 `evidence/cload_extract.json` 的 `value_pf`；`L_max` 为 1–3 的整数；`timing_target` 只能是 `setup_ge_0_std`；`seed` 为整数；`calib_session` 不能为空。任何一项不合格都在建 run 目录之前报错。

## 2. 冻结文件清单：`config/f1.sha256`

`config/f1.sha256`（14 行，相对路径，排序；文件列表就是 `grade.FROZEN_INPUTS`）全文：

```text
e5c832fca426132bed18af9f96147d6b706a2912813880745ccf6f026c40cde5  config/gl_models.sha256
35f1ef4b8940b67295cb8c2877658e72aff81658b9dd1bf7f054644beead52f6  config/warn_whitelist.txt
77e41009085cae58cccbc38f66767595d608bdda9b52bfd482c120c4a2037b1c  ref/coverage.py
bea960510a395395d6533e1fd1848654b24414b5ac135d9ad2ef41fa9eddf338  ref/gen_vectors.py
243fad3ab93a2a5c62abe3d78060aeb7d7bda54b388f5bdb85ace17e0f03d338  ref/model.py
eb4fac82766c172829c366799c583677aaf91a508e5ea280d04b98e9bef16021  ref/timeline.py
f34bb42f82dbe6222f6b2c900a3de1271247ae629c955fe580e07048a5097588  scripts/check_sim.py
d20ebb8f01cf3f32a5f396e9ff92d9c675d5c03a25571fbbf7f91f338b6e66db  scripts/check_sta.py
116b7ce40baeb88bc6c3f42a8f3a845e61e724c8b390230847691f1c00ab8174  scripts/grade.py
46369c783983b4c1f46cda7650f461ce56f7008519a2d6bd1de608c12604726e  scripts/logcheck.py
6728b0a4ea02ec959460654cf739131f5a4a5c48c789be926922dae93ace9fa8  scripts/sta_run.tcl
b517940e44b8d0a87a7b649f7f3355fa8960759ba436a8acf5684bf9bc674049  scripts/synth_case01.tcl
b8d1aab60d137dc39dc7cb55b2ec314b952538dfee8f5be627a140dcca09300c  sdc/case01_sdc.tcl
61a67e2ab55c719f1bcbc832ee81898d0b94e7ddd2eccaedb0bf221e885012fe  tb/tb_dot4sat.v
```

`sha256sum config/f1.sha256`：

```text
7dcf3b5c721b181bf5376ce5f07f72c38abfa2fd0ec2761a819bb8680bbf1829  config/f1.sha256
```

- `scripts/synth_case01.tcl` 为 `b517940e…`（综合配方），`config/warn_whitelist.txt` 为 `35f1ef4b…`（作者在检查点 A 批准的白名单，见第 6 节）。
- F1 之后，grader 在每次运行之前核对这 14 个文件，不一致就在建 run 目录之前报 `evaluation file changed after F1: …`；`config/f1.cfg` 和 `config/f1.sha256` 也冻结进每次运行的 `inputs/`。

## 3. 作者在三个检查点的原话

- **检查点 A（警告白名单，2026-10-09）**：作者回答"批准（推荐）"。审批记录是 `evidence/whitelist_approval.md`。
- **检查点 B（校准，2026-10-09）**：作者先回答"先看路径报告"，看过最差路径报告之后回答"接受（推荐）"，接受校准会话 `runs/20261009-080227-calib-20261009-073842-base-T20`，T = 27.91 ns。
- **检查点 C（F1 冻结参数，2026-10-09）** 的三项回答：
  - L_max：回答"L_max = 3"，理由（作者原话）："允许最大范围，看 AI 会不会选择插流水线"；
  - 资源上限：回答"1.25× 基线（推荐）"，即 area_cap = 1.25 × 基线面积 45383.5264 µm² = 56729.408 µm²；
  - 时序目标规则（spec 6 的第三种状态）：回答"6 点 setup 全 ≥ 0（推荐）"，即 `setup_ge_0_std`；hold 只做观察。

## 4. 校准会话和选定的试探

- 校准会话目录：`runs/20261009-080227-calib-20261009-073842-base-T20`（来源运行 `runs/20261009-073842-base-T20`，下文称 `BASE_RUN`；命令 `python3 scripts/calibrate.py --run runs/20261009-073842-base-T20`，`calibrate.py` 的 sha256 为 `2ca3086a6947cd7522ccb874687625f1749aa2afb5e0edbba09e32e326fe19ab`）。会话状态 `candidate_found`，公式前提成立，D_eff = 26.5177 ns（`calib_record.json` 里 `S0_ns` = -10.517727431135917，`T0_ns` = 20.0）。
- 本目录里的副本：`calib_record.md`（sha256 `2f9da51ea536f030622f93a604114360d33dbb6ca340b094e39c8f4559859db4`）和 `calib_record.json`（sha256 `46e72e1e77b8a06ea63a6502e80e90c4608d2f15a56ff1c9eab3d69a1947bb64`）。
- **选定的校准试探：#1，T = 27.91 ns，S = −4.1897 ns，S/T = −0.1501**（`calib_record.json`：`S_ns` = -4.189726018044011，`S_over_T` = -0.1501155864580441；最差 corner `ss_n40C_1v60`，类别 `in2reg`；最小 hold 0.0591 ns，在 `ff_100C_1v95`）。试探汇总（取自 `calib_record.md`）：

| # | T (ns) | S (ns) | S/T | 最差 corner | 类别 | 最小 hold（corner） | STA 目录 |
|---|---|---|---|---|---|---|---|
| 0 | 20.00 | -10.5177 | -0.5259 | ss_n40C_1v60 | in2reg | 0.0591（ff_100C_1v95） | `runs/20261009-073842-base-T20/sta` |
| 1 | 27.91 | -4.1897 | -0.1501 | ss_n40C_1v60 | in2reg | 0.0591（ff_100C_1v95） | `runs/20261009-080227-calib-20261009-073842-base-T20/trials/01_T27.91` |

- 网表 sha256：`1fa89c975162f4f1f9a2f349bed73b4dae5f53ab921883be842cb0a37763a8d1`，与 `BASE_RUN`、`F1_RUN` 相同。
- 冻结的 STA 模型指纹（`calib_record.json` 的 `chosen.model`）：`scripts/sta_run.tcl` `6728b0a4…`、`scripts/check_sta.py` `d20ebb8f…`、`sdc/case01_sdc.tcl` `b8d1aab6…`、`config/warn_whitelist.txt` `35f1ef4b…`。

### spec 5 第 2 条：最差路径的端点、arrival 和 required

两条都是 `ss_n40C_1v60` 的输入到寄存器 max 路径，起点 `in_b[2]`，终点 `_12026_/D`（`sky130_fd_sc_hd__dfxtp_1`）。数值取自下面两个 `.rpt`：

| 条件 | 报告文件 | 终点 | data arrival time | data required time | slack |
|---|---|---|---|---|---|
| T0 = 20 ns（`BASE_RUN`） | `runs/20261009-073842-base-T20/sta/cat_ss_n40C_1v60_in2reg_max.rpt`，副本 `base_run_T20_cat_ss_n40C_1v60_in2reg_max.rpt`（sha256 `6df0ac57f6ead6d6746a5e0ff7549553b66dca3c5995d06a49f8af9eece5a4a3`） | `_12026_`（`_12026_/D`） | 29.9619 | 19.4441 | -10.5177 |
| 选定 T = 27.91 ns（校准试探 #1） | `runs/20261009-080227-calib-20261009-073842-base-T20/trials/01_T27.91/cat_ss_n40C_1v60_in2reg_max.rpt`，副本 `calib_trial01_T27.91_cat_ss_n40C_1v60_in2reg_max.rpt`（sha256 `043e50bf6638284a043aec4cdf9a23ea999878a369ac58cfef7b613420f38d88`） | `_12026_`（`_12026_/D`） | 31.5439 | 27.3541 | -4.1897 |

- 两条路径经过同样的单元链，只有 input external delay 和时钟周期不同：T0 时是 4.0000 和 20.0000，选定 T 时是 5.5820 和 27.9100。库 setup time 都是 -0.5559。
- 作者在检查点 B 看的就是这份选定 T 下的路径报告。

## 5. C_load 提取和复核

- `evidence/cload_extract.json`（原记录，未覆盖）和 `evidence/F1/cload_recheck.json`（F1 时重新提取）：`cmp` 结果 `CLOAD_SAME`，两个文件的 sha256 相同：

```text
b343b32023212e38f0659313392ac982e47e3995a8f728247083f7d73cc20041  evidence/cload_extract.json
b343b32023212e38f0659313392ac982e47e3995a8f728247083f7d73cc20041  evidence/F1/cload_recheck.json
```

- 内容：`{"lib": "sky130_fd_sc_hd__tt_025C_1v80.lib", "lib_sha256": "8e78e14442062dba34d414fca6490b2f6b96038d4510d1438ca44fee31487135", "cell": "sky130_fd_sc_hd__buf_4", "pin": "A", "field": "capacitance", "value_pf": 0.0024, "unit": "pF"}`
- 复核命令：`python3 scripts/extract_cload.py $SKY130_HD/lib/sky130_fd_sc_hd__tt_025C_1v80.lib $SKY130_KIT/MANIFEST.txt`，退出码 0。

## 6. 白名单审批记录

- 审批记录：`evidence/whitelist_approval.md`（检查点 A，作者批准，2026-10-09）。
- `config/warn_whitelist.txt` 的 sha256 为 `35f1ef4b8940b67295cb8c2877658e72aff81658b9dd1bf7f054644beead52f6`，条目只有一条（yosys 的 ABC 多输出单元提示，整行精确匹配），只对 yosys 生效。
- 触发这条审批的运行 `runs/20261009-064746-pipe2-T20` 已归档（见第 13 节）。
- `F1_RUN` 的 `verdict.json` 里 `whitelist_hits` 为 `{"3": 1}`：键是白名单文件里的规则行号（第 3 行，即上面这一条），整个运行里它被命中了 1 次。

## 7. 正式自检（Step 4）

- 命令：`python3 scripts/selftest.py --lmax 3`，退出码 0，最后一行 `SELFTEST OK (selftest, lmax=3, 18 cases) -> runs/20261009-092809-selftest-lmax3`。
- **`FINAL_SELFTEST` = `runs/20261009-092809-selftest-lmax3`**。
- 本目录里的 `selftest.json` 是它的副本（sha256 `efe405ca14ade5ae8c6864338fc4bae357d51a6a2ae1b74859aa3a991ce70de5`）：`lmax` 为 3，`all_ok` 为 true，18 个用例。

## 8. F1 之后的基线参考运行（Step 5）

- 命令：`python3 scripts/grade.py --impl config/impl.base.cfg`，退出码 0。
- **`F1_RUN` = `20261009-092827-base-T27.91`**，最后一行：

```text
GRADE OK: 20261009-092827-base-T27.91 functional_pass analysis_valid worst_setup={'slack': -4.189726018044011, 'corner': 'ss_n40C_1v60', 'category': 'in2reg'} worst_hold={'slack': 0.059112952317363035, 'corner': 'ff_100C_1v95'} area=45383.5264 timing_target=setup_ge_0_std:not_met area_cap=56729.408:within
```

- `verdict.json` 的副本是 `f1_run_verdict.json`（sha256 `f2ab76b2875189fe21fbad3c5d5285726989fbfd233c30003f6a9ecc260af052`）。主要字段：`phase` = post-F1；`T_ns` = 27.91；`C_load_pF` = 0.0024；`L_max` = 3；`seed` = 1；`sceneset` = std；`latency_L` = 1；`rtl_sim` = checked=2856；`gl_sim` = checked=2856；`netlist_sha256` = `1fa89c975162f4f1f9a2f349bed73b4dae5f53ab921883be842cb0a37763a8d1`；`timing_target` = `{"rule": "setup_ge_0_std", "met": false, "worst_setup_std": -4.189726018044011}`；`area` = `{"area_um2": 45383.5264, "cap_um2": 56729.408, "within_cap": true}`；`rtl_lint` 为空。
- std 六个点的真实最差 setup slack（ns，取自 `verdict.json`）：tt_025C_1v80 11.185458209594348；tt_100C_1v80 11.317221258240215；ss_100C_1v60 -0.687277809672019；ss_n40C_1v60 -4.189726018044011；ff_n40C_1v95 15.871505448031069；ff_100C_1v95 15.894228605363333。

### Step 5 的核对（9 行都以 True 结尾）

```text
phase post-F1 True
T_ns == chosen.T_ns True
netlist == calibration netlist True
S/T in [-0.20, -0.10] True
|S - chosen.S_ns| <= 1e-6 True
model fingerprint True
timing_target.met is false True
area.within_cap is true True
f1.cfg and f1.sha256 frozen True
```

### `F1_RUN` 的 `inputs.sha256`（冻结的 18 个输入文件，含 `config/f1.cfg` 和 `config/f1.sha256`）

```text
c8ee5dbf1547374199774081a827602d4b0ff493a05dbf01f0914b0934d9679f  config/impl.base.cfg
422ba000b48903558d797510cd4d0189b3fac9f83ba4ce4a1b22eb497194c802  rtl/dot4sat.v
61a67e2ab55c719f1bcbc832ee81898d0b94e7ddd2eccaedb0bf221e885012fe  tb/tb_dot4sat.v
b8d1aab60d137dc39dc7cb55b2ec314b952538dfee8f5be627a140dcca09300c  sdc/case01_sdc.tcl
35f1ef4b8940b67295cb8c2877658e72aff81658b9dd1bf7f054644beead52f6  config/warn_whitelist.txt
e5c832fca426132bed18af9f96147d6b706a2912813880745ccf6f026c40cde5  config/gl_models.sha256
243fad3ab93a2a5c62abe3d78060aeb7d7bda54b388f5bdb85ace17e0f03d338  ref/model.py
eb4fac82766c172829c366799c583677aaf91a508e5ea280d04b98e9bef16021  ref/timeline.py
77e41009085cae58cccbc38f66767595d608bdda9b52bfd482c120c4a2037b1c  ref/coverage.py
bea960510a395395d6533e1fd1848654b24414b5ac135d9ad2ef41fa9eddf338  ref/gen_vectors.py
116b7ce40baeb88bc6c3f42a8f3a845e61e724c8b390230847691f1c00ab8174  scripts/grade.py
f34bb42f82dbe6222f6b2c900a3de1271247ae629c955fe580e07048a5097588  scripts/check_sim.py
46369c783983b4c1f46cda7650f461ce56f7008519a2d6bd1de608c12604726e  scripts/logcheck.py
d20ebb8f01cf3f32a5f396e9ff92d9c675d5c03a25571fbbf7f91f338b6e66db  scripts/check_sta.py
6728b0a4ea02ec959460654cf739131f5a4a5c48c789be926922dae93ace9fa8  scripts/sta_run.tcl
b517940e44b8d0a87a7b649f7f3355fa8960759ba436a8acf5684bf9bc674049  scripts/synth_case01.tcl
652c1f1f25be0e0996b841ba371fef5bb667d1609eb92c8e4691c9df4a63bf89  config/f1.cfg
7dcf3b5c721b181bf5376ce5f07f72c38abfa2fd0ec2761a819bb8680bbf1829  config/f1.sha256
```

- `rtl/dot4sat.v` 的 sha256 `422ba000…` 与 `evidence/F0_v1.1_synth_recipe.md` 里的证据快照相同。
- **grader 版本说明**：`BASE_RUN` 和校准会话是在 grader 的最终评审修正之前跑的，它们冻结的 `scripts/grade.py` 是 `2fc3af26a4f7db0636a91c5f58794025008d9d34006ae5816fe9b407f2f63538`；`F1_RUN` 用的是修正之后的 `116b7ce4…`。修正没有改动 STA 模型文件、网表和综合配方：Step 5 已经核对 `F1_RUN` 与校准会话的网表、最差 slack、模型指纹逐项相同（见上面 9 行）。

### Step 6 附录扫描

- 命令：`python3 scripts/grade.py --impl config/impl.base.cfg --sceneset all`，退出码 0，`GRADE OK`。
- **扫描运行 `RUN_ID` = `20261009-092902-base-T27.91`**。`sceneset` = all，`sta_results.tsv` 里绑定了 16 个 scene（std 六个点加 sweep 组 10 个点），网表 sha256 与 `F1_RUN` 相同。
- 它只用于附录里 sweep 组的 10 个点；主体结论只用 std 六个点（spec 4.4）。

## 9. 一条真实的输入到寄存器路径报告

- 文件：`f1_run_cat_ss_n40C_1v60_in2reg_max.rpt`，复制自 `F1_RUN` 的 `sta/cat_ss_n40C_1v60_in2reg_max.rpt`；`ss_n40C_1v60` 就是 `F1_RUN` 的最差 setup corner。sha256 `043e50bf6638284a043aec4cdf9a23ea999878a369ac58cfef7b613420f38d88`，与校准试探 #1 的同名报告逐字节相同（`cmp` 通过）。
- 起点是 `in_b[2] (input port clocked by clk)`，是一个非时钟的数据输入端口，不是 `clk`。报告里这一行带 slew 和 cap：Fanout 19，Cap 0.0415，Slew 0.4338，Delay 0.3091，Time 5.8911（输入外部延迟 5.5820，即 0.2T）。
- 终点 `_12026_`（`sky130_fd_sc_hd__dfxtp_1` 的 D 引脚），data arrival time 31.5439，data required time 27.3541，slack -4.1897（VIOLATED）。

## 10. 约束展开记录

- `expanded.sdc`（sha256 `c4e85ff0401eb803d131bd88ef02ea917cc7d2f324bf3376739437f869e5b981`）：`F1_RUN` 里 `sta/expanded.sdc` 的副本，是 OpenSTA `write_sdc` 展开的实际约束。内容：周期 27.9100，`set_clock_transition`、`set_clock_uncertainty`、`set_clock_latency` 都为 0；130 个输入位的 input delay（max 5.5820、min 0.0000），33 个输出位的 output delay（max 5.5820、min 0.0000）；33 个输出位的 `set_load -pin_load 0.0024`；输入由 `sky130_fd_sc_hd__buf_2`（A→X，输入 transition 0）驱动；没有例外约束（展开后只有 `create_clock`、`set_clock_latency`、`set_clock_transition`、`set_clock_uncertainty`、`set_input_delay`、`set_output_delay`、`set_load`、`set_driving_cell` 这几类命令，没有 false path、multicycle 等）。
- `sta_results.tsv`（sha256 `14f4def3616882bd2149d38e3b7e1ebac2145438fffbe08b578f1b857aabd7ca`）：`F1_RUN` 里 `sta/sta_results.tsv` 的副本。其中 `LOAD` 行记录了 33 个输出位各自实际生效的负载（`out_valid`、`out_data[31]`…`out_data[0]`，值都是 2.4000000934092797e-15 F，即 0.0024 pF 在库单位下的值）；`BIND` 行记录六个 scene 各自绑定的 liberty；`TOPO` 行记录路径拓扑（in2reg 130、reg2reg 0、reg2out 33）；`WS`、`CAT` 行是各 corner 的最差 slack 和路径端点。

## 11. 单元测试记录

- `unit_tests.log`（sha256 `8cb04445dffaf72b46b1aa38d208a01fcd7589e637a896c0e5631ac8a0a63c74`）：在 F1 之后的正式代码上，归档之前跑的。
  - `cd ref && python3 -B -m unittest test_model test_timeline test_gen_vectors`：`Ran 21 tests`、`OK`；
  - `cd scripts && python3 -B -m unittest test_check_sim test_logcheck test_extract_cload test_calibrate test_grade`：`Ran 86 tests`、`OK`；
  - 两个退出码为 `0 0`，日志里 `warning` 的计数为 0。
- 日志中间有若干行 `OK: … vectors, expected_checked=…` 和一行 `FAIL: need 1 <= L <= lmax <= 3, got L=3 lmax=2`，它们是 `test_gen_vectors` 里被测脚本自己打印的输出（含一个故意构造的错误输入），不是测试失败；测试结果以 `Ran … tests` 和 `OK` 为准。

## 12. 其他说明和已知局限

- **`runs/stafaults-20261009-063436/normal/out/sta_check.json` 不是正例的结果**：它是被"周期"和"C_load"两个反例故意改成无效的（C_load 为 0.003，文件里 `valid` 为 false，每个输出位都报 `ext pin cap 2.4000000934092797e-15/2.4000000934092797e-15 F != 0.003 pF`），不能当作 `normal` 正例的核对结果引用。
- **dcalc 报告里的 "Library:" 一行不能作为 scene 绑定的证据，本证据不引用它。** scene 绑定以 `sta_results.tsv` 的 `BIND` 行为准，核对器 `check_sta.py` 会核对每个 corner 恰好绑定 `-liberty sky130_fd_sc_hd__<corner>`。
- **已知局限**：`scripts/sta_run.tcl` 假定第一个寄存器有 `CLK` 引脚，所以基于锁存器的候选会在 STA 这一步失败（失败方向是安全的：这样的候选得不到有效结果，而不是得到错误结果）。这个局限只记录，F1 之前没有改动 `sta_run.tcl`，因为它是校准模型指纹的一部分。
- **每个步骤的墙钟上限（`STEP_TIMEOUT_S`）和候选 RTL 的 lint 规则都属于冻结的评估规则**，随 `scripts/grade.py` 一起冻结。`STEP_TIMEOUT_S`（秒）：`env_snapshot` 600、`versions` 120、`gen_vectors` 600、`rtl_compile` 600、`rtl_sim` 1800、`synth` 3600、`gl_compile` 600、`gl_sim` 3600、`sta` 3600、`check_sta` 600。lint 规则：候选 RTL 里不允许出现文件读写、`$value$plusargs`、`$test$plusargs`、波形转储（`$dumpfile` 等）、`$system`、include 指令和宏记号拼接（两个连续的反引号）；注释先去掉再匹配，完整的系统任务名单见 `scripts/grade.py` 的 `LINT_SYSTF`。
- **未经审阅的 Warning 会使该次运行无效，不能事后补进白名单（spec 6）。** 候选触发的任何这类 Warning（例如用数组时 Yosys 的 "Replacing memory"）都按此处理；白名单只能由作者在 F1 之前批准，F1 之后改白名单就是评估修订。Error 和 Fatal 一律无效。

## 13. 归档（Step 8）

用于结论的运行目录完整复制到 `evidence/F1/archive/`（排除可以重新生成的 `*.vvp`），清单 `evidence/F1/archive/SHA256SUMS` 由 `find` 加 `sha256sum` 生成。归档的目录（都是 `runs/` 下的目录）：

| 目录 | 用途 |
|---|---|
| `20261009-073842-base-T20` | `BASE_RUN`：Task 10 的基线 T0 = 20 ns 运行 |
| `20261009-080227-calib-20261009-073842-base-T20` | Task 11 的校准会话（含试探 01_T27.91） |
| `20261009-092809-selftest-lmax3` | `FINAL_SELFTEST`：F1 的正式自检 |
| `20261009-092827-base-T27.91` | `F1_RUN`：F1 之后的基线参考运行 |
| `20261009-092902-base-T27.91` | Step 6 的附录扫描运行（`--sceneset all`） |
| `stafaults-20261009-063424`、`stafaults-20261009-063436` | Task 8 的 STA 故障注入目录 |
| `fixture-synth-20261009-063412` | Task 8 的夹具网表目录（故障注入用的两份网表） |
| `20261009-064746-pipe2-T20` | 被 `evidence/whitelist_approval.md` 引用的触发运行 |
| `20261009-062337-selftest-lmax3`、`20261009-062415-selftest-lmax3` | Task 5–6 的两次自检 |
| `20261009-071818-pipe2-T20`、`20261009-073247-pipe2-T20` | grader 的夹具运行 |
| `20261009-091106-pipe2-T20`、`20261009-091047-selftest-lmax3` | v2.5 终审修正后的夹具运行和自检（第一份带工具和文件来源记录的 `selftest.json`） |

执行时 `runs/` 下一共 15 个目录，全部在上表中，没有另外的失败运行目录。冻结的 `inputs/` 文件是只读的，归档里保持只读。

- 归档结果：`evidence/F1/archive/` 共 1903 个文件（另有 `SHA256SUMS` 一个），大小约 25 MB（`du -sh`）；源目录里有 72 个 `*.vvp` 被排除，其余 1903 个文件都已复制，`sha256sum -c SHA256SUMS` 全部通过。
- `SHA256SUMS` 的 sha256：`3166178a88ffb5071ff943854ee81b64a71eebe52c47062e6f39bb4e16e1464c`。
- git 里只纳入 `README.md`、小文件和 `SHA256SUMS`；归档里的大文件是否纳入 git，由作者决定，目前未纳入。

## 14. 本目录的文件

| 文件 | 说明 |
|---|---|
| `README.md` | 本文件 |
| `cload_recheck.json` | 第 5 节，C_load 复核 |
| `calib_record.md`、`calib_record.json` | 第 4 节，校准记录副本 |
| `selftest.json` | 第 7 节，`FINAL_SELFTEST` 的副本 |
| `f1_run_verdict.json` | 第 8 节，`F1_RUN` 的 `verdict.json` 副本 |
| `f1_run_cat_ss_n40C_1v60_in2reg_max.rpt` | 第 9 节，输入到寄存器路径报告（`F1_RUN`） |
| `base_run_T20_cat_ss_n40C_1v60_in2reg_max.rpt`、`calib_trial01_T27.91_cat_ss_n40C_1v60_in2reg_max.rpt` | 第 4 节，T0 和选定 T 下的最差路径报告 |
| `expanded.sdc`、`sta_results.tsv` | 第 10 节，约束展开记录（`F1_RUN`） |
| `unit_tests.log` | 第 11 节，单元测试记录 |
| `archive/` | 第 13 节，归档的运行目录和 `SHA256SUMS` |
