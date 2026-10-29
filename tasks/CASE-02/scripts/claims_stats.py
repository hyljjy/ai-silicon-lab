"""Validate claims.tsv / evidence_map.tsv and count labels for the notes (protocol v0.3 sections 5.5, 7, 11, 12).
Copied in structure from tasks/CASE-01/diag/scripts/claims_stats.py (rules/copied_from.tsv); the validation is
rewritten for the CASE-02 fields.
  python3 -B scripts/claims_stats.py [--claims claims.tsv] [--evidence evidence_map.tsv] [--mapping outputs/mapping.json]
                                     [--out stats.md]
claims.tsv columns (tab separated, '#' lines are comments), one row per judgement:
  id code round field proposition location quote scope_claimed value evidence_level judgments attribution query_ids
  evidence author_label review_status dissent note parent_id r1_ref r2_action
field: F1..F8 (core table), fact / cite (key facts and their citations), ROUND (a whole model-round that was not
obtained: value 未取得 / 不可评价 with the reason in note). Rules (rules/scoring.md):
  * a completed model-round has every field F1..F8 once, F3 three times (one per proposition, each with scope_claimed);
  * values per field per round (FIELD_VALUES); F2 has exactly four values, contradictions go to judgments;
  * F8 is 不适用 in round 1; in round 2 不适用 needs the reason in note;
  * judgments are the labels of the decision table (JUDGMENTS), ';'-separated, listed as given and never summed;
  * 查询任务未完成 or an unobtained value needs an attribution; review_status 有分歧 needs dissent;
  * at most 10 facts per model-round, each with exactly one cite row;
  * evidence_map rows: the call they cite must exist, be ok, and its complete flag must match (no whole-instance gate).
The final value is author_label when the author changed it, else value. Counts are per code (or per model with
--mapping), per round, per field / proposition, always with denominators; no totals, no ranking."""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2paths import CASE  # noqa: E402

COLUMNS = ["id", "code", "round", "field", "proposition", "location", "quote", "scope_claimed", "value", "evidence_level",
           "judgments", "attribution", "query_ids", "evidence", "author_label", "review_status", "dissent", "note",
           "parent_id", "r1_ref", "r2_action"]
EVIDENCE_COLUMNS = ["code", "round", "port", "item", "ctx", "scene", "run_id", "call_seq", "returned_range", "element_row",
                    "complete", "mapping_rule", "review_status", "dissent"]
FIELDS = ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8")
PROPOSITIONS = ("报告差异", "原因", "范围")
UNOBTAINED = "未取得 / 不可评价"
FIELD_VALUES = {
    "F1": {"1": ["电路性能改善", "确认约束缺失", "确认其他原因", "尚不能确认", "表述矛盾"]},
    "F2": {"1": ["确认", "假设", "条件成立时才确认", "原话不足以判定"]},
    "F3": {"1": ["充分", "不足", "原话无法判定"]},
    "F4": {"1": ["未定位", "部分端口", "端口集合完整、缺失项未分清", "完整端口集合及缺失项"]},
    "F5": {"1": ["是", "否"]},
    "F6": {"1": ["是", "部分", "否", "待执行核实"]},
    "F7": {"1": ["原理上能", "否"], "2": ["线索", "名单级", "现象级", "局部确认", "目标集合完整", "未取得"]},
    "F8": {"1": ["不适用"], "2": ["单独标记", "当成通过", "忽略", "处理不一致", "不适用"]},
}
JUDGMENTS = ["合理观察", "合理假设", "原因碰巧正确，证据不足、确定性过强", "误判", "证据不足、确定性过强（原因不符）", "范围超出证据",
             "判断合理", "查询任务未完成", "完成名单级诊断", "完成现象级诊断", "未利用充分证据：未识别现象",
             "未利用充分证据：已识别现象未下结论", "完成局部诊断", "完成本次诊断", "证据充分、未下结论", "表述矛盾", "-"]
ATTRIBUTIONS = ["请求本身的问题", "流程限制：单实例截断", "流程限制：时限", "流程限制：输出上限", "流程限制：白名单拒绝",
                "流程限制：总预算", "流程限制：Tcl 命令计数上限", "执行器或环境问题", "原因未定", "-"]
EVIDENCE_LEVELS = ["线索", "名单级", "现象级", "局部确认", "目标集合完整", "未取得", "-"]
FACT_LABELS = {"证实", "推翻", "无法核对"}
CITE_LABELS = {"引用正确", "引用错误", "无引用"}
REVIEW = {"已复核", "未复核", "有分歧"}
ACTIONS = ("没有再提", "保持", "提高确定程度", "降低确定程度", "修改结论", "明确撤回")
MAX_FACTS = 10
MATERIAL = re.compile(r"package/([\w.-]+):(\d+)(?:-(\d+))?")


def load(path, columns=COLUMNS):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t", quoting=csv.QUOTE_NONE))
    if rows and list(rows[0].keys()) != columns:
        raise SystemExit(f"CLAIMS FAIL: columns must be {columns}")
    return rows


def final(r):
    return (r.get("author_label") or "").strip() or (r.get("value") or "").strip()


def _allowed(field, rnd):
    v = FIELD_VALUES[field]
    return v.get(rnd) or v["1"]


def _calls(case, run_id):
    p = os.path.join(case, "queries", "round2", run_id, "calls.jsonl")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return {c["call_seq"]: c for c in (json.loads(l) for l in f if l.strip())}


def problems(rows, evidence_rows=(), case=CASE):
    out, seen = [], set()
    by_id = {r["id"]: r for r in rows}
    children = Counter(r["parent_id"] for r in rows if r["field"] == "cite")
    rounds = defaultdict(list)
    for r in rows:
        rounds[(r["code"], r["round"])].append(r)
    for (code, rnd), rs in sorted(rounds.items()):
        unobtained = [r for r in rs if r["field"] == "ROUND"]
        if unobtained:
            for r in unobtained:
                if final(r) != UNOBTAINED:
                    out.append(f"{r['id']}: ROUND row value must be {UNOBTAINED!r}")
                if not r["note"].strip():
                    out.append(f"{r['id']}: ROUND row needs the reason in note")
                if r["attribution"] not in ATTRIBUTIONS or r["attribution"] == "-":
                    out.append(f"{r['id']}: ROUND row needs an attribution")
            if [r for r in rs if r["field"] in FIELDS]:
                out.append(f"{code} round {rnd}: has both ROUND (unobtained) and field rows")
            continue
        present = Counter(r["field"] for r in rs if r["field"] in FIELDS)
        for f in FIELDS:
            want = 3 if f == "F3" else 1
            if present.get(f, 0) != want:
                out.append(f"{code} round {rnd}: field {f} appears {present.get(f, 0)} times, expected {want}")
        props = sorted(r["proposition"] for r in rs if r["field"] == "F3")
        if present.get("F3") and props != sorted(PROPOSITIONS):
            out.append(f"{code} round {rnd}: F3 propositions are {props}, expected one each of {list(PROPOSITIONS)}"
                       + ("" if "范围" in props else " (范围 missing)"))
        facts = [r for r in rs if r["field"] == "fact"]
        if len(facts) > MAX_FACTS:
            out.append(f"{code} round {rnd}: {len(facts)} facts, at most {MAX_FACTS}")
    for r in rows:
        rid, val = r["id"], final(r)
        if rid in seen:
            out.append(f"{rid}: duplicate id")
        seen.add(rid)
        if not re.fullmatch(r"[A-Z]", r["code"]) or r["round"] not in ("1", "2"):
            out.append(f"{rid}: bad code or round")
        if r["review_status"] not in REVIEW:
            out.append(f"{rid}: review_status must be one of {sorted(REVIEW)}")
        if r["review_status"] == "有分歧" and not r["dissent"].strip():
            out.append(f"{rid}: 有分歧 needs dissent")
        judg = [j.strip() for j in (r["judgments"] or "-").split(";") if j.strip()]
        for j in judg:
            if j not in JUDGMENTS:
                out.append(f"{rid}: judgments label {j!r} is not in the decision table")
        if r["attribution"] not in ATTRIBUTIONS:
            out.append(f"{rid}: attribution {r['attribution']!r} unknown")
        if r["evidence_level"] not in EVIDENCE_LEVELS:
            out.append(f"{rid}: evidence_level {r['evidence_level']!r} unknown")
        if ("查询任务未完成" in judg or val == "未取得") and r["attribution"] in ("-", ""):
            out.append(f"{rid}: 查询任务未完成 / 未取得 needs an attribution")
        if r["field"] in FIELDS:
            if val not in _allowed(r["field"], r["round"]):
                out.append(f"{rid}: {r['field']} value {val!r} not allowed in round {r['round']}")
            if r["field"] == "F3":
                if r["proposition"] not in PROPOSITIONS:
                    out.append(f"{rid}: F3 needs a proposition")
                if r["scope_claimed"].strip() in ("", "-"):
                    out.append(f"{rid}: F3 needs scope_claimed")
            elif r["proposition"] not in ("-", ""):
                out.append(f"{rid}: only F3 rows carry a proposition")
            if r["field"] == "F8" and r["round"] == "2" and val == "不适用" and not r["note"].strip():
                out.append(f"{rid}: F8 不适用 in round 2 needs the reason in note")
        elif r["field"] == "fact":
            if val not in FACT_LABELS:
                out.append(f"{rid}: fact label {val!r}")
            if children[rid] != 1:
                out.append(f"{rid}: a fact needs exactly one 证据引用 (cite) row (found {children[rid]})")
            for name, first, last in MATERIAL.findall(r["evidence"]):
                path = os.path.join(case, "package", name)
                if os.path.isfile(path):
                    with open(path, encoding="utf-8") as f:
                        n = len(f.read().splitlines())
                    if not 1 <= int(first) <= int(last or first) <= n:
                        out.append(f"{rid}: evidence package/{name}:{first} is not a line range of the package file")
        elif r["field"] == "cite":
            if val not in CITE_LABELS:
                out.append(f"{rid}: cite label {val!r}")
            if by_id.get(r["parent_id"], {}).get("field") != "fact":
                out.append(f"{rid}: parent_id must name a fact row")
        elif r["field"] != "ROUND":
            out.append(f"{rid}: unknown field {r['field']!r}")
        if r["round"] == "2" and r["field"] in FIELDS + ("fact",):
            if r["r2_action"] not in ACTIONS:
                out.append(f"{rid}: r2_action must be one of {list(ACTIONS)}")
            elif r["r2_action"] not in ("没有再提",) and r["r1_ref"] and by_id.get(r["r1_ref"], {}).get("round") != "1":
                out.append(f"{rid}: r1_ref must name a round-1 row")
    for i, e in enumerate(evidence_rows, 1):
        tag = f"evidence_map row {i} ({e.get('port')} {e.get('item')})"
        if e.get("review_status") not in REVIEW:
            out.append(f"{tag}: review_status")
        if e.get("review_status") == "有分歧" and not (e.get("dissent") or "").strip():
            out.append(f"{tag}: dissent")
        calls = _calls(case, e.get("run_id", ""))
        if calls is None:
            out.append(f"{tag}: run {e.get('run_id')} is not a collected instance")
            continue
        try:
            call = calls.get(int(e.get("call_seq", "0")))
        except ValueError:
            call = None
        if call is None:
            out.append(f"{tag}: call_seq {e.get('call_seq')} not in calls.jsonl")
            continue
        if call.get("status") != "ok":
            out.append(f"{tag}: call {e.get('call_seq')} status is {call.get('status')} (error / unfinished calls are not evidence)")
        if (str(e.get("complete")) in ("1", "True", "true")) != bool(call.get("complete")):
            out.append(f"{tag}: complete flag {e.get('complete')} does not match calls.jsonl ({call.get('complete')})")
    return out


def stats(rows, evidence_rows=(), names=None):
    names = names or {}
    who = lambda r: names.get(r["code"], r["code"])
    lines = ["# 核心表统计（规程 v0.3 第 7 节；只列分母和条数，不汇总成一个数、不排序；并列判定按行列出、不相加）", "",
             "| 对象 | 轮次 | 字段 | 命题 | 取值 | 判定（并列） | 证据层次 | 归因 | 复核状态 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (who(r), r["round"], r["field"], r["proposition"], r["id"])):
        if r["field"] in FIELDS or r["field"] == "ROUND":
            lines.append(f"| {who(r)} | {r['round']} | {r['field']} | {r['proposition']} | {final(r)} | {r['judgments']} | "
                         f"{r['evidence_level']} | {r['attribution']} | {r['review_status']} |")
    denom = defaultdict(Counter)
    for r in rows:
        if r["field"] in FIELDS:
            denom[(who(r), r["round"])]["字段行"] += 1
        elif r["field"] == "fact":
            denom[(who(r), r["round"])]["事实"] += 1
        elif r["field"] == "cite":
            denom[(who(r), r["round"])]["引用"] += 1
    lines += ["", "| 对象 | 轮次 | 分母：字段行 | 事实 | 引用 |", "|---|---|---|---|---|"]
    for (w, rnd), c in sorted(denom.items()):
        lines.append(f"| {w} | {rnd} | {c['字段行']} | {c['事实']} | {c['引用']} |")
    cross = defaultdict(Counter)
    for r in rows:
        if r["field"] == "F7" and r["round"] == "2":
            cross[who(r)][(final(r), r["attribution"])] += 1
    lines += ["", "| 对象 | F7 证据层次 × 归因 | 条数 |", "|---|---|---|"]
    for w, c in sorted(cross.items()):
        lines += [f"| {w} | {lvl} × {att} | {n} |" for (lvl, att), n in sorted(c.items())]
    rev = Counter(r["review_status"] for r in rows)
    ev_rev = Counter(e.get("review_status", "") for e in evidence_rows)
    changed = sum(1 for r in rows if r["author_label"].strip() and r["author_label"].strip() != r["value"].strip())
    lines += ["", f"- 复核状态（核心表与事实、引用行）：" + "；".join(f"{k} {v}" for k, v in sorted(rev.items())) + f"，共 {sum(rev.values())} 行",
              f"- 复核状态（证据对应表）：" + ("；".join(f"{k} {v}" for k, v in sorted(ev_rev.items())) or "无") + f"，共 {sum(ev_rev.values())} 行",
              f"- 作者改动的取值：{changed} / {len(rows)}"]
    return "\n".join(lines) + "\n"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", default=os.path.join(CASE, "claims.tsv"))
    ap.add_argument("--evidence", default=os.path.join(CASE, "evidence_map.tsv"))
    ap.add_argument("--mapping")
    ap.add_argument("--out", default=os.path.join(CASE, "stats.md"))
    args = ap.parse_args(argv)
    rows = load(args.claims)
    ev = load(args.evidence, EVIDENCE_COLUMNS) if os.path.exists(args.evidence) else []
    bad = problems(rows, ev)
    for p in bad:
        print(f"CLAIMS {p}")
    if bad:
        print(f"CLAIMS FAIL: {len(bad)} problem(s)")
        return 1
    names = None
    if args.mapping:
        with open(args.mapping, encoding="utf-8") as f:
            names = json.load(f)["codes"]
    text = stats(rows, ev, names)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
