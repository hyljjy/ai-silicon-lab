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


def allocate(instances, c):
    if not c.budget_ready:
        raise contract_mod.ContractError("total budget not set in contract.json")
    ordered = sorted(instances, key=_sort_key)
    returned, dropped, total = [], [], 0
    cut = False
    for n, inst in enumerate(ordered):
        tokens = math.ceil(inst["rendered_bytes"] / c.token_bytes_ratio)
        if not cut and total + tokens <= c.total_budget_tokens:
            total += tokens
            returned.append(dict(inst, tokens=tokens, returned=True))
        else:
            cut = True
            rule = _rule_between(ordered[n - 1], inst) if n else c.keep_order[0]
            dropped.append(dict(inst, tokens=tokens, returned=False, rule=rule, attribution=ATTR_BUDGET))
    return {"returned": returned, "dropped": dropped, "total_tokens": total, "budget_tokens": c.total_budget_tokens,
            "ratio": c.token_bytes_ratio}


def statement(alloc, c):
    L = ["## 预算账单", "",
         f"① 总预算：{c.total_budget_tokens} token（每 token 约 {c.token_bytes_ratio} 字节的保守换算；本次已交还合计 {alloc['total_tokens']} token）。",
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
