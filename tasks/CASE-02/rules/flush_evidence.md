# 输出刷新边界：为什么 `flush stdout` 之后取 `file size` 能框住一次调用的全部输出（外审 R6 Q1）

问题：`c2_query.tcl` 的 `c2_call` 包装器在每次 STA 调用前后执行 `flush stdout`，然后用 `file size $STA_LOG` 取日志的字节位置，作为这次调用输出的起止。要成立，需要 OpenSTA 的报告文字和 Tcl 的 `puts` 文字都经过同一条、被 `flush` 刷净的通道，而不是另有一条独立的 C 标准库缓冲。

## 固定版本的源码依据

- 二进制：`/home/eda/tools/opensta/bin/sta`，`sta -version` = 3.1.0，sha256 `70a7e86c8b0ce23731fbaffbfa981eee03fab9b62a41cf47444348079f61e447`（2026-10-03 构建）。
- 源码：`/home/eda/src/OpenSTA`，git `7a034b56de14b485ddf8fd97b420a6f37a91c00d`（2026-10-01），`CMakeLists.txt` `project(STA VERSION 3.1.0`。
- `util/ReportTcl.cc`（该提交）：
  - `ReportTcl::setTclInterp`：取 Tcl 的标准通道 `tcl_stdout_ = Tcl_GetStdChannel(TCL_STDOUT)`，再用 `Tcl_StackChannel` 在它上面叠一层封装通道 `tcl_encap_stdout_`。Tcl 脚本里的 `puts` / `flush stdout` 操作的是叠在最上层的封装通道。
  - `ReportTcl::printConsole(buffer, length)` → `printTcl(tcl_stdout_, …)`：取 `tcl_stdout_` 的通道驱动 `outputProc`，**直接**把报告字节交给底层标准输出通道的驱动写出（`Tcl_ChannelOutputProc(ch_type)(clientData, buffer, length, &error_code)`），不经过 Tcl 的通道缓冲，也不经过 C 的 `stdio` 缓冲。OpenSTA 的全部报告输出（`report_*`、`check_setup`、错误和警告）都走 `Report::print*` → `printConsole`。
  - `ReportTcl::flush()`：`Tcl_Flush(tcl_encap_stdout_)`、`Tcl_Flush(tcl_encap_stderr_)`；日志/重定向命令调用它（注释："Tcl_Main can eval multiple commands before the flushing the command output, so the log/redirect commands must force a flush."）。

## 推论与边界

1. 报告字节在 `printConsole` 返回时已经到达文件描述符（底层驱动是 Tcl 的文件通道驱动，`outputProc` 即 `write`）。`puts` 的字节留在封装通道的缓冲里，直到换行刷新策略、缓冲满或 `flush stdout`。所以 `puts -nonewline` 之后紧接报告而不 `flush`，报告会先于 `puts` 的文字出现——这正是验收样例 (ii)（W02 去 `flush`）观察到的乱序形态；包装器在每次调用前后 `flush stdout`，把 `puts` 的缓冲刷到文件之后再取 `file size`，两类字节都已落盘。
2. 不在这条证据覆盖范围内的：OpenSTA 之外的库直接用 C `printf` 写 `stdout` 的路径（本次用到的命令都走 `Report`；没有逐一审计第三方库）；`stderr` 的内容（日志由外壳 `2>&1` 合并，顺序只对各自通道内有保证）。因此本说明的结论是"已用命令的输出路径在该版本下经同一通道、`flush` 后取大小成立"，不是"任何输出都成立"；经验核对是验收样例 (i)(ii)(iii)：逐调用区间与交还文本一一对应（`calls.jsonl` 的 `returned_out`）。
3. 跨调用的 `puts -nonewline`（例如 `puts -nonewline "[get_full_name $p] "` 后接 `report_arrival`）：前缀文字属于上一次 `flush` 之后、本次调用的 START 之前，记在本次调用区间的开头（包装器在 START 前 `flush`，取到的位置包含前缀）；一个证据单元 = 端口前缀 + 该端口的报告行，位于同一调用区间内。
