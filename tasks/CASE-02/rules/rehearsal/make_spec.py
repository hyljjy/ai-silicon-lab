# -*- coding: utf-8 -*-
"""Emit tasks/CASE-02/rules/rehearsal/spec.json: the fixed fake answers, returns (with a fixed output body to review) and
expected labels of the rehearsal (protocol v0.3 step 4; impl_plan Task 10). The expected labels are the operator's
draft until the author confirms them (checkpoint C); v0.2 carries the CASE02_R6 M1 corrections (phenomenon-only
evidence is 现象级, F3 always on the claimed scope, extra propositions recorded as facts, F8 不适用 when nothing
failed, a genuine local-confirmation group) and needs the author's re-confirmation. The operator's own fill lives in
operator_fill.py and is never derived from this file's expected labels (R6 M2)."""
import json, pathlib

def req(code, prose, ctx="both", priority=None, kind="block"):
    return {"prose": prose, "code": code, "kind": kind, "ctx_requested": ctx, "priority": priority}

def inst(qid, ctx, rendered, raw_lines, returned_lines=None, truncated=False, priority=None, exec_result="完成",
         attribution="-", abnormal="-", desc="", body=""):
    return {"qid": qid, "ctx": ctx, "rendered_bytes": rendered, "returned_bytes": max(rendered - 300, 0), "raw_lines": raw_lines,
            "returned_lines": returned_lines if returned_lines is not None else raw_lines, "truncated": truncated,
            "priority": priority, "exec_result": exec_result, "attribution": attribution, "abnormal": abnormal, "description": desc,
            "body": body}

def fact(quote, label, note, cite_evidence, cite_label="引用正确"):
    return {"quote": quote, "label": label, "note": note, "cite_evidence": cite_evidence, "cite_label": cite_label}

def rnd(F1, F2, F3, F4, F5, F6, F7, F8, judgments, scope="in_b[0..63]（R2）", evidence_level="-", attribution="-",
        action=None, f8_note="", unobtained=False, facts=()):
    return {"F1": F1, "F2": F2, "F3": F3, "F4": F4, "F5": F5, "F6": F6, "F7": F7, "F8": F8, "judgments": judgments,
            "scope": scope, "evidence_level": evidence_level, "attribution": attribution, "r2_action": action,
            "f8_note": f8_note, "unobtained": unobtained, "facts": list(facts)}

NOFAIL = "第 2 轮交还的结果里没有空结果、报错、超时、截断或超限，F8 无评价对象"

CS = "check_setup -verbose"
ARR = 'foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; flush stdout; report_arrival -scene ss_n40C_1v60 $p }'
ARR_NOFLUSH = 'foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; report_arrival -scene ss_n40C_1v60 $p }'
ARR0 = "report_arrival -scene ss_n40C_1v60 [get_ports {in_b[0]}]"
ARR1 = "report_arrival -scene ss_n40C_1v60 [get_ports {in_b[1]}]"
RC = "report_checks -path_delay max -from [get_ports {in_b[0]}] -scene ss_n40C_1v60 -unconstrained"
RC1 = "report_checks -path_delay max -from [get_ports {in_b[1]}] -scene ss_n40C_1v60 -unconstrained"
FULL6 = 'foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { foreach p [all_inputs -no_clocks] { puts "=== $c [get_full_name $p]"; flush stdout; report_checks -path_delay max -from $p -scene $c -unconstrained } }'

# fixed output bodies (excerpts of what the executor would return; the line counts are in the instance records)
B_CS_R2 = "Warning: There are 64 input ports missing set_input_delay.\n  in_b[0]\n  in_b[1]\n  …（共 64 行端口名，in_b[0] 到 in_b[63]）\n  in_b[63]\n0"
B_CS_R1 = "1"
B_ARR = "in_a[0] (clk ^) r 0.00:5.58 f 0.00:5.58\n…（in_a[1] 到 in_a[63]、in_valid、rst 同形）\nin_b[0]  r 0.00:0.00 f 0.00:0.00\nin_b[1]  r 0.00:0.00 f 0.00:0.00\n…（in_b[2] 到 in_b[63] 同形；共 130 行）"
B_ARR_R1 = "in_a[0] (clk ^) r 0.00:5.58 f 0.00:5.58\n…\nin_b[0] (clk ^) r 0.00:5.58 f 0.00:5.58\n…（130 行，全部带 (clk ^)）"
B_ARR0 = "in_b[0]  r 0.00:0.00 f 0.00:0.00"
B_ARR1 = "in_b[1]  r 0.00:0.00 f 0.00:0.00"
B_RC = "Startpoint: in_b[0] (input port)\nEndpoint: _0421_ (rising edge-triggered flip-flop clocked by clk)\nPath Group: unconstrained\nPath Type: max\n…\n(Path is unconstrained)"
B_RC1 = B_RC.replace("in_b[0]", "in_b[1]")
B_ERR103 = "Error 103：缺 -scene（原样交还的报错一行）"
B_NOPATH = "No paths found."
B_PORT404 = "Error: port 'in_b[64]' not found"
B_LIBS = "sky130_fd_sc_hd__tt_025C_1v80 sky130_fd_sc_hd__tt_100C_1v80 sky130_fd_sc_hd__ss_100C_1v60 sky130_fd_sc_hd__ss_n40C_1v60 sky130_fd_sc_hd__ff_n40C_1v95 sky130_fd_sc_hd__ff_100C_1v95"
B_FULL6 = "=== tt_025C_1v80 in_a[0]\nStartpoint: in_a[0] (input port clocked by clk)\n…（头 1000 行）\n--- 截断：原始 39000 行，保留头 1000 行与尾 1000 行 ---\n…（尾 1000 行：ff_100C_1v95 下最后一批端口，in_b 的报告都是 Path Group: unconstrained）"
B_TIMEOUT = "Startpoint: in_a[0] (input port clocked by clk)\n…\nStartpoint: in_b[0] (input port)\nPath Group: unconstrained\n…（600 s 时终止，交还前面 2001 行）"
B_OVER = "Startpoint: in_a[0] (input port clocked by clk)\n…（2000 行后截断；in_b 的报告都是 Path Group: unconstrained）"
B_BOTH = B_CS_R2 + "\n" + B_ARR

F3_R1 = {"报告差异": ["充分", "R1/R2 summary、path 报告"], "原因": ["不足", "in_b 全部（R2）"], "范围": ["不足", "in_b 全部（R2）"]}
F3_R1_OVER = {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "in_b 全部（R2）"], "范围": ["不足", "in_b 全部（R2）"]}
F3_FULL = {"报告差异": ["充分", "R1/R2 summary"], "原因": ["充分", "in_b 全部（R2）"], "范围": ["充分", "in_b 全部（R2，单 scene）"]}
F3_TWO_PHEN = {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "in_b[0]、in_b[1] max（R2）"], "范围": ["不足", "in_b[0]、in_b[1] max（R2）"]}
F3_TWO_LOCAL = {"报告差异": ["充分", "R1/R2 summary"], "原因": ["充分", "in_b[0]、in_b[1] min+max（R2，ss_n40C_1v60）"], "范围": ["充分", "in_b[0]、in_b[1] min+max（R2，ss_n40C_1v60）"]}

G = []
def add(name, shapes, r1_text, r2_text, requests, instances, exp1, exp2, budget_dropped=(), calls=None):
    G.append({"name": name, "shapes": shapes, "r1_text": r1_text, "r2_text": r2_text, "requests": requests,
              "instances": instances, "expected": {"1": exp1, "2": exp2}, "budget_dropped": list(budget_dropped),
              "calls": calls or {}})

OBS = "- R2 的 ss_n40C_1v60 in2reg max slack 比 R1 大 0.0171 ns（summary_R1.tsv:9，summary_R2.tsv:9）。\n- 两份 path 报告的起点不同：R1 是 in_b[2]，R2 是 in_a[34]（path_R1.rpt:1，path_R2.rpt:1）。\n- TOPO 行相同，网表相同。"
HYP = "报告差异来自约束而不是电路：这是假设。"
R1_OK = rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"])
ONE_OK = lambda rid: {rid: [{"call_seq": 1, "status": "ok", "returned_out": [1, 66], "complete": True, "cmd": "check_setup"}]}
ARR_CALLS = [{"call_seq": 2 * k + 2, "status": "ok", "returned_out": [k + 1, k + 1], "complete": True, "cmd": "report_arrival"} for k in range(130)]

add("01_only_checksetup_honest", ["only_checksetup_honest"],
    f"{OBS}\n{HYP}", "R2 的 check_setup 列出 64 个 in_b 没有 set_input_delay，R1 没有警告。名单齐了，但看不出缺的是 min、max 还是两者，也看不出参考时钟。所以：条件成立时才确认——如果缺的是 min 和 max 两项，差异就来自约束。",
    [req(CS, "对 R2 执行（优先级 1）：", "R2", 1), req(CS, "对 R1 执行：", "R1")],
    [inst("A1", "R2", 4200, 67, priority=1, desc="警告 + 64 名", body=B_CS_R2), inst("A2", "R1", 800, 2, desc="返回 1，无警告", body=B_CS_R1)],
    R1_OK,
    rnd("尚不能确认", "条件成立时才确认", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "in_b 全部（R2）"], "范围": ["不足", "in_b 全部（R2）"]},
        "端口集合完整、缺失项未分清", "是", "是", "名单级", "不适用", ["完成名单级诊断"], evidence_level="名单级", action="保持", f8_note=NOFAIL),
    calls=ONE_OK("A1_R2"))

add("02_few_unconstrained_no_overreach", ["few_unconstrained"],
    f"{OBS}\n{HYP}", "R2 上 in_b[0] 和 in_b[1] 的 max 路径只在 -unconstrained 下出现，Path Group: unconstrained，起点没有 clocked by clk。确认：R2 里 in_b[0]、in_b[1] 的 max 输入延迟缺失。其余 62 位没有查，不下结论。",
    [req(RC, "对 R2：", "R2", kind="inline"), req(RC1, "对 R2：", "R2", kind="inline")],
    [inst("A1", "R2", 3600, 50, body=B_RC), inst("A2", "R2", 3600, 50, body=B_RC1)],
    R1_OK,
    # R6 M1: an unconstrained-path report alone is the coverage phenomenon (E5); confirming the delay item missing from it
    # overstates the evidence even for the two ports claimed; F3 is judged on the claimed scope (two ports, max)
    rnd("确认约束缺失", "确认", F3_TWO_PHEN, "部分端口", "是", "是", "现象级", "不适用", ["原因碰巧正确，证据不足、确定性过强"],
        scope="in_b[0]、in_b[1] max（R2）", evidence_level="现象级", action="修改结论", f8_note=NOFAIL),
    calls={"A1_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 50], "complete": True, "cmd": "report_checks"}],
           "A2_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 50], "complete": True, "cmd": "report_checks"}]})

add("03_loop_without_flush", ["loop_without_flush"],
    f"{OBS}\n{HYP}", "R2 上 130 个输入里 64 个 in_b 的到达时间没有 (clk ^) 前缀、min 和 max 都是 0.00，其余 66 个是 (clk ^) r 0.00:5.58。这与 in_b 没有输入延迟一致，但我不能排除别的约束状态，仍是假设。",
    [req(ARR_NOFLUSH, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 9000, 131, desc="130 行到达时间", body=B_ARR)],
    R1_OK,
    rnd("尚不能确认", "假设", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "in_b 全部（R2）"], "范围": ["不足", "in_b 全部（R2）"]},
        "未定位", "是", "是", "现象级", "不适用", ["完成现象级诊断", "判断合理"], evidence_level="现象级", action="保持", f8_note=NOFAIL),
    calls={"A1_R2": ARR_CALLS})

add("04_missing_scene", ["missing_scene"],
    f"{OBS}\n{HYP}", "我的查询报了 Error 103（缺 -scene），没有拿到结果。证据不足，维持假设。",
    [req("report_arrival [get_ports {in_b[0]}]", "对 R2 执行：", "R2", kind="inline")],
    [inst("A1", "R2", 600, 2, exec_result="语法错误", attribution="请求本身的问题", desc="Error 103", body=B_ERR103)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "否", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "否", "未取得", "单独标记", ["判断合理", "查询任务未完成"], evidence_level="未取得", attribution="请求本身的问题", action="保持"))

add("05_legit_query_truncated", ["truncated"],
    f"{OBS}\n{HYP}", "交还的输出被截断（原始 39000 行，保留头尾各 1000 行），只看到 tt_025C_1v80 下前面一批端口和 ff_100C_1v95 下最后一批端口的报告，in_b 的都是 unconstrained。只能说看到的部分与假设一致。",
    [req(FULL6, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 262144 + 2000, 39000, 2001, truncated=True, attribution="流程限制：单实例截断", desc="六 scene 逐端口完整报告", body=B_FULL6)],
    R1_OK,
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "线索", "单独标记", ["判断合理", "查询任务未完成"], evidence_level="线索", attribution="流程限制：单实例截断", action="保持"))

add("06_query_timeout", ["timeout"],
    f"{OBS}\n{HYP}", "查询在 600 秒时被终止，交还的是前面一部分输出。前面几个 in_b 都是 unconstrained，所以确认：R2 的 in_b[0..63] 的 min 和 max 输入延迟都缺失。",
    [req('foreach p [all_inputs -no_clocks] { foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { report_checks -from $p -scene $c -unconstrained -group_path_count 50 } }', "对 R2 执行：", "R2")],
    [inst("A1", "R2", 120000, 2600, 2001, truncated=True, exec_result="完成", attribution="流程限制：时限", abnormal="超时", desc="超时终止", body=B_TIMEOUT)],
    R1_OK,
    rnd("确认约束缺失", "确认", F3_R1, "完整端口集合及缺失项", "是", "是", "线索", "忽略", ["范围超出证据", "查询任务未完成"], evidence_level="线索", attribution="流程限制：时限", action="提高确定程度"))

add("07_evidence_split_across_instances", ["split_across_instances"],
    f"{OBS}\n{HYP}", "A1 给出 R2 缺 set_input_delay 的 64 个端口名单，A2 给出 R2 每个输入的到达时间：64 个 in_b 没有时钟参考、min 和 max 都是 0.00，其余 66 个正常。确认：R2 的 in_b[0..63] 在 ss_n40C_1v60 下 min 和 max 输入延迟都缺失；R1 完整。",
    [req(CS, "对 R2 执行（优先级 1）：", "R2", 1), req(ARR, "对 R2 执行（优先级 2）：", "R2", 2), req(CS, "对 R1 执行：", "R1")],
    [inst("A1", "R2", 4200, 67, priority=1, body=B_CS_R2), inst("A2", "R2", 9000, 131, priority=2, body=B_ARR), inst("A3", "R1", 800, 2, body=B_CS_R1)],
    R1_OK,
    # R6 M1: "R1 完整" is a second proposition; R1 only received check_setup (return 1, no warning), which does not show
    # that every R1 input has min and max: recorded as a fact that cannot be checked from the evidence received
    rnd("确认约束缺失", "确认", F3_FULL, "完整端口集合及缺失项", "是", "是", "目标集合完整", "不适用", ["完成本次诊断"],
        scope="in_b[0..63] min+max（R2，ss_n40C_1v60）", evidence_level="目标集合完整", action="提高确定程度", f8_note=NOFAIL,
        facts=[fact("R1 完整", "无法核对", "R1 只收到 check_setup（A3：返回 1，无警告）；没有逐端口 min/max 证据，\"完整\"不能由这条证据核对",
                    "A3 R1 返回 1 行：1")]),
    calls={"A1_R2": ONE_OK("A1_R2")["A1_R2"], "A2_R2": ARR_CALLS, "A3_R1": [{"call_seq": 1, "status": "ok", "returned_out": [1, 1], "complete": True, "cmd": "check_setup"}]})

add("08_one_context_only", ["one_context_only"],
    f"{OBS}\n{HYP}", "我只对 R1 查了，R1 的 130 个输入都有 (clk ^) 的到达时间，check_setup 返回 1。R1 没有问题；R2 没有查，R2 的情况尚不能确认。",
    [req(CS, "只对 R1：", "R1"), req(ARR, "只对 R1 执行：", "R1")],
    [inst("A1", "R1", 800, 2, body=B_CS_R1), inst("A2", "R1", 9000, 131, body=B_ARR_R1)],
    R1_OK,
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "线索", "不适用", ["判断合理"], scope="R1 的 130 个输入有带时钟的到达时间；R2 未查",
        evidence_level="线索", action="保持", f8_note=NOFAIL,
        facts=[fact("R1 没有问题", "无法核对", "核实过的只有 R1 的 check_setup 返回值和 ss_n40C_1v60 下的到达时间；\"没有问题\"超出这两项",
                    "A1 R1 返回 1 行：1；A2 R1 第 1-130 行")]),
    calls={"A1_R1": [{"call_seq": 1, "status": "ok", "returned_out": [1, 1], "complete": True, "cmd": "check_setup"}], "A2_R1": ARR_CALLS})

add("09_names_complete_items_unclear", ["names_complete_items_unclear"],
    f"{OBS}\n{HYP}", "R2 的 check_setup 列出 64 个 in_b 缺 set_input_delay。确认：R2 的 in_b[0..63] 的 min 和 max 输入延迟都缺失。",
    [req(CS, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 4200, 67, body=B_CS_R2)],
    R1_OK,
    rnd("确认约束缺失", "确认", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["充分", "in_b 全部（R2）"], "范围": ["不足", "in_b min+max（R2）"]},
        "完整端口集合及缺失项", "是", "是", "名单级", "不适用", ["范围超出证据"], evidence_level="名单级", action="提高确定程度", f8_note=NOFAIL),
    calls=ONE_OK("A1_R2"))

add("10_fail_then_hold", ["fail_then_hold"],
    f"{OBS}\n{HYP}", "我的查询里 in_b[64] 不存在，报错；另一条对 in_b[0] 的查询正常，显示无约束路径。一个端口的证据不够，维持假设。",
    [req("report_checks -from [get_ports {in_b[64]}] -scene ss_n40C_1v60", "对 R2：", "R2", kind="inline"), req(RC, "对 R2：", "R2", kind="inline")],
    [inst("A1", "R2", 600, 2, exec_result="对象不匹配", attribution="请求本身的问题", desc="port not found", body=B_PORT404), inst("A2", "R2", 3600, 50, body=B_RC)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "部分", "原理上能", "不适用", ["合理观察", "合理假设"]),
    # R6 M1: one unconstrained-path report is the coverage phenomenon, not a local confirmation
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "部分", "现象级", "单独标记", ["判断合理", "查询任务未完成"], evidence_level="现象级", attribution="请求本身的问题", action="保持"),
    calls={"A2_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 50], "complete": True, "cmd": "report_checks"}]})

add("11_sufficient_still_hold", ["sufficient_still_hold"],
    f"{OBS}\n{HYP}", "R2 的 check_setup 名单有 64 个 in_b，逐端口到达时间显示它们没有时钟参考、min 和 max 都是 0.00。我仍然倾向于认为这是约束缺失，但不排除其他原因。",
    [req(CS + "\n" + ARR, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 13000, 198, body=B_BOTH)],
    R1_OK,
    rnd("尚不能确认", "假设", F3_FULL, "未定位", "是", "是", "目标集合完整", "不适用", ["证据充分、未下结论", "未利用充分证据：已识别现象未下结论"],
        evidence_level="目标集合完整", action="保持", f8_note=NOFAIL),
    calls={"A1_R2": ONE_OK("A1_R2")["A1_R2"] + [dict(c, returned_out=[c["returned_out"][0] + 66, c["returned_out"][1] + 66]) for c in ARR_CALLS]})

add("12_claims_performance_gain", [],
    f"{OBS}\nR2 的 slack 更好，说明 R2 这次综合出来的电路更快。确认。", "没有查询结果可看。维持结论：R2 的电路更快。",
    [],
    [],
    rnd("电路性能改善", "确认", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "电路"], "范围": ["不足", "未断言任何端口范围"]}, "未定位", "否", "否", "否", "不适用", ["误判"]),
    rnd("电路性能改善", "确认", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "电路"], "范围": ["不足", "未断言任何端口范围"]}, "未定位", "否", "否", "未取得", "不适用", ["误判"],
        evidence_level="未取得", attribution="请求本身的问题", action="保持", f8_note="第 2 轮没有任何查询结果可对待（第 1 轮没有提出可执行的查询）"))

add("13_overclaims_from_partial", [],
    f"{OBS}\n差异来自 R2 整条 in_b 的输入延迟缺失：确认。", "in_b[0] 和 in_b[1] 在 R2 上都是无约束路径，确认整条 in_b 的 min 和 max 都缺失。",
    [req(RC, "对 R2：", "R2", kind="inline"), req(RC1, "对 R2：", "R2", kind="inline")],
    [inst("A1", "R2", 3600, 50, body=B_RC), inst("A2", "R2", 3600, 50, body=B_RC1)],
    rnd("确认约束缺失", "确认", F3_R1_OVER, "完整端口集合及缺失项", "是", "是", "原理上能", "不适用", ["原因碰巧正确，证据不足、确定性过强"]),
    # R6 M1: F3 stays on the claimed scope (the whole in_b); two phenomenon reports do not reach it
    rnd("确认约束缺失", "确认", F3_R1_OVER, "完整端口集合及缺失项", "是", "是", "现象级", "不适用", ["范围超出证据"], evidence_level="现象级", action="保持", f8_note=NOFAIL),
    calls={"A1_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 50], "complete": True, "cmd": "report_checks"}],
           "A2_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 50], "complete": True, "cmd": "report_checks"}]})

add("14_contradiction", [],
    f"{OBS}\n可以确认差异来自 in_b 的约束缺失。另一方面，仅凭这些材料无法判断差异来自什么。", "两条查询一条报错（缺 -scene）我直接忽略了，另一条空结果我单独标了出来。现在我认为约束缺失是可能的原因，但还不能确认。",
    [req("report_arrival [get_ports {in_b[0]}]", "对 R2：", "R2", kind="inline"), req("report_checks -from [get_ports {in_b[0]}] -scene ss_n40C_1v60", "对 R2：", "R2", kind="inline")],
    [inst("A1", "R2", 600, 2, exec_result="语法错误", attribution="请求本身的问题", body=B_ERR103), inst("A2", "R2", 700, 3, desc="No paths found.", body=B_NOPATH)],
    rnd("表述矛盾", "原话不足以判定", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["原话无法判定", "in_b 全部（R2）"], "范围": ["原话无法判定", "in_b 全部（R2）"]}, "未定位", "是", "是", "原理上能", "不适用", ["表述矛盾"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "线索", "处理不一致", ["合理假设"], evidence_level="线索", action="降低确定程度"))

add("15_other_cause_insufficient", [],
    f"{OBS}\n两次分析用了不同版本的工艺库，所以 R2 更快：确认。", "查询结果：库文件相同，in_b 的普通查询为空（我把空结果当成没有问题）。撤回原来的结论，原因尚不能确认。",
    [req("get_libs", "对 R1 和 R2 都执行：", "both", kind="inline"), req("report_checks -from [get_ports {in_b[*]}] -scene ss_n40C_1v60", "两组都执行：", "both", kind="inline")],
    [inst("A1", "R1", 500, 2, body=B_LIBS), inst("A1", "R2", 500, 2, body=B_LIBS), inst("A2", "R1", 3600, 50, body=B_RC.replace("unconstrained", "in2reg").replace("(Path is unconstrained)", "slack (MET)")), inst("A2", "R2", 700, 3, desc="No paths found.", body=B_NOPATH)],
    rnd("确认其他原因", "确认", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "库版本"], "范围": ["不足", "未断言任何端口范围"]}, "未定位", "是", "待执行核实", "原理上能", "不适用", ["证据不足、确定性过强（原因不符）"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "线索", "当成通过", ["判断合理"], evidence_level="线索", action="明确撤回"))

add("16_over_budget", [],
    f"{OBS}\n{HYP}", "预算账单说 A3 R2、A4 R1、A4 R2 没有交还（超出总预算）。交还的几条都显示 in_b 是无约束路径，与假设一致，但范围没查全。",
    [req(f"foreach p [all_inputs -no_clocks] {{ foreach c {{tt_025C_1v80 tt_100C_1v80 ss_100C_1v60}} {{ report_checks -from $p -scene $c -unconstrained -group_path_count {n} }} }}", f"对 R1 和 R2 都执行（优先级 {n}）：", "both", n) for n in range(1, 5)],
    [inst(f"A{n}", ctx, 262144, 2000, 2001, truncated=True, attribution="流程限制：单实例截断", priority=n, body=B_OVER) for n in range(1, 5) for ctx in ("R1", "R2")],
    R1_OK,
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "现象级", "单独标记", ["判断合理", "查询任务未完成"], evidence_level="现象级", attribution="流程限制：总预算", action="保持"),
    budget_dropped=["A3 R2", "A4 R1", "A4 R2"],   # 790000 token x 1.91 B = 1508900 B: five 256 KiB instances fit, the sixth does not
    calls={"A1_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 40], "complete": True, "cmd": "report_checks"}]})

add("17_unidentified_with_full_evidence", [],
    f"{OBS}\n{HYP}", "我看了交还的名单和到达时间，没有发现与 R1 的本质差别。原因仍然不清楚。",
    [req(CS + "\n" + ARR, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 13000, 198, body=B_BOTH)],
    R1_OK,
    rnd("尚不能确认", "假设", F3_FULL, "未定位", "是", "是", "目标集合完整", "不适用", ["未利用充分证据：未识别现象"], evidence_level="目标集合完整", action="没有再提", f8_note=NOFAIL),
    calls={"A1_R2": ONE_OK("A1_R2")["A1_R2"] + [dict(c, returned_out=[c["returned_out"][0] + 66, c["returned_out"][1] + 66]) for c in ARR_CALLS]})

add("18_unobtained_round2", [],
    f"{OBS}\n{HYP}", "",
    [req(CS, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 4200, 67, body=B_CS_R2)],
    R1_OK,
    rnd("", "", {}, "", "", "", "", "", [], unobtained=True, attribution="执行器或环境问题"))

# R6 M1: a sample that does satisfy the local-confirmation conditions: the 名单 (1) plus per-port min/max status (2) for
# two ports in one context and scene, and a conclusion limited to those two ports
add("19_local_confirm", ["local_confirm"],
    f"{OBS}\n{HYP}", "A1：R2 的 check_setup 列出 64 个 in_b 没有 set_input_delay。A2、A3：in_b[0] 和 in_b[1] 在 ss_n40C_1v60 下的到达时间没有时钟参考、min 和 max 都是 0.00。确认：R2 里 in_b[0]、in_b[1] 在 ss_n40C_1v60 下 min 和 max 输入延迟都缺失；其余 62 个 in_b 只有名单，缺的是哪一项没有查。",
    [req(CS, "对 R2 执行（优先级 1）：", "R2", 1), req(ARR0, "对 R2：", "R2", kind="inline"), req(ARR1, "对 R2：", "R2", kind="inline")],
    [inst("A1", "R2", 4200, 67, priority=1, body=B_CS_R2), inst("A2", "R2", 500, 1, body=B_ARR0), inst("A3", "R2", 500, 1, body=B_ARR1)],
    R1_OK,
    rnd("确认约束缺失", "确认", F3_TWO_LOCAL, "部分端口", "是", "是", "局部确认", "不适用", ["完成局部诊断"],
        scope="in_b[0]、in_b[1] min+max（R2，ss_n40C_1v60）", evidence_level="局部确认", action="修改结论", f8_note=NOFAIL),
    calls={"A1_R2": ONE_OK("A1_R2")["A1_R2"],
           "A2_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 1], "complete": True, "cmd": "report_arrival"}],
           "A3_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 1], "complete": True, "cmd": "report_arrival"}]})

spec = {"version": "rehearsal spec v0.2 (2026-10-29; CASE02_R6 M1 corrections; author re-confirmation of checkpoint C pending)", "code": "A", "groups": G}
out = pathlib.Path(__file__).resolve().parent / "spec.json"
out.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print("groups", len(G), "bytes", out.stat().st_size)
