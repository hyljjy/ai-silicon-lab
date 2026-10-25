GRADE FAIL

grade_status：GRADE FAIL

失败位置：步骤 sta

该位置的日志摘要：

```text
日志检查发现的问题：
sta error: Error: 171 <RUN>/synth/netlist.v line 6052, syntax error

日志末尾摘要（最多 40 个物理行）：
Error: 171 <RUN>/synth/netlist.v line 6052, syntax error
```

已有的结果字段（缺的写 not_available，没执行的写 not_run）：

- rtl_sim：pass（checked=2835）
- gl_sim：pass（checked=2835）
- sta_analysis：fail
- cfg_L：2
- 面积（µm²）：47983.520000
- 是否超过面积上限：否
- 全局最差 setup slack（ns）：not_available
- 全局最差 hold slack（ns）：not_available
- 是否数值上满足 setup_ge_0_std：not_available

6 个 std 点的全局最小 slack（ns）：

not_available

in2reg、reg2reg、reg2out 三类路径在 6 个点的 setup 和 hold slack（ns）及起点、终点（不存在的写 not_applicable）：

not_available

你第 1 轮的候选已经运行评估，但没有得到有效的时序分析结果，情况见上。你可以提交一个修改后的候选（格式同第 1 轮），也可以单独一行写 `NO_SUBMISSION` 并说明理由。
