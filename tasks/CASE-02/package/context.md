## 1. 接口

模块名 `dot4sat`。单时钟，只在 `clk` 上升沿动作。

| 端口 | 方向 | 位宽 | 说明 |
|---|---|---|---|
| `clk` | 入 | 1 | |
| `rst` | 入 | 1 | 同步复位，高有效 |
| `in_valid` | 入 | 1 | |
| `in_a`、`in_b` | 入 | 64 | 第 i 路（i = 0..3）为 `in_a[16*i +: 16]`、`in_b[16*i +: 16]`，各自按 16 位二进制补码解释 |
| `out_valid` | 出 | 1 | |
| `out_data` | 出 | 32 | 32 位二进制补码 |

## 2. 两次分析记录的共同条件

- 两次分析记录（R1、R2）用同一份综合网表（sha256 `1fa89c975162f4f1f9a2f349bed73b4dae5f53ab921883be842cb0a37763a8d1`）、同一个工具版本（OpenSTA 3.1.0）、同一套工艺库（Sky130 HD，`sky130_fd_sc_hd`）、同一个六点集合（`tt_025C_1v80`、`tt_100C_1v80`、`ss_100C_1v60`、`ss_n40C_1v60`、`ff_n40C_1v95`、`ff_100C_1v95`）和同一组报告生成命令。
- 分析模型：综合后分析；理想时钟（时钟延迟、uncertainty、transition 都为 0）；不读取寄生参数，连线负载只计引脚电容；数据和控制输入由 `sky130_fd_sc_hd__buf_2`（A→X）驱动，输入 transition 为 0。
- OpenSTA 3.1.0 用 scene 组织 corner：`report_checks`、`find_timing_paths` 用 `-scenes` 选择场景（缩写 `-scene` 也可以用）；`report_wns`、`report_tns`、`report_worst_slack` 没有选择场景的选项。报告生成命令里的变量已展开。
- `summary_R1.tsv`、`summary_R2.tsv`：每次记录的 `WS`（六点 setup/hold 最差 slack）、`CAT`（按路径类别的最差路径：slack、起点、终点）、`TOPO`（按类别的结构路径数）三类行，列说明：`WS <scene> <max|min> <slack>`；`CAT <scene> <类别> <max|min> <slack> <起点> <终点>`；`TOPO <类别> <数量>`。
- `path_R1.rpt`、`path_R2.rpt`：两次记录的详细路径报告都来自 `ss_n40C_1v60` 下"输入到寄存器"这一类的 setup 路径，是下面这条命令的输出（按默认设置只报告 slack 最差的一条）；它可能不是各自的全局最差点，各组的全局最差点在 summary 里：
  `report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4`
- `intent.md` 是接口时序的意图说明（要求），`values.txt` 是 T 和 C_load 的取值，`dot4sat.v` 是模块的 RTL 原文。
- **两次记录各自实际生效的约束清单和覆盖检查结果尚未提供**，可以在"检查请求"里要求。
- 时钟周期 T 的来历：T 是按"基线最差 setup slack 约为周期的 −15%"校准得到的固定值。

## 查询的执行契约

你在"检查请求"里写的每条 OpenSTA 查询，会由一个固定的执行器按下面的规则执行。规则对参与的每个模型相同，运行开始后不放宽也不收紧。

### 可用命令

查询在一个受限的 Tcl 解释器里运行，只有下面三张表里的命令可用（还有 Tcl 的基本控制结构：`foreach`、`if`、`set`、`puts`、`llength`、`lindex`、`string`、`expr`、`catch`、`flush` 等）。不能读写文件，不能启动外部进程，不能把输出重定向到文件。

只读查询命令（按原文顺序）：`report_annotated_check`、`report_annotated_delay`、`report_arrival`、`report_check_types`、`report_checks`、`report_clock_latency`、`report_clock_min_period`、`report_clock_properties`、`report_clock_skew`、`report_constant`、`report_dcalc`、`report_disabled_edges`、`report_edges`、`report_instance`、`report_lib_cell`、`report_net`、`report_object_full_names`、`report_object_names`、`report_parasitic_annotation`、`report_path`、`report_required`、`report_slack`、`report_slew`、`report_slews`、`report_tns`、`report_units`、`report_wns`、`report_worst_slack`、`check_setup`、`find_timing_paths`、`get_cell`、`get_cells`、`get_clock`、`get_clocks`、`get_fanin`、`get_fanout`、`get_full_name`、`get_lib`、`get_lib_cell`、`get_lib_cells`、`get_lib_pin`、`get_lib_pins`、`get_libs`、`get_modes`、`get_name`、`get_net`、`get_nets`、`get_pin`、`get_pins`、`get_port`、`get_ports`、`get_property`、`get_scenes`、`get_timing_edges`、`all_clocks`、`all_inputs`、`all_outputs`、`all_registers`、`total_negative_slack`、`worst_clock_skew`、`worst_negative_slack`、`worst_slack`。

改变分析模型的命令（约束、分析条件、单位、场景、网表）：`connect_pin`、`create_clock`、`create_generated_clock`、`create_voltage_area`、`delete_clock`、`delete_generated_clock`、`delete_instance`、`delete_net`、`disconnect_pin`、`make_instance`、`make_net`、`make_port`、`replace_cell`、`set_assigned_check`、`set_assigned_delay`、`set_assigned_transition`、`set_case_analysis`、`set_clock_gating_check`、`set_clock_groups`、`set_clock_latency`、`set_clock_sense`、`set_clock_transition`、`set_clock_uncertainty`、`set_cmd_units`、`set_data_check`、`set_delay_calculator`、`set_disable_clock_gating_check`、`set_disable_inferred_clock_gating`、`set_disable_timing`、`set_drive`、`set_driving_cell`、`set_false_path`、`set_fanout_load`、`set_hierarchy_separator`、`set_ideal_latency`、`set_ideal_network`、`set_ideal_transition`、`set_input_delay`、`set_input_transition`、`set_level_shifter_strategy`、`set_level_shifter_threshold`、`set_load`、`set_logic_dc`、`set_logic_one`、`set_logic_zero`、`set_max_area`、`set_max_capacitance`、`set_max_delay`、`set_max_dynamic_power`、`set_max_fanout`、`set_max_leakage_power`、`set_max_time_borrow`、`set_max_transition`、`set_min_capacitance`、`set_min_delay`、`set_min_pulse_width`、`set_mode`、`set_multicycle_path`、`set_operating_conditions`、`set_output_delay`、`set_path_margin`、`set_port_fanout_number`、`set_power_activity`、`set_propagated_clock`、`set_property`、`set_pvt`、`set_resistance`、`set_scene`、`set_sense`、`set_timing_derate`、`set_units`、`set_voltage`、`set_wire_load_min_block_size`、`set_wire_load_mode`、`set_wire_load_model`、`set_wire_load_selection_group`、`unset_case_analysis`、`unset_clock_groups`、`unset_clock_latency`、`unset_clock_transition`、`unset_clock_uncertainty`、`unset_data_check`、`unset_disable_clock_gating_check`、`unset_disable_inferred_clock_gating`、`unset_disable_timing`、`unset_input_delay`、`unset_output_delay`、`unset_path_exceptions`、`unset_power_activity`、`unset_propagated_clock`、`unset_timing_derate`。含这些命令的查询在单独的对照实例里执行，结果会标注"改变模型的对照"；它可以支持或反对一个假设，但不能用来证实关于原始分析模型的事实。

建环境命令（分析环境已经由记录提供，调用时跳过并回显一行说明）：`create_clock`、`define_corners`、`define_scene`、`link_design`、`read_liberty`、`read_power_activities`、`read_saif`、`read_sdc`、`read_sdf`、`read_spef`、`read_vcd`、`read_verilog`、`sky130_define_scenes`、`sky130_read_libs`。其中 `create_clock` 的周期等于记录里的 T 时按建环境命令跳过，周期是其他值时按改变模型的命令处理。

### 多场景的写法

分析里有六个 scene。`report_arrival`、`report_required`、`report_slack` 在多 scene 下必须带 `-scene <名字>`；不带时工具会报 `Error 103`，这个错误会原样交还给你，执行器不替你改写。`report_checks`、`find_timing_paths` 接受 `-scene` 或 `-scenes`。

### 输出顺序

执行器在每条命令执行前后自动 `flush` 标准输出，所以循环里 `puts` 的文字和紧随其后的报告输出会按你写的顺序出现，你不需要自己处理。

### 实例、行数和字节上限

每条查询对每一份分析记录各执行一次，称为一个实例：你写明只对 R1 或只对 R2 执行的，有 1 个实例；没写明的，有 2 个实例（R1、R2 各一个，结果分别标注）。每个模型最多 12 条检查请求；第 13 条起不执行。

每个实例交还给你的输出最多 2000 行（含命令回显行），同时最多 256 KiB（按交还文字的 UTF-8 字节计）。超过时保留开头和结尾各一半，中间用一行 `[已截断：省略 N 行；原始 M 行 B 字节；见执行契约]` 代替，省略的行数相对原始输出计。计数的例外：截断标记那一行和下面说的单行截断后缀不计入上面的行数和字节数（所以被截断的实例交还 2001 行）；单独一行超过 256 KiB 时，这一行先缩短到 128 KiB 并在行尾加 `…[本行截断]` 标记，再按上面的规则处理。原始输出会完整保存，但不交还。

下面这些形态的查询（编号 W01–W08）保证不会被截断：
- W01：check_setup 带端口名单；
- W02：单 scene 对全部非时钟输入逐端口 report_arrival 的循环；
- W03：单 scene 对全部非时钟输入逐端口 find_timing_paths 计数（max/min，带与不带 -unconstrained）的循环；
- W04：W01 与 W02 放在同一实例；
- W05：六个 scene 的 W02 与 W03 放在同一实例；
- W06：默认路径数的一条 report_checks；
- W07：单 scene 的 report_check_types -verbose；
- W08：六个 scene 的 worst_slack 与 total_negative_slack（max 与 min）；

下面这些形态不保证不被截断（按实测会超出上面的上限）：
- 逐端口完整 report_checks 报告乘以多端口（单 scene 全部输入约 6500 行，六个 scene 约 39000 行）；
- -group_path_count 或 -endpoint_path_count 不小于 40 的报告；
- 跨多个 scene 的完整报告枚举；

### 总预算

一个模型的全部实例加起来交还给你的文字有总预算：790000 token（按保守换算，每 token 约 1.91 字节）。超过时按下面的顺序保留，排在后面的实例整个不交还：你在检查请求里声明的优先级在前；没有声明的按请求编号顺序；同一条请求 R1 先于 R2。第 2 轮题目末尾固定附一张预算账单，写明总预算、每个已交还实例占用的行数和是否截断、每个未交还实例的原始行数和被排到后面所依据的规则。未交还不等于查询失败。

### 时间和其他上限

每个实例里查询部分的时限 600 秒，整个工具进程 1200 秒；进程输出超过 50 MiB 时终止；工具进程的内存上限 8 GiB（超过时工具进程自行退出）；受限解释器最多执行 1000000 条 Tcl 命令。因超时或超限终止的实例，交还的是终止前已经产生的输出，末尾附一行说明。

### 交还的内容

每个实例交还：你的原始查询、实际执行的查询（只有预先登记的两条机械改写规则可能改动它，改动会注明）、输出、一个固定的结果代码。第 2 轮里新提出的查询会被记录，但不执行。
