# 第 2 轮判定

由 `revise/scripts/judge.py run 2` 从 `r2_criteria.jsonl` 生成；原值见 `r2_judgments.jsonl`，数值显示 6 位小数（ROUND_HALF_UP）。"未判定""不适用"的说明由操作者另写 `r2_notes.jsonl`，作者复核。

## 计数

| 候选 | 支持 | 反对 | 未判定 | 无结果 | 不适用 | 格式问题 | 触发 | 未触发 | 失败条件未判定 |
|---|---|---|---|---|---|---|---|---|---|
| cand_u2pe | 9 | 0 | 1 | 0 | 0 | 0 | 0 | 7 | 0 |
| cand_3yvg | 2 | 1 | 0 | 4 | 0 | 0 | 0 | 3 | 3 |
| cand_c1dx | 3 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 4 |

## 预测

| 候选 | prediction_id | id | metric | check | corner | category | value_kind | 实际 | 方向 | 范围 | 判定 | 格式问题 | 说明 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cand_u2pe | cand_u2pe.P1 | P1 | slack | setup | all | global | absolute | 6.104896 | 支持 | 支持 | 支持 |  | 实际值 6.104896；相对 F1 基线的变化 10.294622；方向 改善：支持；范围 [0, 21.7]：支持；点估计 9 不判 |
| cand_u2pe | cand_u2pe.P2 | P2 | slack | setup | all | global | delta | 10.294622 | 支持 | 支持 | 支持 |  | 实际值 10.294622；相对 F1 基线的变化 10.294622；方向 改善：支持；范围 [4.19, 25.9]：支持；点估计 13 不判 |
| cand_u2pe | cand_u2pe.P3 | P3 | slack | setup | ss_n40C_1v60 | reg2reg | absolute | 6.104897 | 不判 | 支持 | 支持 |  | 实际值 6.104897；方向 未知：不判；范围 [0, 未知]：支持；点估计 9 不判 |
| cand_u2pe | cand_u2pe.P4 | P4 | slack | setup | ss_n40C_1v60 | in2reg | absolute | 21.704105 | 支持 | 支持 | 支持 |  | 实际值 21.704105；相对 F1 基线的变化 25.893831；方向 改善：支持；范围 [20.5, 22.5]：支持；点估计 21.4 不判 |
| cand_u2pe | cand_u2pe.P5 | P5 | slack | setup | ss_n40C_1v60 | reg2out | absolute | 21.692432 | 支持 | 支持 | 支持 |  | 实际值 21.692432；相对 F1 基线的变化 0.000000；方向 不变：支持；范围 [21.5, 21.8]：支持；点估计 21.69 不判 |
| cand_u2pe | cand_u2pe.P6 | P6 | area |  |  |  | delta | 3283.148800 | 支持 | 支持 | 支持 |  | 实际值 3283.148800；相对 F1 基线的变化 3283.148800；方向 退化：支持；范围 [2500, 5500]：支持；点估计 3400 不判 |
| cand_u2pe | cand_u2pe.P7 | P7 | area |  |  |  | absolute | 48666.675200 | 支持 | 支持 | 支持 |  | 实际值 48666.675200；相对 F1 基线的变化 3283.148800；方向 退化：支持；范围 [47900, 50900]：支持；点估计 48800 不判 |
| cand_u2pe | cand_u2pe.P8 | P8 | slack | hold | all | global | absolute | 0.023094 | 不判 | 不判 | 未判定 |  | 实际值 0.023094；相对 F1 基线的变化 -0.036019；方向 未知：不判；范围 [未知, 未知]：不判；点估计 未知 不判 |
| cand_u2pe | cand_u2pe.P9 | P9 | L |  |  |  |  | 3 | 不判 | 支持 | 支持 |  | 实际值 3；点 3：支持 |
| cand_u2pe | cand_u2pe.P10 | P10 | function |  |  |  |  | pass | 不判 | 支持 | 支持 |  | 实际值 pass；点 pass：支持 |
| cand_3yvg | cand_3yvg.P1 | P1 | slack | setup | all | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_3yvg | cand_3yvg.P2 | P2 | slack | setup | ss_100C_1v60 | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_3yvg | cand_3yvg.P3 | P3 | slack | setup | all | reg2reg | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_3yvg | cand_3yvg.P4 | P4 | area |  |  |  | delta | 2786.422400 | 支持 | 反对 | 反对 |  | 实际值 2786.422400；相对 F1 基线的变化 2786.422400；方向 退化：支持；范围 [2000, 2600]：反对；点估计 2400 不判 |
| cand_3yvg | cand_3yvg.P5 | P5 | slack | hold | all | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_3yvg | cand_3yvg.P6 | P6 | L |  |  |  |  | 2 | 不判 | 支持 | 支持 |  | 实际值 2；点 2：支持 |
| cand_3yvg | cand_3yvg.P7 | P7 | function |  |  |  |  | pass | 不判 | 支持 | 支持 |  | 实际值 pass；点 pass：支持 |
| cand_c1dx | cand_c1dx.P1 | P1 | slack | setup | all | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_c1dx | cand_c1dx.P2 | P2 | slack | setup | ss_n40C_1v60 | in2reg | delta | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_c1dx | cand_c1dx.P3 | P3 | slack | setup | ss_n40C_1v60 | reg2reg | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_c1dx | cand_c1dx.P4 | P4 | area |  |  |  | absolute | 47983.520000 | 支持 | 支持 | 支持 |  | 实际值 47983.520000；相对 F1 基线的变化 2599.993600；方向 退化：支持；范围 [未知, 56729.408]：支持；点估计 未知 不判 |
| cand_c1dx | cand_c1dx.P5 | P5 | L |  |  |  |  | 2 | 不判 | 支持 | 支持 |  | 实际值 2；点 2：支持 |
| cand_c1dx | cand_c1dx.P6 | P6 | function |  |  |  |  | pass | 不判 | 支持 | 支持 |  | 实际值 pass；点 pass：支持 |
| cand_c1dx | cand_c1dx.P7 | P7 | slack | hold | all | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |

## 失败条件

| 候选 | fc_id | 原文 | 判定 | 证据字段 |
|---|---|---|---|---|
| cand_u2pe | F1 | STA 步骤再次报网表 syntax error 或其他读入错误。这说明 `signed` 声明不是根因，或者不是唯一根因。 | 未触发 | sta_analysis |
| cand_u2pe | F2 | 6 个 std 点中最差的 setup slack < 0。 | 未触发 | cells[ff_100C_1v95,setup,global].cand.slack, cells[ff_n40C_1v95,setup,global].cand.slack, cells[ss_100C_1v60,setup,global].cand.slack, cells[ss_n40C_1v60,setup,global].cand.slack, cells[tt_025C_1v80,setup,global].cand.slack, cells[tt_100C_1v80,setup,global].cand.slack |
| cand_u2pe | F3 | ss_n40C_1v60 下 reg2reg 类最差 setup slack < 0。 | 未触发 | cells[ss_n40C_1v60,setup,reg2reg].cand.slack |
| cand_u2pe | F4 | ss_n40C_1v60 下 in2reg 类最差 setup slack ≤ −4.1897 ns。 | 未触发 | cells[ss_n40C_1v60,setup,in2reg].cand.slack |
| cand_u2pe | F5 | 综合面积 > 56729.408 µm²。 | 未触发 | area_um2 |
| cand_u2pe | F6 | RTL 仿真或门级功能仿真任一失败（function = fail）。 | 未触发 | rtl_sim, gl_sim |
| cand_u2pe | F7 | 候选因 G1–G8 任一规则被拒，没有进入评估。 | 未触发 | state |
| cand_3yvg | F1 | STA 步骤再次因 `synth/netlist.v` 语法错误失败，无有效 slack 结果（说明问题与 RTL 语义无关，且材料不足以定位；第 1 轮评估结果）。 | 未判定 | sta_analysis |
| cand_3yvg | F2 | 6 个 std corner 中最差 setup slack < 0，正式成功标准未满足（`constraints.md:24`）。 | 未判定 | cells[ff_100C_1v95,setup,global].cand.slack, cells[ff_n40C_1v95,setup,global].cand.slack, cells[ss_100C_1v60,setup,global].cand.slack, cells[ss_n40C_1v60,setup,global].cand.slack, cells[tt_025C_1v80,setup,global].cand.slack, cells[tt_100C_1v80,setup,global].cand.slack |
| cand_3yvg | F3 | RTL 仿真或门级功能仿真任一失败，function 判 fail（`constraints.md:75`），特别是 A1 饱和边界或 L=2 valid 对齐出错。 | 未触发 | rtl_sim, gl_sim |
| cand_3yvg | F4 | 综合后面积超过 56729.408 µm²（`constraints.md:19`）。 | 未触发 | area_um2 |
| cand_3yvg | F5 | 因违反 G1–G8 任一条被拒绝评估（`constraints.md:31-40`）。 | 未触发 | state |
| cand_3yvg | F6 | 最差 setup slack 低于约 +0.5 ns，说明"输入寄存 + A1 可收敛"的估计被推翻，应改走 L=3 方案（`阶段A答复.md:539-586`）。 | 未判定 |  |
| cand_c1dx | F1 | 任一 std corner 的全局最差 setup slack < 0（constraints.md:22-24）。 | 未判定 | cells[ff_100C_1v95,setup,global].cand.slack, cells[ff_n40C_1v95,setup,global].cand.slack, cells[ss_100C_1v60,setup,global].cand.slack, cells[ss_n40C_1v60,setup,global].cand.slack, cells[tt_025C_1v80,setup,global].cand.slack, cells[tt_100C_1v80,setup,global].cand.slack |
| cand_c1dx | F2 | 综合后的网表在 STA 读取时再次出现语法错误，导致无法得到有效时序结果。 | 未判定 | sta_analysis |
| cand_c1dx | F3 | 综合后面积 > 56729.408 µm²（constraints.md:19）。 | 未触发 | area_um2 |
| cand_c1dx | F4 | RTL 仿真或门级功能仿真中，任何观测点 `out_valid`/`out_data` 与 L=2 期望不符（contract_excerpt.md:38-39、53）。 | 未判定 |  |
| cand_c1dx | F5 | 实际延迟不是 2，或因配置校验失败使候选被拒（contract_excerpt.md:58-59）。 | 未判定 | cfg_L |
