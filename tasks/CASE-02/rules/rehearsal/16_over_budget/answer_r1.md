一、观察
- R2 的 ss_n40C_1v60 in2reg max slack 比 R1 大 0.0171 ns（summary_R1.tsv:9，summary_R2.tsv:9）。
- 两份 path 报告的起点不同：R1 是 in_b[2]，R2 是 in_a[34]（path_R1.rpt:1，path_R2.rpt:1）。
- TOPO 行相同，网表相同。

二、结论和确定程度
报告差异来自约束而不是电路：这是假设。

三、证据
- summary 与 path 报告的差异；有效约束清单尚未提供。

四、检查请求
1. 对 R1 和 R2 都执行（优先级 1）：
```tcl
foreach p [all_inputs -no_clocks] { foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60} { report_checks -from $p -scene $c -unconstrained -group_path_count 1 } }
```
2. 对 R1 和 R2 都执行（优先级 2）：
```tcl
foreach p [all_inputs -no_clocks] { foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60} { report_checks -from $p -scene $c -unconstrained -group_path_count 2 } }
```
3. 对 R1 和 R2 都执行（优先级 3）：
```tcl
foreach p [all_inputs -no_clocks] { foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60} { report_checks -from $p -scene $c -unconstrained -group_path_count 3 } }
```
4. 对 R1 和 R2 都执行（优先级 4）：
```tcl
foreach p [all_inputs -no_clocks] { foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60} { report_checks -from $p -scene $c -unconstrained -group_path_count 4 } }
```
