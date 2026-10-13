"""Round-2 coverage of round-1 judgments (final review I2; added after the labels, not a pre-registered file).

  python3 -B diag/scripts/round2_coverage.py [--mapping diag/outputs/mapping.json] [--out diag/stats_round2_coverage.md]

The transition table of claims_stats.py counts round-2 rows. This report looks from the other side: how many round-1
judgments (citation rows excluded) are named by at least one round-2 row's r1_ref, which refuted round-1 facts were
never named again, and which round-2 rows modify a round-1 fact or hypothesis. It only counts; it judges nothing.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claims_stats import DIAG, final, load  # noqa: E402

CITE = "证据引用"
TYPES = ("事实", "假设", "缺失证据", "查询", "修改建议")
JUDGED = ("事实", "假设")


def mentioned_ids(rows):
    return {r["r1_ref"] for r in rows if r["round"] == "2" and r["type"] != CITE and r["r1_ref"]}


def coverage(rows):
    """code -> type -> (round-1 judgments named in round 2, all round-1 judgments)."""
    named, out = mentioned_ids(rows), defaultdict(dict)
    for code in sorted({r["code"] for r in rows}):
        for typ in TYPES:
            r1 = [r for r in rows if r["code"] == code and r["round"] == "1" and r["type"] == typ]
            if r1:
                out[code][typ] = (sum(r["id"] in named for r in r1), len(r1))
    return out


def unmentioned_refuted(rows):
    named = mentioned_ids(rows)
    return [r["id"] for r in rows if r["round"] == "1" and r["type"] == "事实" and final(r) == "推翻"
            and r["id"] not in named]


def modified_judgments(rows):
    """(round-2 id, round-1 id, round-1 label, round-2 label) for 修改 rows where both sides are facts or hypotheses."""
    by_id = {r["id"]: r for r in rows}
    out = []
    for r in rows:
        r1 = by_id.get(r["r1_ref"])
        if r["round"] == "2" and r["r2_action"] == "修改" and r["type"] in JUDGED and r1 and r1["type"] in JUDGED:
            out.append((r["id"], r1["id"], final(r1), final(r)))
    return out


def report(rows, names=None):
    names = names or {}
    who = lambda c: names.get(c, c)
    lines = ["# 第 2 轮对第 1 轮判断的覆盖（终审 I2；脚本 `scripts/round2_coverage.py`，在打标签之后新增，不在预登记清单中）", "",
             "按第 1 轮的判断计数（证据引用行除外）：第 2 轮至少有一行的 r1_ref 指向它，算\"提及\"。只计数，不判定对错。", "",
             "| 对象 | 类型 | 第 2 轮提及 | 第 1 轮条数 |", "|---|---|---|---|"]
    cov = coverage(rows)
    for code in sorted(cov):
        for typ, (n, d) in cov[code].items():
            lines.append(f"| {who(code)} | {typ} | {n} | {d} |")
        n_all = sum(n for n, _ in cov[code].values())
        d_all = sum(d for _, d in cov[code].values())
        lines.append(f"| {who(code)} | 合计 | {n_all} | {d_all} |")
    refuted = unmentioned_refuted(rows)
    lines += ["", f"- 第 1 轮被推翻、第 2 轮没有再提及的事实：{len(refuted)} 条（{'、'.join(refuted) if refuted else '无'}）"]
    mods = modified_judgments(rows)
    lines += [f"- 第 2 轮修改了第 1 轮事实或假设的行：{len(mods)} 条"]
    lines += [f"  - {a} ← {b}（第 1 轮 {la}，第 2 轮 {lb}）" for a, b, la, lb in mods]
    return "\n".join(lines) + "\n"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", default=os.path.join(DIAG, "claims.tsv"))
    ap.add_argument("--mapping")
    ap.add_argument("--out", default=os.path.join(DIAG, "stats_round2_coverage.md"))
    args = ap.parse_args(argv)
    names = None
    if args.mapping:
        with open(args.mapping, encoding="utf-8") as f:
            names = json.load(f)["codes"]
    text = report(load(args.claims), names)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
