"""The CASE-02 query execution contract (protocol v0.3 section 6.4): the single source of the per-instance caps,
time limits, total budget, keep order and guaranteed workloads (rules/contract.json), the truncation applied to
every instance's returned output, the mapping from raw output ranges to returned ranges, and the neutral contract
section of package/context.md that all three models receive."""
import json
import os
from dataclasses import dataclass, field


class ContractError(ValueError):
    pass


@dataclass
class Contract:
    per_instance_max_lines: int
    per_instance_max_bytes: int
    truncation: dict
    query_seconds: int
    process_seconds: int
    process_max_bytes: int
    tcl_command_limit: int
    max_requests: int
    instances_per_request: dict
    max_logical_instances: int
    max_executions: int
    total_budget_tokens: object
    token_bytes_ratio: object
    budget_table: object
    keep_order: list
    shell_limits: dict
    guaranteed_workloads: list = field(default_factory=list)
    not_guaranteed: list = field(default_factory=list)
    version: str = ""
    process_max_memory_bytes: int = 8 * 1024 ** 3

    @property
    def budget_ready(self):
        return isinstance(self.total_budget_tokens, int) and self.total_budget_tokens > 0 \
            and isinstance(self.token_bytes_ratio, (int, float)) and self.token_bytes_ratio > 0


def from_dict(d):
    keys = {f for f in Contract.__dataclass_fields__}
    return Contract(**{k: v for k, v in d.items() if k in keys})


def load(path):
    with open(path, encoding="utf-8") as f:
        return from_dict(json.load(f))


BEGIN_MARK = "QUERY BEGIN"
END_MARK = "QUERY END"


def count(norm_lines):
    """Content lines of a normalized query output: the BEGIN and END marker lines are not counted, command echoes
    are (stage-A split_log counting rule)."""
    return sum(1 for l in norm_lines if not (BEGIN_MARK in l and l.startswith("===")) and
               not (END_MARK in l and l.startswith("===")))


def _nbytes(line):
    return len(line.encode("utf-8")) + 1


def _cut_utf8(line, limit):
    b = line.encode("utf-8")[:limit]
    return b.decode("utf-8", errors="ignore")


def truncate(norm_lines, c):
    """Head/tail truncation of one instance's output (protocol 6.4 (a), (g)). Returns a dict:
    returned_lines, truncated, omitted_lines, raw_lines, raw_bytes, returned_bytes, marker_index, cut_by."""
    tr = c.truncation
    raw_lines = len(norm_lines)
    raw_bytes = sum(_nbytes(l) for l in norm_lines)
    lines = list(norm_lines)
    long_cut = False
    for i, l in enumerate(lines):
        if _nbytes(l) - 1 > c.per_instance_max_bytes:
            lines[i] = _cut_utf8(l, tr["long_line_bytes"]) + tr["long_line_marker"]
            long_cut = True
    over_lines = raw_lines > c.per_instance_max_lines
    over_bytes = sum(_nbytes(l) for l in lines) > c.per_instance_max_bytes
    if not over_lines and not over_bytes:
        return {"returned_lines": lines, "truncated": long_cut, "omitted_lines": 0, "raw_lines": raw_lines,
                "raw_bytes": raw_bytes, "returned_bytes": sum(_nbytes(l) for l in lines), "marker_index": None,
                "cut_by": "bytes" if long_cut else None}
    k = min(tr["head_lines"], raw_lines // 2)
    while k > 0 and sum(_nbytes(l) for l in lines[:k]) + sum(_nbytes(l) for l in lines[raw_lines - k:]) > c.per_instance_max_bytes:
        k -= 1
    head, tail = lines[:k], lines[raw_lines - k:] if k else []
    omitted = raw_lines - 2 * k
    marker = tr["marker"].format(omitted=omitted, raw_lines=raw_lines, raw_bytes=raw_bytes)
    returned = head + [marker] + tail
    return {"returned_lines": returned, "truncated": True, "omitted_lines": omitted, "raw_lines": raw_lines,
            "raw_bytes": raw_bytes, "returned_bytes": sum(_nbytes(l) for l in head + tail), "marker_index": k,
            "cut_by": "lines" if over_lines else "bytes"}


def map_range(t, raw_range):
    """Map a half-open [start, end) line range of the raw (normalized) output to the returned output; None when the
    range crosses or lies inside the omitted middle."""
    s, e = raw_range
    k = t["marker_index"]
    if k is None:
        return (s, e)
    n = t["raw_lines"]
    tail_start = n - k
    if e <= k:
        return (s, e)
    if s >= tail_start:
        return (s - tail_start + k + 1, e - tail_start + k + 1)
    return None


def workloads(c):
    return [dict(w) for w in c.guaranteed_workloads]


def _words(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def render_context_section(c, allow_query_path, allow_whatif_path, setup_path):
    """The '查询的执行契约' section of context.md: neutral, identical for all three models, no diagnostic hints.
    Refuses to render before the total budget is filled in (Task 6)."""
    if not c.budget_ready:
        raise ContractError("contract.json has no total budget yet; context.md cannot be rendered")
    kib = c.per_instance_max_bytes // 1024
    mib = c.process_max_bytes // (1024 * 1024)
    unspecified = c.instances_per_request["unspecified"]
    L = []
    a = L.append
    a("## 查询的执行契约")
    a("")
    a("你在\"检查请求\"里写的每条 OpenSTA 查询，会由一个固定的执行器按下面的规则执行。规则对参与的每个模型相同，运行开始后不放宽也不收紧。")
    a("")
    a("### 可用命令")
    a("")
    a("查询在一个受限的 Tcl 解释器里运行，只有下面三张表里的命令可用（还有 Tcl 的基本控制结构：`foreach`、`if`、`set`、`puts`、`llength`、`lindex`、`string`、`expr`、`catch`、`flush` 等）。不能读写文件，不能启动外部进程，不能把输出重定向到文件。")
    a("")
    a("只读查询命令（按原文顺序）：" + "、".join("`" + w + "`" for w in _words(allow_query_path)) + "。")
    a("")
    a("改变分析模型的命令（约束、分析条件、单位、场景、网表）：" + "、".join("`" + w + "`" for w in _words(allow_whatif_path))
      + "。含这些命令的查询在单独的对照实例里执行，结果会标注\"改变模型的对照\"；它可以支持或反对一个假设，但不能用来证实关于原始分析模型的事实。")
    a("")
    a("建环境命令（分析环境已经由记录提供，调用时跳过并回显一行说明）：" + "、".join("`" + w + "`" for w in _words(setup_path))
      + "。其中 `create_clock` 的周期等于记录里的 T 时按建环境命令跳过，周期是其他值时按改变模型的命令处理。")
    a("")
    a("### 多场景的写法")
    a("")
    a("分析里有六个 scene。`report_arrival`、`report_required`、`report_slack` 在多 scene 下必须带 `-scene <名字>`；不带时工具会报 `Error 103`，这个错误会原样交还给你，执行器不替你改写。`report_checks`、`find_timing_paths` 接受 `-scene` 或 `-scenes`。")
    a("")
    a("### 输出顺序")
    a("")
    a("执行器在每条命令执行前后自动 `flush` 标准输出，所以循环里 `puts` 的文字和紧随其后的报告输出会按你写的顺序出现，你不需要自己处理。")
    a("")
    a("### 实例、行数和字节上限")
    a("")
    a(f"每条查询对每一份分析记录各执行一次，称为一个实例：你写明只对 R1 或只对 R2 执行的，有 1 个实例；没写明的，有 {unspecified} 个实例（R1、R2 各一个，结果分别标注）。每个模型最多 {c.max_requests} 条检查请求；第 {c.max_requests + 1} 条起不执行。")
    a("")
    a(f"每个实例交还给你的输出最多 {c.per_instance_max_lines} 行（含命令回显行），同时最多 {kib} KiB。超过时保留开头和结尾各一半，中间用一行 `[已截断：省略 N 行；原始 M 行 B 字节；见执行契约]` 代替，省略的行数相对原始输出计。原始输出会完整保存，但不交还。")
    a("")
    a("下面这些形态的查询保证不会被截断：")
    for w in c.guaranteed_workloads:
        a(f"- {w['description']}；")
    a("")
    a("下面这些形态会超过上限、被截断：")
    for s in c.not_guaranteed:
        a(f"- {s}；")
    a("")
    a("### 总预算")
    a("")
    a(f"一个模型的全部实例加起来交还给你的文字有总预算：{c.total_budget_tokens} token（按保守换算，每 token 约 {c.token_bytes_ratio} 字节）。"
      f"超过时按下面的顺序保留，排在后面的实例整个不交还：你在检查请求里声明的优先级在前；没有声明的按请求编号顺序；同一条请求 R1 先于 R2。"
      f"第 2 轮题目末尾固定附一张预算账单，写明总预算、每个已交还实例占用的行数和是否截断、每个未交还实例的原始行数和被排到后面所依据的规则。未交还不等于查询失败。")
    a("")
    a("### 时间和其他上限")
    a("")
    gib = c.process_max_memory_bytes // (1024 ** 3)
    a(f"每个实例里查询部分的时限 {c.query_seconds} 秒，整个工具进程 {c.process_seconds} 秒；进程输出超过 {mib} MiB 时终止；工具进程的内存上限 {gib} GiB（超过时工具进程自行退出）；受限解释器最多执行 {c.tcl_command_limit} 条 Tcl 命令。"
      f"因超时或超限终止的实例，交还的是终止前已经产生的输出，末尾附一行说明。")
    a("")
    a("### 交还的内容")
    a("")
    a("每个实例交还：你的原始查询、实际执行的查询（只有预先登记的两条机械改写规则可能改动它，改动会注明）、输出、一个固定的结果代码。第 2 轮里新提出的查询会被记录，但不执行。")
    return "\n".join(L) + "\n"
