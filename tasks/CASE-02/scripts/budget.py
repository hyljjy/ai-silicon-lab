"""Total-budget allocation of the round-2 returns and the budget statement (protocol v0.3 section 6.4 (b)(c);
author decisions R4 Q1). Instances are kept in the contract's keep order (declared priority, numeric qid, R1 before
R2) until the cumulative rendered cost exceeds total_budget_tokens; from the first instance that does not fit, every
later one is dropped, each with the ordering rule that put it there. Cost = ceil(rendered_bytes / token_bytes_ratio)."""
import math
import re

import contract as contract_mod

ATTR_BUDGET = "流程限制：总预算"
FIXED_SENTENCE = "以上未交还的结果已完整归档，未交还原因是累计超过公开的总预算，不是查询失败。"
RULE_TEXT = {"declared_priority": "模型声明的优先级", "qid_numeric": "查询编号顺序", "R1_before_R2": "R1 先于 R2"}


def qid_key(qid):
    m = re.match(r"^([A-Za-z]*)(\d+)$", qid)
    return (m.group(1), int(m.group(2))) if m else (qid, 0)


def _sort_key(i):
    pr = i.get("priority")
    return (0 if pr is not None else 1, pr if pr is not None else 0, qid_key(i["qid"]), 0 if i["ctx"] == "R1" else 1)


def _rule_between(prev, cur):
    """The keep-order rule by which `cur` sorts after `prev`."""
    pp, pc = prev.get("priority"), cur.get("priority")
    if (pp is not None) != (pc is not None) or (pp is not None and pp != pc):
        return "declared_priority"
    if qid_key(prev["qid"]) != qid_key(cur["qid"]):
        return "qid_numeric"
    return "R1_before_R2"


FRAME_BYTES = 24          # the one-line marker a dropped instance leaves in the results ("### 查询 … [未交还…]")


def _cost(instances, dropped_rest, c):
    """Tokens the prompt actually carries for these returned instances: their rendered bytes plus the budget
    statement that will list them and the dropped ones, plus one marker line per dropped instance (R6 M5)."""
    body = sum(i["rendered_bytes"] for i in instances)
    markers = FRAME_BYTES * len(dropped_rest)
    total = 0
    for _ in range(3):      # the statement prints the total itself; iterate to a fixed point of its byte length
        stmt = len(statement({"returned": instances, "dropped": dropped_rest, "total_tokens": total}, c).encode("utf-8"))
        new_total = math.ceil((body + stmt + markers) / c.token_bytes_ratio)
        if new_total == total:
            break
        total = new_total
    return total, math.ceil((stmt + markers) / c.token_bytes_ratio)


def allocate(instances, c):
    if not c.budget_ready:
        raise contract_mod.ContractError("total budget not set in contract.json")
    ordered = sorted(instances, key=_sort_key)
    returned, dropped = [], []
    cut = False
    for n, inst in enumerate(ordered):
        tokens = math.ceil(inst["rendered_bytes"] / c.token_bytes_ratio)
        rest = [dict(x, rule="-") for x in ordered[n + 1:]]
        cand = returned + [dict(inst, tokens=tokens, returned=True)]
        total_if, _ = _cost(cand, rest, c)
        if not cut and total_if <= c.total_budget_tokens:
            returned = cand
        else:
            cut = True
            rule = _rule_between(ordered[n - 1], inst) if n else c.keep_order[0]
            dropped.append(dict(inst, tokens=tokens, returned=False, rule=rule, attribution=ATTR_BUDGET))
    total, overhead = _cost(returned, dropped, c)
    return {"returned": returned, "dropped": dropped, "total_tokens": total, "overhead_tokens": overhead,
            "budget_tokens": c.total_budget_tokens, "ratio": c.token_bytes_ratio}


def prompt_capacity(rendered_bytes, results_bytes, c, capacity_tokens=None):
    """Two separate checks (R6 M5): the returned results against total_budget_tokens, and the whole round-2 prompt
    against the input capacity (ctx_min minus the shell overhead, the round-2 output reserve and the safety margin)."""
    if capacity_tokens is None:
        bt = c.budget_table or {}
        capacity_tokens = int(bt.get("ctx_min", 0) - bt.get("overhead_tokens", 0) - bt.get("round2_output_reserve_tokens", 0)
                              - bt.get("safety_fraction", 0.1) * bt.get("ctx_min", 0))
    results_tokens = math.ceil(results_bytes / c.token_bytes_ratio)
    prompt_tokens = math.ceil(rendered_bytes / c.token_bytes_ratio)
    return {"results_bytes": results_bytes, "results_tokens": results_tokens, "results_budget": c.total_budget_tokens,
            "results_ok": results_tokens <= c.total_budget_tokens, "rendered_bytes": rendered_bytes,
            "prompt_tokens": prompt_tokens, "capacity_tokens": capacity_tokens, "capacity_ok": prompt_tokens <= capacity_tokens,
            "ok": results_tokens <= c.total_budget_tokens and prompt_tokens <= capacity_tokens}


def statement(alloc, c):
    L = ["## 预算账单", "",
         f"① 总预算：{c.total_budget_tokens} token（每 token 约 {c.token_bytes_ratio} 字节的保守换算；本次已交还合计 {alloc.get('total_tokens', 0)} token，含本账单）。",
         "", "② 已交还的实例："]
    if alloc["returned"]:
        for i in alloc["returned"]:
            L.append(f"- {i['qid']} {i['ctx']}：{i.get('returned_lines', i.get('raw_lines', '?'))} 行"
                     f"{'，已截断（原始 ' + str(i.get('raw_lines')) + ' 行）' if i.get('truncated') else '，未截断'}")
    else:
        L.append("- （无）")
    L += ["", "③ 未交还的实例：" + ("（无）" if not alloc["dropped"] else "")]
    for d in alloc["dropped"]:
        L.append(f"- {d['qid']} {d['ctx']}：完整输出 {d.get('raw_lines', '?')} 行，按\"{RULE_TEXT.get(d['rule'], d['rule'])}\"排在后面")
    L += ["", "④ " + FIXED_SENTENCE]
    return "\n".join(L) + "\n"
