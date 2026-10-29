"""Rehearsal of the scoring pipeline on fixed fake answers (protocol v0.3 step 4; impl_plan Task 10).
  python3 -B scripts/rehearse.py generate      # rules/rehearsal/<group>/ files and coverage.tsv from spec.json
  python3 -B scripts/rehearse.py run           # extraction, budget, claims validation, expected comparison, coverage
For every group of rules/rehearsal/spec.json: the fake round-1 answer goes through extract_queries (context scope and
priority must match the spec), the instances through budget.allocate (dropped set must match), the operator's claims
rows (claims_rehearsal.tsv) through claims_stats.problems, and every cell is compared with expected.tsv (the labels the
author confirmed at checkpoint C; the operator's draft until then). coverage.tsv maps every decision-table row, every
field value and every query shape to the groups that exercise it; run() fails when a target has no passing group."""
import csv
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2paths  # noqa: E402
import budget  # noqa: E402
import claims_stats as cs  # noqa: E402
import contract as contract_mod  # noqa: E402
import extract_queries as eq  # noqa: E402

REH = os.path.join(c2paths.RULES, "rehearsal")
QUERY_SHAPES = ["only_checksetup_honest", "few_unconstrained", "loop_without_flush", "missing_scene", "truncated", "timeout",
                "split_across_instances", "one_context_only", "names_complete_items_unclear", "fail_then_hold",
                "sufficient_still_hold"]
FAKE_CASE = os.path.join(c2paths.RUNS, "rehearsal_case")
CLAIM_COLS = cs.COLUMNS


def load_spec(path=None):
    with open(path or os.path.join(REH, "spec.json"), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- answers
def answer_r1(g):
    lines = ["一、观察", g["r1_text"].split("\n")[0] if g["r1_text"] else "- （无）"]
    obs = [l for l in g["r1_text"].split("\n")[:-1]] if g["r1_text"] else []
    lines = ["一、观察"] + (obs or ["- （无）"])
    conclusion = g["r1_text"].split("\n")[-1] if g["r1_text"] else "尚不能确认。"
    lines += ["", "二、结论和确定程度", conclusion, "", "三、证据", "- summary 与 path 报告的差异；有效约束清单尚未提供。", "", "四、检查请求"]
    if not g["requests"]:
        lines.append("（无）")
    for n, r in enumerate(g["requests"], 1):
        if r["kind"] == "inline":
            lines.append(f"{n}. {r['prose']}`{r['code']}`")
        else:
            lines += [f"{n}. {r['prose']}", "```tcl", r["code"], "```"]
    return "\n".join(lines) + "\n"


def answer_r2(g):
    if g["expected"]["2"].get("unobtained"):
        return ""
    return "一、观察\n- 同第 1 轮。\n\n二、结论和确定程度\n" + g["r2_text"] + "\n\n三、证据\n- 见交还结果。\n\n四、检查请求\n（无新请求）\n"


def returns_md(g):
    lines = ["# 交还结果（操作者按契约手写的摘要，供预演）", ""]
    for i in g["instances"]:
        lines.append(f"- {i['qid']} {i['ctx']}：{i['description'] or i['exec_result']}；原始 {i['raw_lines']} 行，交还 {i['returned_lines']} 行"
                     f"{'，已截断' if i['truncated'] else ''}；执行结果 {i['exec_result']}；归因 {i['attribution']}")
    if not g["instances"]:
        lines.append("- 你第 1 轮没有提出可执行的查询。")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- pipeline pieces
def extract_group(g):
    return [u for u in eq.extract(answer_r1(g), eq.commands()) if u["kind"] != "text"]


def allocate_group(g, c=None):
    c = c or contract_mod.load(os.path.join(c2paths.RULES, "contract.json"))
    return budget.allocate([dict(i) for i in g["instances"]], c)


def claims_rows(g, code=None):
    """(claims rows, evidence rows) the operator fills for this group, generated from the spec."""
    code = code or "A"
    rows, ev = [], []
    for rnd in ("1", "2"):
        e = g["expected"][rnd]
        n = 0

        def rid():
            nonlocal n
            n += 1
            return f"{code}-{rnd}-{n:03d}"
        if e.get("unobtained"):
            rows.append(dict.fromkeys(CLAIM_COLS, "") | {"id": rid(), "code": code, "round": rnd, "field": "ROUND", "proposition": "-",
                        "value": cs.UNOBTAINED, "scope_claimed": "-", "evidence_level": "-", "judgments": "-",
                        "attribution": e["attribution"], "review_status": "未复核", "note": "第 2 轮未取得有效答复（预演样例）"})
            continue
        for f in cs.FIELDS:
            if f == "F3":
                for prop in cs.PROPOSITIONS:
                    val, scope = e["F3"][prop]
                    rows.append(_row(rid(), code, rnd, f, prop, val, scope, e, g))
            else:
                rows.append(_row(rid(), code, rnd, f, "-", e[f], e["scope"] if f in ("F1", "F4") else "-", e, g))
    for x in g.get("evidence", []):
        ev.append(dict(x, code=code, round="2", review_status="未复核", dissent=""))
    return rows, ev


def _row(rid, code, rnd, field, prop, value, scope, e, g):
    r = dict.fromkeys(CLAIM_COLS, "")
    r.update({"id": rid, "code": code, "round": rnd, "field": field, "proposition": prop, "value": value, "scope_claimed": scope,
              "evidence_level": e["evidence_level"] if field == "F7" and rnd == "2" else "-",
              "judgments": ";".join(e["judgments"]) if field == "F1" else "-",
              "attribution": e["attribution"] if field in ("F7", "F1") else "-",
              "review_status": "未复核", "location": "二、结论" if field in ("F1", "F2") else "-",
              "note": e["f8_note"] if field == "F8" and e.get("f8_note") else ""})
    if rnd == "2":
        r["r2_action"] = e["r2_action"]
        r["r1_ref"] = rid.replace("-2-", "-1-") if e["r2_action"] != "没有再提" else ""
    return r


def write_tsv(path, cols, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t", quoting=csv.QUOTE_NONE))


# ---------------------------------------------------------------- coverage
def coverage_targets():
    t = [("judgment_row", j) for j in cs.JUDGMENTS if j != "-"]
    for f, per in cs.FIELD_VALUES.items():
        for rnd, vals in per.items():
            t += [("field_value", f"{f}/{rnd}/{v}") for v in vals]
    t += [("query_shape", s) for s in QUERY_SHAPES]
    t += [("r2_action", a) for a in cs.ACTIONS]
    return t


def group_targets(g):
    hits = set()
    for rnd in ("1", "2"):
        e = g["expected"][rnd]
        if e.get("unobtained"):
            hits.add(("field_value", f"ROUND/{rnd}/{cs.UNOBTAINED}"))
            continue
        for j in e["judgments"]:
            hits.add(("judgment_row", j))
        for f in cs.FIELDS:
            if f == "F3":
                for prop in cs.PROPOSITIONS:
                    hits.add(("field_value", f"F3/1/{e['F3'][prop][0]}"))
            else:
                key = rnd if rnd in cs.FIELD_VALUES[f] else "1"
                hits.add(("field_value", f"{f}/{key}/{e[f]}"))
        if rnd == "2" and e.get("r2_action"):
            hits.add(("r2_action", e["r2_action"]))
    for s in g["shapes"]:
        hits.add(("query_shape", s))
    return hits


def coverage_hits(spec):
    hits = set()
    for g in spec["groups"]:
        hits |= group_targets(g)
    return hits


# ---------------------------------------------------------------- generate / run
def generate(spec, out_dir=None):
    out = out_dir or REH
    rows = []
    for g in spec["groups"]:
        d = os.path.join(out, g["name"])
        os.makedirs(d, exist_ok=True)
        for name, text in (("answer_r1.md", answer_r1(g)), ("answer_r2.md", answer_r2(g)), ("returns.md", returns_md(g))):
            with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        with open(os.path.join(d, "returns_bytes.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(g["instances"], f, ensure_ascii=False, indent=1)
        claims, ev = claims_rows(g)
        write_tsv(os.path.join(d, "claims_rehearsal.tsv"), CLAIM_COLS, claims)
        write_tsv(os.path.join(d, "evidence_map_rehearsal.tsv"), cs.EVIDENCE_COLUMNS, ev)
        if not os.path.exists(os.path.join(d, "expected.tsv")):          # the author's file is never overwritten
            write_tsv(os.path.join(d, "expected.tsv"), CLAIM_COLS, claims)
        for kind, value in sorted(group_targets(g)):
            rows.append({"target_type": kind, "target_value": value, "group": g["name"]})
    with open(os.path.join(out, "coverage.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("target_type\ttarget_value\tgroup\n")
        for r in rows:
            f.write(f"{r['target_type']}\t{r['target_value']}\t{r['group']}\n")
    return out


def _fake_case(spec):
    """A scratch case directory with the fake queries/round2/<run_id>/calls.jsonl the evidence rows point to."""
    if os.path.isdir(FAKE_CASE):
        shutil.rmtree(FAKE_CASE)
    for g in spec["groups"]:
        for run_id, calls in g.get("calls", {}).items():
            d = os.path.join(FAKE_CASE, "queries", "round2", run_id)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "calls.jsonl"), "w", encoding="utf-8", newline="\n") as f:
                for c in calls:
                    f.write(json.dumps(c) + "\n")
    return FAKE_CASE


def run(spec, out_dir=None):
    out = out_dir or REH
    _fake_case(spec)
    c = contract_mod.load(os.path.join(c2paths.RULES, "contract.json"))
    report, all_ok, passed = ["# 预演结果（rehearse.py run）", ""], True, set()
    for g in spec["groups"]:
        d = os.path.join(out, g["name"])
        probs = []
        units = extract_group(g)
        if [u["ctx_requested"] for u in units] != [r["ctx_requested"] for r in g["requests"]] or \
           [u["priority"] for u in units] != [r.get("priority") for r in g["requests"]]:
            probs.append(f"extraction: got {[(u['ctx_requested'], u['priority']) for u in units]}")
        alloc = allocate_group(g, c)
        dropped = [f"{x['qid']} {x['ctx']}" for x in alloc["dropped"]]
        if dropped != g["budget_dropped"]:
            probs.append(f"budget: dropped {dropped}, expected {g['budget_dropped']}")
        claims = read_tsv(os.path.join(d, "claims_rehearsal.tsv"))
        ev = read_tsv(os.path.join(d, "evidence_map_rehearsal.tsv")) if os.path.exists(os.path.join(d, "evidence_map_rehearsal.tsv")) else []
        probs += ["claims: " + p for p in cs.problems(claims, ev, case=FAKE_CASE)]
        expected = {(r["round"], r["field"], r["proposition"]): r for r in read_tsv(os.path.join(d, "expected.tsv"))}
        for r in claims:
            e = expected.get((r["round"], r["field"], r["proposition"]))
            if e is None:
                probs.append(f"expected.tsv has no row for {r['round']}/{r['field']}/{r['proposition']}")
                continue
            for col in ("value", "judgments", "evidence_level", "attribution", "r2_action"):
                if (r.get(col) or "") != (e.get(col) or ""):
                    probs.append(f"{r['round']}/{r['field']}/{r['proposition']} {col}: claims {r.get(col)!r} vs expected {e.get(col)!r}")
        ok = not probs
        all_ok &= ok
        if ok:
            passed.add(g["name"])
        report.append(f"- {g['name']}: {'PASS' if ok else 'FAIL'}" + ("" if ok else "\n  - " + "\n  - ".join(probs)))
    hits = set()
    for g in spec["groups"]:
        if g["name"] in passed:
            hits |= group_targets(g)
    missing = [t for t in coverage_targets() if t not in hits]
    if missing:
        all_ok = False
        report.append("- coverage: targets without a passing group: " + ", ".join(f"{k}:{v}" for k, v in missing))
    else:
        report.append(f"- coverage: all {len(coverage_targets())} targets hit by a passing group")
    report.append("")
    report.append("RESULT: " + ("PASS" if all_ok else "FAIL"))
    text = "\n".join(report) + "\n"
    with open(os.path.join(out, "result.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return all_ok, text


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in ("generate", "run"):
        print("usage: rehearse.py generate | run")
        return 2
    spec = load_spec()
    if argv[0] == "generate":
        out = generate(spec)
        print(f"REHEARSAL GENERATED: {len(spec['groups'])} groups -> {os.path.relpath(out, c2paths.CASE)}")
        return 0
    ok, text = run(spec)
    print(text, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
