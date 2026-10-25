# 第 1 轮判定

由 `revise/scripts/judge.py run 1` 从 `r1_criteria.jsonl` 生成；原值见 `r1_judgments.jsonl`，数值显示 6 位小数（ROUND_HALF_UP）。"未判定""不适用"的说明由操作者另写 `r1_notes.jsonl`，作者复核。

## 计数

| 候选 | 支持 | 反对 | 未判定 | 无结果 | 不适用 | 格式问题 | 触发 | 未触发 | 失败条件未判定 |
|---|---|---|---|---|---|---|---|---|---|
| cand_9pbi | 2 | 2 | 0 | 6 | 0 | 0 | 0 | 3 | 4 |
| cand_983p | 3 | 0 | 0 | 4 | 0 | 0 | 0 | 3 | 2 |
| cand_wpml | 3 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 3 |

## 预测

| 候选 | prediction_id | id | metric | check | corner | category | value_kind | 实际 | 方向 | 范围 | 判定 | 格式问题 | 说明 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cand_9pbi | cand_9pbi.P1 | P1 | slack | setup | all | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_9pbi | cand_9pbi.P2 | P2 | slack | setup | all | global | delta | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_9pbi | cand_9pbi.P3 | P3 | slack | setup | ss_n40C_1v60 | reg2reg | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_9pbi | cand_9pbi.P4 | P4 | slack | setup | ss_n40C_1v60 | in2reg | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_9pbi | cand_9pbi.P5 | P5 | slack | setup | ss_n40C_1v60 | reg2out | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_9pbi | cand_9pbi.P6 | P6 | area |  |  |  | delta | 3407.017600 | 支持 | 反对 | 反对 |  | 实际值 3407.017600；相对 F1 基线的变化 3407.017600；方向 退化：支持；范围 [4000, 11345.9]：反对；点估计 5200 不判 |
| cand_9pbi | cand_9pbi.P7 | P7 | area |  |  |  | absolute | 48790.544000 | 支持 | 反对 | 反对 |  | 实际值 48790.544000；相对 F1 基线的变化 3407.017600；方向 退化：支持；范围 [49383, 56729.408]：反对；点估计 50600 不判 |
| cand_9pbi | cand_9pbi.P8 | P8 | slack | hold | all | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_9pbi | cand_9pbi.P9 | P9 | L |  |  |  |  | 3 | 不判 | 支持 | 支持 |  | 实际值 3；点 3：支持 |
| cand_9pbi | cand_9pbi.P10 | P10 | function |  |  |  |  | pass | 不判 | 支持 | 支持 |  | 实际值 pass；点 pass：支持 |
| cand_983p | cand_983p.P1 | P1 | slack | setup | all | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_983p | cand_983p.P2 | P2 | slack | setup | ss_100C_1v60 | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_983p | cand_983p.P3 | P3 | slack | setup | all | reg2reg | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_983p | cand_983p.P4 | P4 | area |  |  |  | delta | 2599.993600 | 支持 | 不判 | 支持 |  | 实际值 2599.993600；相对 F1 基线的变化 2599.993600；方向 退化：支持；范围 [未知, 未知]：不判；点估计 未知 不判 |
| cand_983p | cand_983p.P5 | P5 | slack | hold | all | reg2reg | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_983p | cand_983p.P6 | P6 | L |  |  |  |  | 2 | 不判 | 支持 | 支持 |  | 实际值 2；点 2：支持 |
| cand_983p | cand_983p.P7 | P7 | function |  |  |  |  | pass | 不判 | 支持 | 支持 |  | 实际值 pass；点 pass：支持 |
| cand_wpml | cand_wpml.P1 | P1 | slack | setup | all | global | absolute | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_wpml | cand_wpml.P2 | P2 | slack | setup | ss_n40C_1v60 | in2reg | delta | no_result | 不判 | 不判 | 无结果 |  | 所需字段没有有效结果（未执行、不可用或不确定） |
| cand_wpml | cand_wpml.P3 | P3 | area |  |  |  | absolute | 46336.940800 | 支持 | 支持 | 支持 |  | 实际值 46336.940800；相对 F1 基线的变化 953.414400；方向 退化：支持；范围 [未知, 56729.408]：支持；点估计 未知 不判 |
| cand_wpml | cand_wpml.P4 | P4 | L |  |  |  |  | 2 | 不判 | 支持 | 支持 |  | 实际值 2；点 2：支持 |
| cand_wpml | cand_wpml.P5 | P5 | function |  |  |  |  | pass | 不判 | 支持 | 支持 |  | 实际值 pass；点 pass：支持 |

## 失败条件

| 候选 | fc_id | 原文 | 判定 | 证据字段 |
|---|---|---|---|---|
| cand_9pbi | F1 | 6 个 std 点中最差的 setup slack（WS max 的最小值）< 0。 | 未判定 | cells[ff_100C_1v95,setup,global].cand.slack, cells[ff_n40C_1v95,setup,global].cand.slack, cells[ss_100C_1v60,setup,global].cand.slack, cells[ss_n40C_1v60,setup,global].cand.slack, cells[tt_025C_1v80,setup,global].cand.slack, cells[tt_100C_1v80,setup,global].cand.slack |
| cand_9pbi | F2 | ss_n40C_1v60 下 reg2reg 类最差 setup slack < 0。这说明单个乘法器或四数相加加饱和一级仍然超过一个周期。 | 未判定 | cells[ss_n40C_1v60,setup,reg2reg].cand.slack |
| cand_9pbi | F3 | ss_n40C_1v60 下 in2reg 类最差 setup slack 没有高于基线的 −4.1897 ns。 | 未判定 | cells[ss_n40C_1v60,setup,in2reg].cand.slack |
| cand_9pbi | F4 | 综合面积 > 56729.408 µm²。 | 未触发 | area_um2 |
| cand_9pbi | F5 | RTL 仿真或门级功能仿真任一失败（function = fail）。 | 未触发 | rtl_sim, gl_sim |
| cand_9pbi | F6 | 评估按 L = 3 比对时，出现 valid 错位、丢失、重复，或者 valid 为 1 时 `out_data` 与参考值不等。 | 未判定 | cfg_L |
| cand_9pbi | F7 | 候选因 G1–G8 任一规则被拒，没有进入评估。 | 未触发 | state |
| cand_983p | F1 | 6 个 std corner 中最差 setup slack < 0，即正式成功标准未满足（`constraints.md:24`）。 | 未判定 | cells[ff_100C_1v95,setup,global].cand.slack, cells[ff_n40C_1v95,setup,global].cand.slack, cells[ss_100C_1v60,setup,global].cand.slack, cells[ss_n40C_1v60,setup,global].cand.slack, cells[tt_025C_1v80,setup,global].cand.slack, cells[tt_100C_1v80,setup,global].cand.slack |
| cand_983p | F2 | RTL 仿真或门级功能仿真任一失败（valid 对齐、复位边界、饱和数值任一不符），function 判为 fail（`constraints.md:75`）。 | 未触发 | rtl_sim, gl_sim |
| cand_983p | F3 | 综合后面积超过 56729.408 µm²（`constraints.md:19`）。 | 未触发 | area_um2 |
| cand_983p | F4 | 因违反 G1–G8 中任一条（端口集合、单模块、无 parameter/宏、事件控制形式、clk 用法、DECLARED_L 范围）被拒绝评估（`constraints.md:31-40`）。 | 未触发 | state |
| cand_983p | F5 | 最差 setup slack 改善量明显小于 P1 的下端（例如仍低于 −1 ns），说明"输入寄存即可收敛"的一阶估计被推翻（`阶段A答复.md:119-122`）。 | 未判定 | cells[ff_100C_1v95,setup,global].cand.slack, cells[ff_n40C_1v95,setup,global].cand.slack, cells[ss_100C_1v60,setup,global].cand.slack, cells[ss_n40C_1v60,setup,global].cand.slack, cells[tt_025C_1v80,setup,global].cand.slack, cells[tt_100C_1v80,setup,global].cand.slack |
| cand_wpml | F1 | 任一 std corner 的最差 setup WS < 0（constraints.md:22-24）。 | 未判定 | cells[ff_100C_1v95,setup,global].cand.slack, cells[ff_n40C_1v95,setup,global].cand.slack, cells[ss_100C_1v60,setup,global].cand.slack, cells[ss_n40C_1v60,setup,global].cand.slack, cells[tt_025C_1v80,setup,global].cand.slack, cells[tt_100C_1v80,setup,global].cand.slack |
| cand_wpml | F2 | 综合后面积 > 56729.408 µm²（constraints.md:19）。 | 未触发 | area_um2 |
| cand_wpml | F3 | RTL 仿真或门级功能仿真中，任何观测点 `out_valid`/`out_data` 与 L=2 期望不符（contract_excerpt.md:38-39、53）。 | 未判定 |  |
| cand_wpml | F4 | 实际延迟不是 2，或因配置校验失败使候选被拒（contract_excerpt.md:58-59；constraints.md:44、46）。 | 未判定 | cfg_L |
