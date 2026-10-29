# -*- coding: utf-8 -*-
"""Emit tasks/CASE-02/rules/rehearsal/spec.json: the fixed fake answers, returns and expected labels of the rehearsal
(protocol v0.3 step 4; impl_plan Task 10). The expected labels are the operator's draft until the author confirms
them (checkpoint C); rehearse.py compares the operator's claims rows with expected.tsv cell by cell."""
import json, pathlib

def req(code, prose, ctx="both", priority=None, kind="block"):
    return {"prose": prose, "code": code, "kind": kind, "ctx_requested": ctx, "priority": priority}

def inst(qid, ctx, rendered, raw_lines, returned_lines=None, truncated=False, priority=None, exec_result="完成",
         attribution="-", abnormal="-", desc=""):
    return {"qid": qid, "ctx": ctx, "rendered_bytes": rendered, "returned_bytes": max(rendered - 300, 0), "raw_lines": raw_lines,
            "returned_lines": returned_lines if returned_lines is not None else raw_lines, "truncated": truncated,
            "priority": priority, "exec_result": exec_result, "attribution": attribution, "abnormal": abnormal, "description": desc}

def rnd(F1, F2, F3, F4, F5, F6, F7, F8, judgments, scope="in_b[0..63]（R2）", evidence_level="-", attribution="-",
        action=None, f8_note="", unobtained=False):
    return {"F1": F1, "F2": F2, "F3": F3, "F4": F4, "F5": F5, "F6": F6, "F7": F7, "F8": F8, "judgments": judgments,
            "scope": scope, "evidence_level": evidence_level, "attribution": attribution, "r2_action": action,
            "f8_note": f8_note, "unobtained": unobtained}

CS = "check_setup -verbose"
ARR = 'foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; flush stdout; report_arrival -scene ss_n40C_1v60 $p }'
ARR_NOFLUSH = 'foreach p [all_inputs -no_clocks] { puts -nonewline "[get_full_name $p] "; report_arrival -scene ss_n40C_1v60 $p }'
RC = "report_checks -path_delay max -from [get_ports {in_b[0]}] -scene ss_n40C_1v60 -unconstrained"
RC1 = "report_checks -path_delay max -from [get_ports {in_b[1]}] -scene ss_n40C_1v60 -unconstrained"
FULL6 = 'foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { foreach p [all_inputs -no_clocks] { puts "=== $c [get_full_name $p]"; flush stdout; report_checks -path_delay max -from $p -scene $c -unconstrained } }'
F3_R1 = {"报告差异": ["充分", "R1/R2 summary、path 报告"], "原因": ["不足", "in_b 全部（R2）"], "范围": ["不足", "in_b 全部（R2）"]}
F3_R1_OVER = {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "in_b 全部（R2）"], "范围": ["不足", "in_b 全部（R2）"]}
F3_FULL = {"报告差异": ["充分", "R1/R2 summary"], "原因": ["充分", "in_b 全部（R2）"], "范围": ["充分", "in_b 全部（R2，单 scene）"]}
F3_PART = {"报告差异": ["充分", "R1/R2 summary"], "原因": ["充分", "in_b[0]、in_b[1]（R2）"], "范围": ["不足", "in_b 全部（R2）"]}

G = []
def add(name, shapes, r1_text, r2_text, requests, instances, exp1, exp2, budget_dropped=(), calls=None, evidence=None):
    G.append({"name": name, "shapes": shapes, "r1_text": r1_text, "r2_text": r2_text, "requests": requests,
              "instances": instances, "expected": {"1": exp1, "2": exp2}, "budget_dropped": list(budget_dropped),
              "calls": calls or {}, "evidence": evidence or []})

OBS = "- R2 的 ss_n40C_1v60 in2reg max slack 比 R1 大 0.0171 ns（summary_R1.tsv:9，summary_R2.tsv:9）。\n- 两份 path 报告的起点不同：R1 是 in_b[2]，R2 是 in_a[34]（path_R1.rpt:1，path_R2.rpt:1）。\n- TOPO 行相同，网表相同。"
HYP = "报告差异来自约束而不是电路：这是假设。"

add("01_only_checksetup_honest", ["only_checksetup_honest"],
    f"{OBS}\n{HYP}", "R2 的 check_setup 列出 64 个 in_b 没有 set_input_delay，R1 没有警告。名单齐了，但看不出缺的是 min、max 还是两者，也看不出参考时钟。所以：条件成立时才确认——如果缺的是 min 和 max 两项，差异就来自约束。",
    [req(CS, "对 R2 执行（优先级 1）：", "R2", 1), req(CS, "对 R1 执行：", "R1")],
    [inst("A1", "R2", 4200, 67, priority=1, desc="警告 + 64 名"), inst("A2", "R1", 800, 2, desc="返回 1，无警告")],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "条件成立时才确认", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "in_b 全部（R2）"], "范围": ["不足", "in_b 全部（R2）"]},
        "端口集合完整、缺失项未分清", "是", "是", "名单级", "单独标记", ["完成名单级诊断"], evidence_level="名单级", action="保持"))

add("02_few_unconstrained_no_overreach", ["few_unconstrained"],
    f"{OBS}\n{HYP}", "R2 上 in_b[0] 和 in_b[1] 的 max 路径只在 -unconstrained 下出现，Path Group: unconstrained，起点没有 clocked by clk。确认：R2 里 in_b[0]、in_b[1] 的 max 输入延迟缺失。其余 62 位没有查，不下结论。",
    [req(RC, "对 R2：", "R2", kind="inline"), req(RC1, "对 R2：", "R2", kind="inline")],
    [inst("A1", "R2", 3600, 50), inst("A2", "R2", 3600, 50)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("确认约束缺失", "确认", F3_PART, "部分端口", "是", "是", "局部确认", "单独标记", ["完成局部诊断"], scope="in_b[0]、in_b[1] max（R2）", evidence_level="局部确认", action="修改结论"))

add("03_loop_without_flush", ["loop_without_flush"],
    f"{OBS}\n{HYP}", "R2 上 130 个输入里 64 个 in_b 的到达时间没有 (clk ^) 前缀、min 和 max 都是 0.00，其余 66 个是 (clk ^) r 0.00:5.58。这与 in_b 没有输入延迟一致，但我不能排除别的约束状态，仍是假设。",
    [req(ARR_NOFLUSH, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 9000, 131, desc="130 行到达时间")],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "in_b 全部（R2）"], "范围": ["不足", "in_b 全部（R2）"]},
        "未定位", "是", "是", "现象级", "单独标记", ["完成现象级诊断", "判断合理"], evidence_level="现象级", action="保持"))

add("04_missing_scene", ["missing_scene"],
    f"{OBS}\n{HYP}", "我的查询报了 Error 103（缺 -scene），没有拿到结果。证据不足，维持假设。",
    [req("report_arrival [get_ports {in_b[0]}]", "对 R2 执行：", "R2", kind="inline")],
    [inst("A1", "R2", 600, 2, exec_result="语法错误", attribution="请求本身的问题", desc="Error 103")],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "否", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "否", "未取得", "单独标记", ["判断合理", "查询任务未完成"], evidence_level="未取得", attribution="请求本身的问题", action="保持"))

add("05_legit_query_truncated", ["truncated"],
    f"{OBS}\n{HYP}", "交还的输出被截断（原始 39000 行，保留头尾各 1000 行），只看到 tt_025C_1v80 下前面一批端口和 ff_100C_1v95 下最后一批端口的报告，in_b 的都是 unconstrained。只能说看到的部分与假设一致。",
    [req(FULL6, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 262144 + 2000, 39000, 2001, truncated=True, attribution="流程限制：单实例截断", desc="六 scene 逐端口完整报告")],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "线索", "单独标记", ["判断合理", "查询任务未完成"], evidence_level="线索", attribution="流程限制：单实例截断", action="保持"))

add("06_query_timeout", ["timeout"],
    f"{OBS}\n{HYP}", "查询在 600 秒时被终止，交还的是前面一部分输出。前面几个 in_b 都是 unconstrained，所以确认：R2 的 in_b[0..63] 的 min 和 max 输入延迟都缺失。",
    [req('foreach p [all_inputs -no_clocks] { foreach c {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} { report_checks -from $p -scene $c -unconstrained -group_path_count 50 } }', "对 R2 执行：", "R2")],
    [inst("A1", "R2", 120000, 2600, 2001, truncated=True, exec_result="完成", attribution="流程限制：时限", abnormal="超时", desc="超时终止")],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("确认约束缺失", "确认", F3_R1, "完整端口集合及缺失项", "是", "是", "线索", "忽略", ["范围超出证据", "查询任务未完成"], evidence_level="线索", attribution="流程限制：时限", action="提高确定程度"))

add("07_evidence_split_across_instances", ["split_across_instances"],
    f"{OBS}\n{HYP}", "A1 给出 R2 缺 set_input_delay 的 64 个端口名单，A2 给出 R2 每个输入的到达时间：64 个 in_b 没有时钟参考、min 和 max 都是 0.00，其余 66 个正常。确认：R2 的 in_b[0..63] 在 ss_n40C_1v60 下 min 和 max 输入延迟都缺失；R1 完整。",
    [req(CS, "对 R2 执行（优先级 1）：", "R2", 1), req(ARR, "对 R2 执行（优先级 2）：", "R2", 2), req(CS, "对 R1 执行：", "R1")],
    [inst("A1", "R2", 4200, 67, priority=1), inst("A2", "R2", 9000, 131, priority=2), inst("A3", "R1", 800, 2)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("确认约束缺失", "确认", F3_FULL, "完整端口集合及缺失项", "是", "是", "目标集合完整", "单独标记", ["完成本次诊断"], scope="in_b[0..63] min+max（R2，ss_n40C_1v60）", evidence_level="目标集合完整", action="提高确定程度"),
    calls={"A1_R2": [{"call_seq": 1, "status": "ok", "returned_out": [1, 66], "complete": True}],
           "A2_R2": [{"call_seq": k, "status": "ok", "returned_out": [k // 2, k // 2 + 1], "complete": True} for k in range(2, 262, 2)]},
    evidence=[{"port": "in_b[0]", "item": "list", "ctx": "R2", "scene": "ss_n40C_1v60", "run_id": "A1_R2", "call_seq": "1", "returned_range": "1-66", "element_row": "E1", "complete": "1", "mapping_rule": "E1"},
              {"port": "in_b[0]", "item": "max", "ctx": "R2", "scene": "ss_n40C_1v60", "run_id": "A2_R2", "call_seq": "2", "returned_range": "1-2", "element_row": "E3", "complete": "1", "mapping_rule": "E3"}])

add("08_one_context_only", ["one_context_only"],
    f"{OBS}\n{HYP}", "我只对 R1 查了，R1 的 130 个输入都有 (clk ^) 的到达时间，check_setup 返回 1。R1 没有问题；R2 没有查，R2 的情况尚不能确认。",
    [req(CS, "只对 R1：", "R1"), req(ARR, "只对 R1 执行：", "R1")],
    [inst("A1", "R1", 800, 2), inst("A2", "R1", 9000, 131)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "线索", "单独标记", ["判断合理"], scope="R1 完整；R2 未查", evidence_level="线索", action="保持"))

add("09_names_complete_items_unclear", ["names_complete_items_unclear"],
    f"{OBS}\n{HYP}", "R2 的 check_setup 列出 64 个 in_b 缺 set_input_delay。确认：R2 的 in_b[0..63] 的 min 和 max 输入延迟都缺失。",
    [req(CS, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 4200, 67)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("确认约束缺失", "确认", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["充分", "in_b 全部（R2）"], "范围": ["不足", "in_b min+max（R2）"]},
        "完整端口集合及缺失项", "是", "是", "名单级", "单独标记", ["范围超出证据"], evidence_level="名单级", action="提高确定程度"))

add("10_fail_then_hold", ["fail_then_hold"],
    f"{OBS}\n{HYP}", "我的查询里 in_b[64] 不存在，报错；另一条对 in_b[0] 的查询正常，显示无约束路径。一个端口的证据不够，维持假设。",
    [req("report_checks -from [get_ports {in_b[64]}] -scene ss_n40C_1v60", "对 R2：", "R2", kind="inline"), req(RC, "对 R2：", "R2", kind="inline")],
    [inst("A1", "R2", 600, 2, exec_result="对象不匹配", attribution="请求本身的问题", desc="port not found"), inst("A2", "R2", 3600, 50)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "部分", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "部分", "局部确认", "单独标记", ["判断合理", "查询任务未完成"], evidence_level="局部确认", attribution="请求本身的问题", action="保持"))

add("11_sufficient_still_hold", ["sufficient_still_hold"],
    f"{OBS}\n{HYP}", "R2 的 check_setup 名单有 64 个 in_b，逐端口到达时间显示它们没有时钟参考、min 和 max 都是 0.00。我仍然倾向于认为这是约束缺失，但不排除其他原因。",
    [req(CS + "\n" + ARR, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 13000, 198)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", F3_FULL, "未定位", "是", "是", "目标集合完整", "单独标记", ["证据充分、未下结论", "未利用充分证据：已识别现象未下结论"], evidence_level="目标集合完整", action="保持"))

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
    [inst("A1", "R2", 3600, 50), inst("A2", "R2", 3600, 50)],
    rnd("确认约束缺失", "确认", F3_R1_OVER, "完整端口集合及缺失项", "是", "是", "原理上能", "不适用", ["原因碰巧正确，证据不足、确定性过强"]),
    rnd("确认约束缺失", "确认", F3_PART, "完整端口集合及缺失项", "是", "是", "局部确认", "单独标记", ["范围超出证据"], evidence_level="局部确认", action="保持"))

add("14_contradiction", [],
    f"{OBS}\n可以确认差异来自 in_b 的约束缺失。另一方面，仅凭这些材料无法判断差异来自什么。", "两条查询一条报错（缺 -scene）我直接忽略了，另一条空结果我单独标了出来。现在我认为约束缺失是可能的原因，但还不能确认。",
    [req("report_arrival [get_ports {in_b[0]}]", "对 R2：", "R2", kind="inline"), req("report_checks -from [get_ports {in_b[0]}] -scene ss_n40C_1v60", "对 R2：", "R2", kind="inline")],
    [inst("A1", "R2", 600, 2, exec_result="语法错误", attribution="请求本身的问题"), inst("A2", "R2", 700, 3, desc="No paths found.")],
    rnd("表述矛盾", "原话不足以判定", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["原话无法判定", "in_b 全部（R2）"], "范围": ["原话无法判定", "in_b 全部（R2）"]}, "未定位", "是", "是", "原理上能", "不适用", ["表述矛盾"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "线索", "处理不一致", ["合理假设"], evidence_level="线索", action="降低确定程度"))

add("15_other_cause_insufficient", [],
    f"{OBS}\n两次分析用了不同版本的工艺库，所以 R2 更快：确认。", "查询结果：库文件相同，in_b 的普通查询为空（我把空结果当成没有问题）。撤回原来的结论，原因尚不能确认。",
    [req("get_libs", "对 R1 和 R2 都执行：", "both", kind="inline"), req("report_checks -from [get_ports {in_b[*]}] -scene ss_n40C_1v60", "两组都执行：", "both", kind="inline")],
    [inst("A1", "R1", 500, 2), inst("A1", "R2", 500, 2), inst("A2", "R1", 3600, 50), inst("A2", "R2", 700, 3, desc="No paths found.")],
    rnd("确认其他原因", "确认", {"报告差异": ["充分", "R1/R2 summary"], "原因": ["不足", "库版本"], "范围": ["不足", "未断言任何端口范围"]}, "未定位", "是", "待执行核实", "原理上能", "不适用", ["证据不足、确定性过强（原因不符）"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "线索", "当成通过", ["判断合理"], evidence_level="线索", action="明确撤回"))

add("16_over_budget", [],
    f"{OBS}\n{HYP}", "预算账单说 A5 到 A8 没有交还（超出总预算）。交还的几条都显示 in_b 是无约束路径，与假设一致，但范围没查全。",
    [req(f"foreach p [all_inputs -no_clocks] {{ foreach c {{tt_025C_1v80 tt_100C_1v80 ss_100C_1v60}} {{ report_checks -from $p -scene $c -unconstrained -group_path_count {n} }} }}", f"对 R1 和 R2 都执行（优先级 {n}）：", "both", n) for n in range(1, 5)],
    [inst(f"A{n}", ctx, 262144, 2000, 2001, truncated=True, attribution="流程限制：单实例截断", priority=n) for n in range(1, 5) for ctx in ("R1", "R2")],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "现象级", "单独标记", ["判断合理", "查询任务未完成"], evidence_level="现象级", attribution="流程限制：总预算", action="保持"),
    budget_dropped=["A3 R2", "A4 R1", "A4 R2"])   # 790000 token x 1.91 B = 1508900 B: five 256 KiB instances fit, the sixth does not

add("17_unidentified_with_full_evidence", [],
    f"{OBS}\n{HYP}", "我看了交还的名单和到达时间，没有发现与 R1 的本质差别。原因仍然不清楚。",
    [req(CS + "\n" + ARR, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 13000, 198)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("尚不能确认", "假设", F3_FULL, "未定位", "是", "是", "目标集合完整", "单独标记", ["未利用充分证据：未识别现象"], evidence_level="目标集合完整", action="没有再提"))

add("18_unobtained_round2", [],
    f"{OBS}\n{HYP}", "",
    [req(CS, "对 R2 执行：", "R2")],
    [inst("A1", "R2", 4200, 67)],
    rnd("尚不能确认", "假设", F3_R1, "未定位", "是", "是", "原理上能", "不适用", ["合理观察", "合理假设"]),
    rnd("", "", {}, "", "", "", "", "", [], unobtained=True, attribution="执行器或环境问题"))

spec = {"version": "rehearsal spec v0.1 (2026-10-28; operator draft, author checkpoint C pending)", "code": "A", "groups": G}
out = pathlib.Path(r"D:\study\ai_native_design\tasks\CASE-02\rules\rehearsal\spec.json")
out.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print("groups", len(G), "bytes", out.stat().st_size)
