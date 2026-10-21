"""Round-2 coverage table, corrected / wrong predictions and disappearing failure conditions of CASE-01 stage B
(implementation plan Task 7; protocol v0.4 section 10.4). Pure Python (standard library); no subprocess; Windows and
WSL.

Coverage rows (revise/predictions/r2_coverage.jsonl; view r2_coverage.tsv by judge.py views 2):
  {row_type, r1_ref, r2_ref, candidate_r1, candidate_r2, action, same_object, same_criterion, link_basis}
  r1_ref / r2_ref name a criteria row of candidate_r1 (round 1) / candidate_r2 (round 2): its prediction_id
  (prediction rows) or fc_id (failure-condition rows); "" when absent. same_object / same_criterion are true / false
  on rows with both references, null otherwise. action: keep modify withdraw new not_mentioned.

validate(r1_rows, r2_rows, coverage_rows, prev=None) -> problems (empty: valid). prev: {candidate_r2: candidate_r1}
  or a callable; default: mapping.prev_code(mapping.load(2), candidate_r2).

compute(case=None, check=False, prev=None) writes revise/predictions/r2_coverage_result.json from the criteria,
  the judgments of both rounds, the coverage table and the round-2 status.json / compare documents:
  - predictions (keep / modify, same_object true): round-1 反对 -> round-2 支持 预测改对; 支持 -> 反对 预测改错;
    anything else 无变化或不可比. Object changes (new + not_mentioned / withdraw) are not compared.
  - failure conditions judged 触发 in round 1: the round-1 expression evaluated on the round-2 candidate of the same
    model (whatever round 2 says about it): false 消失, true 仍在, unknown indeterminate; a round-2 candidate that is
    declined / unavailable, or without status.json, is indeterminate.
  - action counts per row type (withdraw is counted on its own, never as corrected).
  check=True recomputes and compares bytes with the existing file ('CHECK FAIL ...'), writes nothing.
  Prints 'COVERAGE FAIL: ...' (nothing written) when an input is invalid. Returns 0 or 1.

Command line:  python3 -B revise/scripts/coverage.py compute [--check]"""
import json
import os
import sys
from decimal import Decimal, InvalidOperation

import judge
import revpaths as rp

COVERAGE_COLUMNS = ("row_type", "r1_ref", "r2_ref", "candidate_r1", "candidate_r2", "action", "same_object",
                    "same_criterion", "link_basis")
ACTIONS = ("keep", "modify", "withdraw", "new", "not_mentioned")
OBJECT_FIELDS = ("metric", "check", "corner", "category", "value_kind")
CRITERION_FIELDS = ("direction", "low", "high", "unit", "point", "epsilon", "comparator")
ROW_TYPES = ("prediction", "failure_condition")
OUTCOMES = ("预测改对", "预测改错", "无变化或不可比")
FC_OUTCOMES = ("消失", "仍在", "indeterminate")
NO_CANDIDATE = ("declined", "unavailable")


def _norm(v):
    """Field value for the same_criterion comparison: a finite decimal by value, else the stripped text."""
    s = v.strip() if isinstance(v, str) else v
    if isinstance(s, str):
        try:
            d = Decimal(s)
            if d.is_finite():
                return ("num", d)
        except InvalidOperation:
            pass
    return ("text", s)


def canonical_expr(expr):
    return json.dumps(expr, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def same_object(a, b):
    return all((a.get(k) or "").strip() == (b.get(k) or "").strip() for k in OBJECT_FIELDS)


def same_criterion(a, b):
    if a.get("row_type") == "failure_condition":
        return canonical_expr(a.get("expr")) == canonical_expr(b.get("expr"))
    return all(_norm(a.get(k)) == _norm(b.get(k)) for k in CRITERION_FIELDS)


def _prev_fn(prev):
    return judge.prev_fn(prev, 2)


def _index(rows, label, probs):
    idx = {}
    for r in rows:
        key = (r.get("candidate"), judge.ref_of(r))
        if key in idx:
            probs.append(f"COVERAGE: {label} reference {key[1]!r} of {key[0]} is not unique")
        idx[key] = r
    return idx


def validate(r1_rows, r2_rows, coverage_rows, prev=None):
    probs = []
    try:
        prev_of = _prev_fn(prev)
    except Exception as e:                                 # mapping.MappingError and file errors
        return [f"COVERAGE: the round-2 mapping cannot be loaded ({e})"]
    i1 = _index(r1_rows, "round-1", probs)
    i2 = _index(r2_rows, "round-2", probs)
    used1, used2 = {}, {}
    for n, c in enumerate(coverage_rows, 1):
        w = f"coverage row {n}"
        if not isinstance(c, dict) or list(c) != list(COVERAGE_COLUMNS):
            probs.append(f"{w}: fields must be exactly, in order: {' '.join(COVERAGE_COLUMNS)}")
            continue
        rt, act, r1, r2 = c["row_type"], c["action"], c["r1_ref"], c["r2_ref"]
        if rt not in ROW_TYPES:
            probs.append(f"{w}: row_type {rt!r} is not prediction / failure_condition")
            continue
        if act not in ACTIONS:
            probs.append(f"{w}: action {act!r} is not one of {' '.join(ACTIONS)}")
            continue
        if not all(isinstance(c[k], str) for k in ("r1_ref", "r2_ref", "candidate_r1", "candidate_r2",
                                                   "link_basis")):
            probs.append(f"{w}: r1_ref r2_ref candidate_r1 candidate_r2 link_basis must be strings")
            continue
        c1, c2 = c["candidate_r1"], c["candidate_r2"]
        try:
            p = prev_of(c2) if c2 else None
        except Exception as e:
            p = None
            probs.append(f"{w}: candidate_r2 {c2!r} is not in the round-2 mapping ({e})")
        if not c1 or not c2 or p != c1:
            probs.append(f"{w}: candidate_r1 {c1!r} is not the previous code of candidate_r2 {c2!r} "
                         f"(mapping.prev_code(2, candidate_r2) must equal candidate_r1)")
        # legal empty-reference combinations
        if act == "new":
            ok = r1 == "" and r2 != ""
        elif act in ("not_mentioned", "withdraw"):
            ok = r1 != "" and r2 == ""
        else:
            ok = r1 != "" and r2 != ""
        if not ok:
            probs.append(f"{w}: action {act} has an illegal empty-ref combination r1_ref={r1!r} r2_ref={r2!r} "
                         f"(new: r1_ref empty, r2_ref set; not_mentioned / withdraw: r1_ref set, r2_ref empty; "
                         f"keep / modify: both set)")
        row1 = row2 = None
        if r1:
            row1 = i1.get((c1, r1))
            if row1 is None:
                probs.append(f"{w}: r1_ref {r1!r} names no round-1 criteria row of {c1} (dangling)")
            elif row1["row_type"] != rt:
                probs.append(f"{w}: r1_ref {r1!r} is a {row1['row_type']} row, not row_type {rt}")
                row1 = None
            used1.setdefault((c1, r1), []).append(n)
        if r2:
            row2 = i2.get((c2, r2))
            if row2 is None:
                probs.append(f"{w}: r2_ref {r2!r} names no round-2 criteria row of {c2} (dangling)")
            elif row2["row_type"] != rt:
                probs.append(f"{w}: r2_ref {r2!r} is a {row2['row_type']} row, not row_type {rt}")
                row2 = None
            elif row2.get("r1_ref") and row2["r1_ref"] != r1:
                probs.append(f"{w}: round-2 row {r2!r} has r1_ref {row2['r1_ref']!r}, the coverage row {r1!r}")
            used2.setdefault((c2, r2), []).append(n)
        so, sc = c["same_object"], c["same_criterion"]
        if not (r1 and r2):
            if so is not None or sc is not None:
                probs.append(f"{w}: same_object / same_criterion must be null on a row without both references")
            continue
        if not isinstance(so, bool):
            probs.append(f"{w}: same_object must be true or false")
        if not isinstance(sc, bool):
            probs.append(f"{w}: same_criterion must be true or false")
        if row1 is None or row2 is None:
            continue
        crit = same_criterion(row1, row2)
        if isinstance(sc, bool) and sc != crit:
            probs.append(f"{w}: same_criterion is {sc}, the recomputed value is {crit}")
        if rt == "prediction":
            obj = same_object(row1, row2)
            if isinstance(so, bool) and so != obj:
                probs.append(f"{w}: same_object is {so}, the recomputed value is {obj} (object fields "
                             f"{' '.join(OBJECT_FIELDS)})")
            if not obj:
                probs.append(f"{w}: the object changed ({' '.join(OBJECT_FIELDS)}); this must be new plus "
                             f"not_mentioned / withdraw, not {act}")
            elif act == "keep" and not crit:
                probs.append(f"{w}: keep needs the same criterion ({' '.join(CRITERION_FIELDS)}); this is modify")
            elif act == "modify" and crit:
                probs.append(f"{w}: modify needs a changed criterion; the criterion is the same, this is keep")
        else:
            if so is not True:
                probs.append(f"{w}: a failure-condition {act} needs same_object true (author-confirmed link); "
                             f"otherwise new plus not_mentioned / withdraw")
            if not c["link_basis"].strip():
                probs.append(f"{w}: link_basis must give the basis of the author-confirmed failure-condition link")
            if act == "keep" and not crit:
                probs.append(f"{w}: keep needs the same expr (canonical JSON); the expr changed, this is modify")
            elif act == "modify" and crit:
                probs.append(f"{w}: modify needs a changed expr; the expr is the same, this is keep")
    for (c1, r1), row in i1.items():
        k = len(used1.get((c1, r1), []))
        if k != 1:
            probs.append(f"COVERAGE: round-1 row {r1!r} of {c1} has {k} coverage rows (exactly 1 required)")
    for (c2, r2), row in i2.items():
        k = len(used2.get((c2, r2), []))
        if k != 1:
            probs.append(f"COVERAGE: round-2 row {r2!r} of {c2} appears in {k} coverage rows (exactly 1 required)")
    return probs


# ------------------------------------------------------------------------------------------------- compute
def _paths(case):
    pred = os.path.join(case, "revise", "predictions")
    return {"coverage": os.path.join(pred, "r2_coverage.jsonl"),
            "j1": os.path.join(pred, "r1_judgments.jsonl"),
            "j2": os.path.join(pred, "r2_judgments.jsonl"),
            "c1": os.path.join(pred, "r1_criteria.jsonl"),
            "c2": os.path.join(pred, "r2_criteria.jsonl"),
            "result": os.path.join(pred, "r2_coverage_result.json")}


def result_doc(case, prev=None):
    p = _paths(case)
    r1 = judge.read_jsonl(p["c1"])
    r2 = judge.read_jsonl(p["c2"])
    cov = judge.read_jsonl(p["coverage"])
    probs = validate(r1, r2, cov, prev=prev)
    if probs:
        raise judge.JudgeError("; ".join(probs))
    j1 = {(r.get("candidate"), judge.ref_of(r)): r for r in judge.read_jsonl(p["j1"])}
    j2 = {(r.get("candidate"), judge.ref_of(r)): r for r in judge.read_jsonl(p["j2"])}
    for label, crit, js in (("r1", r1, j1), ("r2", r2, j2)):
        missing = [judge.ref_of(r) for r in crit if (r["candidate"], judge.ref_of(r)) not in js]
        if missing:
            raise judge.JudgeError(f"{label}_judgments.jsonl lacks rows {missing}")

    actions = {rt: {a: 0 for a in ACTIONS} for rt in ROW_TYPES}
    pcounts = {o: 0 for o in OUTCOMES}
    precs = []
    for c in cov:
        actions[c["row_type"]][c["action"]] += 1
        if c["row_type"] != "prediction" or c["action"] not in ("keep", "modify") or c["same_object"] is not True:
            continue
        a = j1[(c["candidate_r1"], c["r1_ref"])]["judgment"]
        b = j2[(c["candidate_r2"], c["r2_ref"])]["judgment"]
        outcome = "预测改对" if (a, b) == ("反对", "支持") else "预测改错" if (a, b) == ("支持", "反对") else "无变化或不可比"
        pcounts[outcome] += 1
        precs.append({"r1_ref": c["r1_ref"], "r2_ref": c["r2_ref"], "candidate_r1": c["candidate_r1"],
                      "candidate_r2": c["candidate_r2"], "action": c["action"], "r1_judgment": a,
                      "r2_judgment": b, "outcome": outcome})

    fcounts = {o: 0 for o in FC_OUTCOMES}
    frecs = []
    by_r1 = {(c["candidate_r1"], c["r1_ref"]): c for c in cov if c["r1_ref"]}
    cands = {}
    for r in r1:
        if r["row_type"] != "failure_condition":
            continue
        if j1[(r["candidate"], r["fc_id"])]["judgment"] != "触发":
            continue
        c = by_r1[(r["candidate"], r["fc_id"])]
        code2 = c["candidate_r2"]
        if code2 not in cands:
            try:
                cands[code2] = judge.load_candidate(case, 2, code2)
            except judge.JudgeError as e:
                cands[code2] = e
        got = cands[code2]
        evidence, value = [], None
        if isinstance(got, judge.JudgeError):
            outcome, why = "indeterminate", f"第 2 轮候选的结果不可用：{got}"
        else:
            st, mx, files = got
            state = st.get("state") if isinstance(st, dict) else None
            evidence.append({"file": files["status"], "field": "state"})
            if state in NO_CANDIDATE:
                outcome, why = "indeterminate", f"第 2 轮没有候选（{state}）"
            else:
                value, ev = judge.eval3_with_evidence(r["expr"], st, mx)
                for label, field in ev:
                    item = {"file": files[label], "field": field}
                    if item not in evidence:
                        evidence.append(item)
                outcome = {False: "消失", True: "仍在", None: "indeterminate"}[value]
                why = "第 1 轮原表达式在第 2 轮候选结果上的三值结果为" + {True: "真", False: "假", None: "未知"}[value]
        fcounts[outcome] += 1
        frecs.append({"r1_ref": r["fc_id"], "candidate_r1": r["candidate"], "candidate_r2": code2,
                      "action": c["action"], "r2_ref": c["r2_ref"], "text": r["text"], "expr": r["expr"],
                      "outcome": outcome, "reason": why, "evidence": evidence})
    return {"predictions": {"counts": pcounts, "records": precs},
            "failure_conditions": {"counts": fcounts, "records": frecs},
            "actions": actions}


def compute(case=None, check=False, prev=None):
    case = case or rp.CASE
    try:
        doc = result_doc(case, prev=prev)
    except (judge.JudgeError, rp.RevpathsError) as e:
        print(f"COVERAGE FAIL: {e}", flush=True)
        return 1
    data = (json.dumps(doc, indent=1, ensure_ascii=False, default=judge._dec_out) + "\n").encode("utf-8")
    path = _paths(case)["result"]
    if check:
        try:
            same = rp.read_bytes(path) == data
        except OSError:
            same = False
        if not same:
            print("CHECK FAIL: revise/predictions/r2_coverage_result.json differs from the recomputed content",
                  flush=True)
            return 1
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    if args != ["compute"]:
        print("usage: coverage.py compute [--check]", file=sys.stderr)
        return 2
    return compute(check=check)


if __name__ == "__main__":
    sys.exit(main())
