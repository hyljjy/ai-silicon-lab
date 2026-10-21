GRADE OK

结果字段（缺的写 not_available，没执行的写 not_run）：

- rtl_sim：{rtl_sim}
- gl_sim：{gl_sim}
- sta_analysis：{sta_analysis}
- cfg_L：{cfg_L}
- 面积（µm²）：{area_um2}
- 是否超过面积上限：{over_cap}
- 全局最差 setup slack（ns）：{worst_setup}
- 全局最差 hold slack（ns）：{worst_hold}
- 是否数值上满足 setup_ge_0_std：{numeric_target_met}

6 个 std 点的全局最小 slack（ns）：

{global_table}

in2reg、reg2reg、reg2out 三类路径在 6 个点的 setup 和 hold slack（ns）及起点、终点（不存在的写 not_applicable）：

{category_table}
