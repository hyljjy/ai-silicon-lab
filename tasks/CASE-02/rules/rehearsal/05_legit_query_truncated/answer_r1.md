一、观察
- R2 的 ss_n40C_1v60 in2reg max slack 比 R1 大 0.0171 ns（summary_R1.tsv:9，summary_R2.tsv:9）。
- 两份 path 报告的起点不同：R1 是 in_b[2]，R2 是 in_a[34]（path_R1.rpt:1，path_R2.rpt:1）。
- TOPO 行相同，网表相同。

二、结论和确定程度
报告差异来自约束而不是电路：这是假设。

三、证据
- summary 与 path 报告的差异；有效约束清单尚未提供。

四、检查请求
1. 对 R2 执行：
```tcl
foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { foreach p [all_inputs -no_clocks] { puts "=== $c [get_full_name $p]"; flush stdout; report_checks -path_delay max -from $p -scene $c -unconstrained } }
```
