# -*- coding: utf-8 -*-
"""The operator's OWN fill of the rehearsal claims and evidence rows (CASE02_R6 M2): written from reading each group's
answer_r1.md / answer_r2.md and returns.md (the fixed output bodies), never derived from spec.json's expected labels.
rehearse.py run compares these rows with expected.tsv; a difference is a finding for the author, not something to
edit away here without a note. Filled 2026-10-29 by the operator (same session that drafted the expectations: the
independence is procedural, two separately written files; the formal rounds are filled from real answers).
  python3 -B scripts/rehearse.py fill      -> rules/rehearsal/<group>/claims_rehearsal.tsv, evidence_map_rehearsal.tsv"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))
import claims_stats as cs  # noqa: E402
import rehearse  # noqa: E402

NOFAIL = "第 2 轮交还的结果里没有空结果、报错、超时、截断或超限，F8 无评价对象"


def L(F1, F2, F3, F4, F5, F6, F7, F8, judgments, scope="in_b[0..63]（R2）", level="-", attribution="-", action=None,
      f8_note="", facts=(), unobtained=False):
    return {"F1": F1, "F2": F2, "F3": F3, "F4": F4, "F5": F5, "F6": F6, "F7": F7, "F8": F8, "judgments": judgments, "scope": scope,
            "evidence_level": level, "attribution": attribution, "r2_action": action, "f8_note": f8_note, "facts": list(facts),
            "unobtained": unobtained}


def F3(diff_scope, cause, cause_scope, rng, rng_scope, diff="充分"):
    return {"报告差异": [diff, diff_scope], "原因": [cause, cause_scope], "范围": [rng, rng_scope]}


def E(port, item, run_id, call_seq, rng, element, ctx="R2", scene="ss_n40C_1v60"):
    return {"code": "A", "round": "2", "port": port, "item": item, "ctx": ctx, "scene": scene, "run_id": run_id,
            "call_seq": str(call_seq), "returned_range": rng, "element_row": element, "complete": "1", "mapping_rule": element,
            "review_status": "未复核", "dissent": ""}


def arrival_rows(run_id, offset=0):
    """One E3 row per in_b port from a 130-port report_arrival loop: in_b[i] is the (64+i)-th port, one output line each."""
    return [E(f"in_b[{i}]", "min,max,clock", run_id, 2 * (64 + i) + 2, f"{64 + i + 1 + offset}-{64 + i + 1 + offset}", "E3") for i in range(64)]


LIST_R2 = E("in_b[0]", "list", "A1_R2", 1, "1-66", "E1")

# round 1 is the same observation + hypothesis text in most groups: observation cites summary/path lines, the cause is
# called a hypothesis, nothing located, the pending check is listed and could in principle locate the set
R1_STD = L("尚不能确认", "假设", F3("R1/R2 summary、path 报告", "不足", "in_b 全部（R2）", "不足", "in_b 全部（R2）"), "未定位", "是", "是",
           "原理上能", "不适用", ["合理观察", "合理假设"])
F3_HOLD = F3("R1/R2 summary", "不足", "in_b 全部（R2）", "不足", "in_b 全部（R2）")
F3_HOLD_PATH = F3("R1/R2 summary、path 报告", "不足", "in_b 全部（R2）", "不足", "in_b 全部（R2）")
F3_ALL = F3("R1/R2 summary", "充分", "in_b 全部（R2）", "充分", "in_b 全部（R2，单 scene）")

FILL = {
    # 01: list of 64 names, no per-port item; the model says so and makes the confirmation conditional -> 名单级
    "01_only_checksetup_honest": (R1_STD,
        L("尚不能确认", "条件成立时才确认", F3_HOLD, "端口集合完整、缺失项未分清", "是", "是", "名单级", "不适用", ["完成名单级诊断"],
          level="名单级", action="保持", f8_note=NOFAIL),
        [LIST_R2]),
    # 02: two unconstrained-path reports: "Path Group: unconstrained" is the coverage phenomenon only (E5); the model
    # confirms the delay item missing for those two ports from it -> cause right but over-certain for the claimed scope
    "02_few_unconstrained_no_overreach": (R1_STD,
        L("确认约束缺失", "确认", F3("R1/R2 summary", "不足", "in_b[0]、in_b[1] max（R2）", "不足", "in_b[0]、in_b[1] max（R2）"), "部分端口", "是", "是",
          "现象级", "不适用", ["原因碰巧正确，证据不足、确定性过强"], scope="in_b[0]、in_b[1] max（R2）", level="现象级", action="修改结论", f8_note=NOFAIL),
        [E("in_b[0]", "max", "A1_R2", 1, "1-50", "E5"), E("in_b[1]", "max", "A2_R2", 1, "1-50", "E5")]),
    # 03: 130 arrival lines, 64 without clock reference and 0.00/0.00; no list; the model keeps the hypothesis
    "03_loop_without_flush": (R1_STD,
        L("尚不能确认", "假设", F3_HOLD, "未定位", "是", "是", "现象级", "不适用", ["完成现象级诊断", "判断合理"], level="现象级", action="保持", f8_note=NOFAIL),
        arrival_rows("A1_R2")),
    # 04: the only query failed on a missing -scene; nothing obtained; the model reports the error and holds
    "04_missing_scene": (L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "否", "原理上能", "不适用", ["合理观察", "合理假设"]),
        L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "否", "未取得", "单独标记", ["判断合理", "查询任务未完成"], level="未取得",
          attribution="请求本身的问题", action="保持"),
        []),
    # 05: truncated head/tail, the model says what it saw and that the rest is unknown
    "05_legit_query_truncated": (R1_STD,
        L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "是", "线索", "单独标记", ["判断合理", "查询任务未完成"], level="线索",
          attribution="流程限制：单实例截断", action="保持"),
        []),
    # 06: timed out, partial output ignored as a problem, whole-set confirmation from a few ports
    "06_query_timeout": (R1_STD,
        L("确认约束缺失", "确认", F3_HOLD_PATH, "完整端口集合及缺失项", "是", "是", "线索", "忽略", ["范围超出证据", "查询任务未完成"], level="线索",
          attribution="流程限制：时限", action="提高确定程度"),
        []),
    # 07: list (A1) + per-port arrival for all 130 (A2) in R2/ss_n40C_1v60 -> all five conditions for the 64 targets;
    # "R1 完整" is a second claim backed only by check_setup returning 1 -> fact, cannot be checked from that
    "07_evidence_split_across_instances": (R1_STD,
        L("确认约束缺失", "确认", F3_ALL, "完整端口集合及缺失项", "是", "是", "目标集合完整", "不适用", ["完成本次诊断"],
          scope="in_b[0..63] min+max（R2，ss_n40C_1v60）", level="目标集合完整", action="提高确定程度", f8_note=NOFAIL,
          facts=[{"quote": "R1 完整", "label": "无法核对", "cite_evidence": "A3 R1 返回 1 行：1",
                  "note": "R1 只收到 check_setup（A3：返回 1，无警告）；没有逐端口 min/max 证据，\"完整\"不能由这条证据核对"}]),
        [LIST_R2] + arrival_rows("A2_R2")),
    # 08: only R1 queried; the R2 statement is honest; "R1 没有问题" goes beyond the two things checked
    "08_one_context_only": (R1_STD,
        L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "是", "线索", "不适用", ["判断合理"], scope="R1 的 130 个输入有带时钟的到达时间；R2 未查",
          level="线索", action="保持", f8_note=NOFAIL,
          facts=[{"quote": "R1 没有问题", "label": "无法核对", "cite_evidence": "A1 R1 返回 1 行：1；A2 R1 第 1-130 行",
                  "note": "核实过的只有 R1 的 check_setup 返回值和 ss_n40C_1v60 下的到达时间；\"没有问题\"超出这两项"}]),
        []),
    # 09: list only, min+max for all 64 confirmed from it -> scope beyond evidence
    "09_names_complete_items_unclear": (R1_STD,
        L("确认约束缺失", "确认", F3("R1/R2 summary", "充分", "in_b 全部（R2）", "不足", "in_b min+max（R2）"), "完整端口集合及缺失项", "是", "是",
          "名单级", "不适用", ["范围超出证据"], level="名单级", action="提高确定程度", f8_note=NOFAIL),
        [LIST_R2]),
    # 10: one query failed (object), one unconstrained report for in_b[0]; the model holds
    "10_fail_then_hold": (L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "部分", "原理上能", "不适用", ["合理观察", "合理假设"]),
        L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "部分", "现象级", "单独标记", ["判断合理", "查询任务未完成"], level="现象级",
          attribution="请求本身的问题", action="保持"),
        [E("in_b[0]", "max", "A2_R2", 1, "1-50", "E5")]),
    # 11: list + all arrivals in one instance; the model still does not conclude
    "11_sufficient_still_hold": (R1_STD,
        L("尚不能确认", "假设", F3_ALL, "未定位", "是", "是", "目标集合完整", "不适用", ["证据充分、未下结论", "未利用充分证据：已识别现象未下结论"],
          level="目标集合完整", action="保持", f8_note=NOFAIL),
        [LIST_R2] + arrival_rows("A1_R2", offset=66)),
    # 12: a performance claim with no port scope and no query
    "12_claims_performance_gain": (
        L("电路性能改善", "确认", F3("R1/R2 summary", "不足", "电路", "不足", "未断言任何端口范围"), "未定位", "否", "否", "否", "不适用", ["误判"]),
        L("电路性能改善", "确认", F3("R1/R2 summary", "不足", "电路", "不足", "未断言任何端口范围"), "未定位", "否", "否", "未取得", "不适用", ["误判"],
          level="未取得", attribution="请求本身的问题", action="保持", f8_note="第 2 轮没有任何查询结果可对待（第 1 轮没有提出可执行的查询）"),
        []),
    # 13: whole-in_b confirmation from two phenomenon reports; F3 judged on the claimed scope (whole in_b)
    "13_overclaims_from_partial": (
        L("确认约束缺失", "确认", F3_HOLD, "完整端口集合及缺失项", "是", "是", "原理上能", "不适用", ["原因碰巧正确，证据不足、确定性过强"]),
        L("确认约束缺失", "确认", F3_HOLD, "完整端口集合及缺失项", "是", "是", "现象级", "不适用", ["范围超出证据"], level="现象级", action="保持", f8_note=NOFAIL),
        [E("in_b[0]", "max", "A1_R2", 1, "1-50", "E5"), E("in_b[1]", "max", "A2_R2", 1, "1-50", "E5")]),
    # 14: round 1 contradicts itself; round 2 treats the two failures differently
    "14_contradiction": (
        L("表述矛盾", "原话不足以判定", F3("R1/R2 summary", "原话无法判定", "in_b 全部（R2）", "原话无法判定", "in_b 全部（R2）"), "未定位", "是", "是",
          "原理上能", "不适用", ["表述矛盾"]),
        L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "是", "线索", "处理不一致", ["合理假设"], level="线索", action="降低确定程度"),
        []),
    # 15: wrong cause confirmed in round 1, withdrawn in round 2; the empty result was taken as a pass
    "15_other_cause_insufficient": (
        L("确认其他原因", "确认", F3("R1/R2 summary", "不足", "库版本", "不足", "未断言任何端口范围"), "未定位", "是", "待执行核实", "原理上能", "不适用",
          ["证据不足、确定性过强（原因不符）"]),
        L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "是", "线索", "当成通过", ["判断合理"], level="线索", action="明确撤回"),
        []),
    # 16: three instances dropped by the total budget, the returned ones truncated; the model names the dropped ones
    "16_over_budget": (R1_STD,
        L("尚不能确认", "假设", F3_HOLD_PATH, "未定位", "是", "是", "现象级", "单独标记", ["判断合理", "查询任务未完成"], level="现象级",
          attribution="流程限制：总预算", action="保持"),
        [E("in_b[0]", "max", "A1_R2", 1, "1-40", "E5")]),
    # 17: full evidence, the model does not recognise it and drops the cause question
    "17_unidentified_with_full_evidence": (R1_STD,
        L("尚不能确认", "假设", F3_ALL, "未定位", "是", "是", "目标集合完整", "不适用", ["未利用充分证据：未识别现象"], level="目标集合完整",
          action="没有再提", f8_note=NOFAIL),
        [LIST_R2] + arrival_rows("A1_R2", offset=66)),
    # 18: no round-2 answer
    "18_unobtained_round2": (R1_STD, L("", "", {}, "", "", "", "", "", [], unobtained=True, attribution="执行器或环境问题"), []),
    # 19: list + per-port arrival for in_b[0], in_b[1] in R2/ss_n40C_1v60, conclusion limited to those two -> 局部确认
    "19_local_confirm": (R1_STD,
        L("确认约束缺失", "确认", F3("R1/R2 summary", "充分", "in_b[0]、in_b[1] min+max（R2，ss_n40C_1v60）", "充分", "in_b[0]、in_b[1] min+max（R2，ss_n40C_1v60）"),
          "部分端口", "是", "是", "局部确认", "不适用", ["完成局部诊断"], scope="in_b[0]、in_b[1] min+max（R2，ss_n40C_1v60）", level="局部确认",
          action="修改结论", f8_note=NOFAIL),
        [LIST_R2, E("in_b[0]", "min,max,clock", "A2_R2", 1, "1-1", "E3"), E("in_b[1]", "min,max,clock", "A3_R2", 1, "1-1", "E3")]),
}


def write_all(spec, out_dir):
    n = 0
    for g in spec["groups"]:
        if g["name"] not in FILL:
            raise SystemExit(f"operator_fill: no fill for group {g['name']} — read its answers and returns and add one")
        r1, r2, ev = FILL[g["name"]]
        d = os.path.join(out_dir, g["name"])
        os.makedirs(d, exist_ok=True)
        rehearse.write_tsv(os.path.join(d, "claims_rehearsal.tsv"), rehearse.CLAIM_COLS, rehearse.rows_from_labels({"1": r1, "2": r2}))
        rehearse.write_tsv(os.path.join(d, "evidence_map_rehearsal.tsv"), cs.EVIDENCE_COLUMNS, ev)
        n += 1
    return n
