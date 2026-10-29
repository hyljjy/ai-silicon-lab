"""Assemble the round-2 query results for one code (protocol v0.3 section 6.4; rules/rewrite_table.md sections 6, 8).
Copied and adapted from tasks/CASE-01/diag/scripts/build_results.py (rules/copied_from.tsv).

  python3 -B scripts/build_results.py <code>      -> round2/<code>_results.md, round2/<code>_budget.json

Input: round2/translation.tsv (author-reviewed). Tab-separated columns:
  code qid ctx original executed rewrites run_id_first run_id_rewritten collected fixed_code attribution author_note
Every collected instance is first rendered on its own; the rendered byte sizes go through budget.allocate (declared
priority, numeric qid, R1 before R2); dropped instances are replaced by a one-line marker; the budget statement is
appended at the end. An instance whose environment check failed is never returned (fixed text, no output).
A code with no rows gets the single sentence that it proposed no executable query, plus the statement."""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2paths import CASE, RULES, read_bytes, write_new_or_same  # noqa: E402
import budget  # noqa: E402
import contract as contract_mod  # noqa: E402

COLUMNS = ["code", "qid", "ctx", "original", "executed", "rewrites", "run_id_first", "run_id_rewritten", "collected",
           "fixed_code", "attribution", "author_note"]
NO_QUERY = "你第 1 轮没有提出可执行的查询。\n"
ENV_FAIL = "该次执行的环境核对未通过，结果不交还。"
DROPPED = "[未交还：超出总预算，见文末预算账单]"
WHATIF = "改变模型的对照"


def rows_for(code, case=CASE):
    with open(os.path.join(case, "round2", "translation.tsv"), encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t")]
    if rows and list(rows[0].keys()) != COLUMNS:
        raise SystemExit(f"CASE02 FAIL: translation.tsv columns must be {COLUMNS}")
    return [r for r in rows if r["code"] == code]


def block(lang, text):
    return f"```{lang}\n{text.rstrip(chr(10))}\n```\n"


def render_instance(r, case):
    """(markdown of one instance with its output, result.json dict or None)."""
    txt = lambda rel: read_bytes(os.path.join(case, rel)).decode("utf-8")
    lang = "tcl" if r["original"].endswith(".tcl") else "text"
    head = f"### 查询 {r['qid']}（{r['ctx']}）\n" if r["ctx"] in ("R1", "R2") else f"### 查询 {r['qid']}\n"
    part = [head, "你写的查询：\n", block(lang, txt(r["original"]))]
    if r["collected"] == "-":
        part.append(f"结果代码：{r['fixed_code']}\n")
        return "".join(part), None
    run = os.path.join(case, "queries", "round2", r["collected"])
    with open(os.path.join(run, "result.json"), encoding="utf-8") as f:
        res = json.load(f)
    part += ["实际执行的命令：\n", block("tcl", txt(r["executed"])),
             f"机械改写：{'无' if r['rewrites'] in ('-', '') else r['rewrites']}\n"]
    if not res.get("env_relation_ok", False):
        part += [f"结果代码：{ENV_FAIL}\n", f"归因：{res.get('attribution', '执行器或环境问题')}\n"]
        return "".join(part), res
    part += [f"执行类型：{res['exec_type']}；执行结果：{res['exec_result']}；异常：{res.get('abnormal', '-')}；"
             f"归因：{res.get('attribution', '-')}\n"]
    if res["exec_type"] == WHATIF:
        part.append("说明：这条查询改变了分析模型，结果只作对照，不代表原始分析模型。\n")
    part += ["输出：\n", block("text", read_bytes(os.path.join(run, "query_return.txt")).decode("utf-8"))]
    return "".join(part), res


def render(code, c=None, case=CASE):
    """(results markdown, allocation)."""
    c = c or contract_mod.load(os.path.join(RULES, "contract.json"))
    rows = rows_for(code, case)
    if not rows:
        alloc = budget.allocate([], c)
        return NO_QUERY + "\n" + budget.statement(alloc, c), alloc
    rendered = {}
    instances = []
    for r in rows:
        key = (r["qid"], r["ctx"])
        text, res = render_instance(r, case)
        rendered[key] = (text, res, r)
        if res is not None and res.get("env_relation_ok", False):
            instances.append({"qid": r["qid"], "ctx": r["ctx"], "rendered_bytes": len(text.encode("utf-8")),
                              "returned_bytes": res.get("returned_bytes", 0), "priority": _priority_of(r, case),
                              "truncated": bool(res.get("output_attr", {}).get("truncated")),
                              "raw_lines": res.get("raw_lines"), "returned_lines": res.get("returned_lines")})
    alloc = budget.allocate(instances, c)
    dropped = {(d["qid"], d["ctx"]) for d in alloc["dropped"]}
    parts = []
    for r in rows:
        key = (r["qid"], r["ctx"])
        text, res, _ = rendered[key]
        if key in dropped:
            head = text.split("\n", 1)[0]
            parts.append(head + "\n" + DROPPED + "\n")
        else:
            parts.append(text)
    return "\n".join(parts) + "\n" + budget.statement(alloc, c), alloc


def _priority_of(r, case):
    """Declared priority from extracted_<code>.tsv when present."""
    path = os.path.join(case, "round2", f"extracted_{r['code']}.tsv")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row.get("qid") == r["qid"]:
                p = row.get("priority", "-")
                return int(p) if p not in ("-", "", None) else None
    return None


def visibility(alloc):
    """Final visibility of every instance in the model's prompt (R6 M4): the evidence checks of claims_stats refuse
    an instance that was executed but never returned."""
    out = {}
    for i in alloc["returned"]:
        out[f"{i['qid']}_{i['ctx']}"] = {"visible": True, "reason": "-"}
    for d in alloc["dropped"]:
        out[f"{d['qid']}_{d['ctx']}"] = {"visible": False, "reason": d["attribution"], "rule": d["rule"]}
    return out


def check_budget(text, alloc, c):
    """Budget check of a complete rendered text (the whole round-2 prompt is checked by build_prompt)."""
    import math
    rendered_bytes = len(text.encode("utf-8"))
    tokens = math.ceil(rendered_bytes / c.token_bytes_ratio)
    return {"rendered_bytes": rendered_bytes, "tokens": tokens, "budget_tokens": c.total_budget_tokens,
            "ok": tokens <= c.total_budget_tokens, "allocated_tokens": alloc["total_tokens"]}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: build_results.py <code>")
        return 2
    code = argv[0]
    c = contract_mod.load(os.path.join(RULES, "contract.json"))
    text, alloc = render(code, c)
    data = text.encode("utf-8")
    write_new_or_same(os.path.join(CASE, "round2", f"{code}_results.md"), data)
    write_new_or_same(os.path.join(CASE, "round2", f"{code}_budget.json"),
                      json.dumps(alloc, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    write_new_or_same(os.path.join(CASE, "round2", f"{code}_visibility.json"),
                      json.dumps(visibility(alloc), ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    print(f"RESULTS OK: round2/{code}_results.md ({len(data)} bytes; returned {len(alloc['returned'])}, "
          f"dropped {len(alloc['dropped'])}, {alloc['total_tokens']}/{alloc['budget_tokens']} tokens)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
