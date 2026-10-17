"""Revised statistics after the post-unblinding review (not a pre-registered file; added 2026-10-17).

  python3 -B diag/scripts/claims_stats_revised.py [--mapping diag/outputs/mapping.json] [--out diag/stats_revised.md]

claims.tsv is never changed. This script reads diag/review/postblind/decisions.tsv (one row per decision; when an id
has several rows the last one counts), overlays new_label and new_r2_action on a copy of the claims rows, checks the
copy with claims_stats.problems(), and writes the revised label table, the revised round-2 coverage report and the
list of revisions. The original stats.md and stats_round2_coverage.md stay as the record of the original labels.
"""
import argparse
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claims_stats import ACTIONS, COLUMNS, DIAG, LABELS, load, problems, stats  # noqa: E402,F401
import round2_coverage  # noqa: E402

DEC_COLUMNS = ["id", "codex_flag", "author_decision", "new_label", "new_r2_action", "reason", "date"]
DECISIONS = os.path.join(DIAG, "review", "postblind", "decisions.tsv")


def load_decisions(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.startswith("#") or not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != len(DEC_COLUMNS):
                raise SystemExit(f"DECISIONS FAIL: line {n} has {len(fields)} fields, expected {len(DEC_COLUMNS)}")
            if fields[0] == "id":
                continue
            out[fields[0]] = dict(zip(DEC_COLUMNS, fields))
    return out


def overlay(rows, decisions):
    """Return (revised copy of rows, ids with a new label, ids with a new round-2 action)."""
    out = copy.deepcopy(rows)
    by_id = {r["id"]: r for r in out}
    labels, actions = [], []
    for i, d in decisions.items():
        if i not in by_id:
            raise SystemExit(f"DECISIONS FAIL: {i} is not in claims.tsv")
        r = by_id[i]
        touched = False
        if d["new_label"] != "-":
            if d["new_label"] not in LABELS[r["type"]]:
                raise SystemExit(f"DECISIONS FAIL: {i}: {d['new_label']} is not a label for {r['type']}")
            if d["new_label"] != r["label"]:
                r["label"] = d["new_label"]
                labels.append(i)
                touched = True
        if d["new_r2_action"] != "-":
            if d["new_r2_action"] not in ACTIONS or r["round"] != "2":
                raise SystemExit(f"DECISIONS FAIL: {i}: bad round-2 action {d['new_r2_action']}")
            if d["new_r2_action"] != r["r2_action"]:
                r["r2_action"] = d["new_r2_action"]
                actions.append(i)
                touched = True
        if touched:
            r["note"] = (r["note"] + "；" if r["note"] else "") + "揭盲后修订：" + d["reason"]
    return out, sorted(labels), sorted(actions)


def report(rows, decisions, names=None):
    revised, labels, actions = overlay(rows, decisions)
    by_id = {r["id"]: r for r in rows}
    disputes = sorted(i for i, d in decisions.items() if d["author_decision"] == "争议")
    body = stats(revised, names).splitlines()
    body = [l for l in body if not l.startswith("- 作者改动的标签")]
    lines = ["# 揭盲后复核的修订统计（脚本 `scripts/claims_stats_revised.py`，揭盲后新增，不在预登记清单中）", "",
             "`claims.tsv` 未改动。本表把 `review/postblind/decisions.tsv` 的作者裁定（同一编号以最后一行为准）叠加到原表的副本上重新统计。"
             "原始统计见 `stats.md`、`stats_round2_coverage.md`。复核在揭盲之后进行，作者和外审 Codex 都知道代号对应的模型。", "",
             "## 修订后的标签统计", ""] + body + [
             f"- 揭盲前作者改动的标签：0 / {len(rows)}（历史记录；作者当时没有逐条复核，不能作为独立复核的证据）",
             f"- 揭盲后作者裁定的编号：{len(decisions)}；修订标签 {len(labels)} 条，修订第 2 轮动作 {len(actions)} 条，记为争议 {len(disputes)} 条",
             "", "## 修订后的第 2 轮覆盖", ""]
    cov = round2_coverage.report(revised, names).splitlines()
    lines += [l for l in cov if not l.startswith("# ")]
    lines += ["", "## 修订清单", "", "| 编号 | 原标签 | 修订后标签 | 原动作 | 修订后动作 |", "|---|---|---|---|---|"]
    rev_by_id = {r["id"]: r for r in revised}
    for i in sorted(set(labels) | set(actions)):
        a, b = by_id[i], rev_by_id[i]
        lines.append(f"| {i} | {a['label']} | {b['label']} | {a['r2_action'] or '-'} | {b['r2_action'] or '-'} |")
    if disputes:
        lines += ["", "争议（标签未改）：" + "、".join(disputes)]
    return "\n".join(lines) + "\n", revised


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", default=os.path.join(DIAG, "claims.tsv"))
    ap.add_argument("--decisions", default=DECISIONS)
    ap.add_argument("--mapping")
    ap.add_argument("--out", default=os.path.join(DIAG, "stats_revised.md"))
    args = ap.parse_args(argv)
    rows = load(args.claims)
    names = None
    if args.mapping:
        with open(args.mapping, encoding="utf-8") as f:
            names = json.load(f)["codes"]
    text, revised = report(rows, load_decisions(args.decisions), names)
    bad = problems(revised)
    for p in bad:
        print(f"REVISED {p}")
    if bad:
        print(f"REVISED FAIL: {len(bad)} problem(s)")
        return 1
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
