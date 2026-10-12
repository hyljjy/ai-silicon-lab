"""Validate diag/claims.tsv and count labels for the article (protocol v0.5 sections 6, 7.3, 8 and 9).

  python3 -B diag/scripts/claims_stats.py [--mapping diag/outputs/mapping.json] [--out diag/stats.md]

claims.tsv columns (tab-separated, one row per judgement, '#' lines are comments):
  id code round location quote type_initial type retype_reason falsifier_given condition query_ids label evidence
  author_label note parent_id r1_ref r2_action
Rules checked (besides allowed values):
  * every 事实 row has exactly one 证据引用 row whose parent_id is the fact's id ("-" quote and 无引用 when the model
    gave no citation); every 证据引用 row points to a 事实 row;
  * every run in query_ids of a 证实 or 支持 row is a collected run (diag/queries/<group>/<id>/result.json) with
    env_ok true, query_status completed, codes exactly [已执行] (frozen model) or [改变冻结模型的查询…] (whatif run),
    and (strict runs) a clean query log; a 事实 may not rest on a whatif run (protocol 8 h); 支持 needs query_ids;
  * a 事实 labelled 证实 or 推翻 needs query_ids, or evidence citing the materials as package/<file>:<line>[-<line>]
    (query_ids "-"): a fact whose content is the material text itself (protocol 7.3); every such citation must name
    lines that exist in diag/package/<file>;
  * 未判定 needs a reason in note; a retyped row needs retype_reason;
  * round-2 rows carry r2_action 保持|修改|撤回|新增, and r1_ref (a round-1 id) unless 新增.
The final label is author_label when the author changed it, else label. Counts are per code (or per model with
--mapping), per round, per type and per final label, always with their denominators; no totals across models.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagpaths import DIAG  # noqa: E402

COLUMNS = ["id", "code", "round", "location", "quote", "type_initial", "type", "retype_reason", "falsifier_given",
           "condition", "query_ids", "label", "evidence", "author_label", "note", "parent_id", "r1_ref", "r2_action"]
TYPES = ("事实", "假设", "证据引用", "缺失证据", "查询", "修改建议")
RESULT_CODES = {"已执行", "语法错误", "对象不存在", "改变冻结模型的查询（已在单独运行中执行）", "环境已由冻结环境提供，未执行",
                "工具异常退出", "未执行：未指明可执行的对象或命令", "需要模型外数据"}
LABELS = {
    "事实": {"证实", "推翻", "无法核对"},
    "假设": {"支持", "反对", "未判定", "需阶段 B"},
    "证据引用": {"引用正确", "引用错误", "无引用"},
    "缺失证据": {"材料中已有", "可执行", "模型外"},
    "查询": {"已记录"} | RESULT_CODES,
    "修改建议": {"违反题目要求", "与合同冲突", "留给阶段 B"},
}
ACTIONS = {"保持", "修改", "撤回", "新增"}
CODE_WHATIF = "改变冻结模型的查询（已在单独运行中执行）"
MATERIAL = re.compile(r"package/([\w.-]+):(\d+)(?:-(\d+))?")


def load(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"))
    if rows and list(rows[0].keys()) != COLUMNS:
        raise SystemExit(f"CLAIMS FAIL: columns must be {COLUMNS}")
    return rows


def final(r):
    return r["author_label"].strip() or r["label"].strip()


def material_ok(diag, name, first, last):
    """package/<name>:<first>-<last> names lines that exist in a materials-package file."""
    path = os.path.join(diag, "package", name)
    if not os.path.isfile(path) or not 1 <= first <= last:
        return False
    with open(path, encoding="utf-8") as f:
        return last <= len(f.read().splitlines())


def run_result(qid, diag):
    """result.json of a collected run, searched in every diag/queries/<group>/."""
    qdir = os.path.join(diag, "queries")
    for group in sorted(os.listdir(qdir)) if os.path.isdir(qdir) else []:
        p = os.path.join(qdir, group, qid, "result.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return None


def problems(rows, diag=DIAG):
    out, seen = [], set()
    by_id = {r["id"]: r for r in rows}
    children = Counter(r["parent_id"] for r in rows if r["type"] == "证据引用")
    for r in rows:
        rid, lab = r["id"], final(r)
        if rid in seen:
            out.append(f"{rid}: duplicate id")
        seen.add(rid)
        if r["code"] not in ("A", "B", "C") or r["round"] not in ("1", "2"):
            out.append(f"{rid}: bad code or round")
        if r["type"] not in TYPES or r["type_initial"] not in TYPES:
            out.append(f"{rid}: bad type")
        if r["type"] != r["type_initial"] and not r["retype_reason"].strip():
            out.append(f"{rid}: retyped without a reason")
        if r["type"] in LABELS and lab and lab not in LABELS[r["type"]]:
            out.append(f"{rid}: label {lab!r} not allowed for type {r['type']}")
        if r["type"] == "假设" and r["falsifier_given"] not in ("是", "否"):
            out.append(f"{rid}: falsifier_given must be 是 or 否")
        if r["type"] == "事实" and children[rid] != 1:
            out.append(f"{rid}: a fact needs exactly one 证据引用 row (found {children[rid]})")
        if r["type"] == "证据引用" and by_id.get(r["parent_id"], {}).get("type") != "事实":
            out.append(f"{rid}: parent_id must name a 事实 row")
        if lab == "未判定" and not r["note"].strip():
            out.append(f"{rid}: 未判定 needs the reason in note")
        qids = [q.strip() for q in r["query_ids"].split(",") if q.strip() and q.strip() != "-"]
        cites = MATERIAL.findall(r["evidence"])
        for name, first, last in cites:
            if not material_ok(diag, name, int(first), int(last or first)):
                out.append(f"{rid}: evidence package/{name}:{first}{'-' + last if last else ''} is not a line range "
                           "of a package file")
        if lab in ("证实", "推翻") and r["type"] == "事实" and not qids and not cites:
            out.append(f"{rid}: {lab} needs query_ids or a package/<file>:<line> citation in evidence")
        if lab == "支持" and not qids:
            out.append(f"{rid}: 支持 without query_ids")
        if lab in ("证实", "支持"):
            for q in qids:
                res = run_result(q, diag)
                if res is None:
                    out.append(f"{rid}: query {q} is not a collected run")
                    continue
                want = [CODE_WHATIF] if res.get("mode") == "whatif" else ["已执行"]
                if not (res.get("env_ok") and res.get("query_status") == "completed" and res.get("codes") == want
                        and (res.get("query_log_ok") or not res.get("strict_log"))):
                    out.append(f"{rid}: query {q} does not meet the minimum conditions of section 7.3 d")
                if r["type"] == "事实" and res.get("mode") == "whatif":
                    out.append(f"{rid}: a fact cannot be confirmed by a whatif run ({q})")
        if r["round"] == "2":
            if r["r2_action"] not in ACTIONS:
                out.append(f"{rid}: r2_action must be one of {sorted(ACTIONS)}")
            elif r["r2_action"] != "新增" and by_id.get(r["r1_ref"], {}).get("round") != "1":
                out.append(f"{rid}: r1_ref must name a round-1 row")
    return out


def stats(rows, names=None):
    names = names or {}
    who = lambda r: names.get(r["code"], r["code"])
    table = defaultdict(Counter)
    for r in rows:
        table[(who(r), r["round"], r["type"])][final(r) or "（未标）"] += 1
    lines = ["| 对象 | 轮次 | 类型 | 分母 | 各标签条数 |", "|---|---|---|---|---|"]
    for (w, rnd, typ), c in sorted(table.items()):
        lines.append(f"| {w} | {rnd} | {typ} | {sum(c.values())} | "
                     + "；".join(f"{k} {v}" for k, v in sorted(c.items())) + " |")
    trans = defaultdict(Counter)
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        if r["round"] == "2" and r["r2_action"] in ACTIONS:
            before = final(by_id[r["r1_ref"]]) if r["r1_ref"] in by_id else "（新增）"
            trans[who(r)][(before, r["r2_action"])] += 1
    if trans:
        lines += ["", "| 对象 | 第 1 轮标签 → 第 2 轮动作 | 条数 |", "|---|---|---|"]
        for w, c in sorted(trans.items()):
            lines += [f"| {w} | {b} → {a} | {n} |" for (b, a), n in sorted(c.items())]
    changed = sum(1 for r in rows if r["author_label"].strip() and r["author_label"].strip() != r["label"].strip())
    labelled = sum(1 for r in rows if final(r))
    hyps = [r for r in rows if r["type"] == "假设"]
    retyped = sum(r["type"] != r["type_initial"] for r in rows)
    lines += ["", f"- 作者改动的标签：{changed} / {labelled}",
              f"- 给出证伪条件的假设：{sum(r['falsifier_given'] == '是' for r in hyps)} / {len(hyps)}",
              f"- 拆分时改动类型的判断：{retyped} / {len(rows)}"]
    return "\n".join(lines) + "\n"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", default=os.path.join(DIAG, "claims.tsv"))
    ap.add_argument("--mapping")
    ap.add_argument("--out", default=os.path.join(DIAG, "stats.md"))
    args = ap.parse_args(argv)
    rows = load(args.claims)
    bad = problems(rows)
    for p in bad:
        print(f"CLAIMS {p}")
    if bad:
        print(f"CLAIMS FAIL: {len(bad)} problem(s)")
        return 1
    names = None
    if args.mapping:
        with open(args.mapping, encoding="utf-8") as f:
            names = json.load(f)["codes"]
    text = stats(rows, names)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
