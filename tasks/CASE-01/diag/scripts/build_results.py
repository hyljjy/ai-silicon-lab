"""Assemble the round-2 query results for one code (protocol v0.5 section 8; rules/rewrite_table.md section 6).

  python3 -B diag/scripts/build_results.py <A|B|C>      -> diag/round2/<code>_results.md

Input: diag/round2/translation.tsv, reviewed by the author before round 2 (section 8 i). Tab-separated columns:
  code  qid  original  executed  rewrites  collected  fixed_code
original/executed: files (relative to diag/) with the model's query text and the text actually run; rewrites: the
mechanical rewrites applied, or "-"; collected: the id under diag/queries/round2/ whose query_return.txt is returned,
or "-" when nothing ran; fixed_code: a fixed result code for queries that did not run, or "-".
A code with no rows gets the single sentence that it proposed no executable query (section 8, Q5).
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagpaths import DIAG, read_bytes, write_new_or_same  # noqa: E402

COLUMNS = ["code", "qid", "original", "executed", "rewrites", "collected", "fixed_code"]
NO_QUERY = "你第 1 轮没有提出可执行的查询。\n"
WHATIF = "改变冻结模型的查询（已在单独运行中执行）"


def rows_for(code, diag=DIAG):
    with open(os.path.join(diag, "round2", "translation.tsv"), encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t")]
    if rows and list(rows[0].keys()) != COLUMNS:
        raise SystemExit(f"DIAG FAIL: translation.tsv columns must be {COLUMNS}")
    return [r for r in rows if r["code"] == code]


def block(lang, text):
    return f"```{lang}\n{text.rstrip(chr(10))}\n```\n"


def render(code, diag=DIAG):
    rows = rows_for(code, diag)
    if not rows:
        return NO_QUERY
    parts = []
    for r in rows:
        txt = lambda rel: read_bytes(os.path.join(diag, rel)).decode("utf-8")
        lang = "tcl" if r["original"].endswith(".tcl") else "text"
        part = [f"### 查询 {r['qid']}\n", "你写的查询：\n", block(lang, txt(r["original"]))]
        if r["collected"] != "-":
            run = os.path.join(diag, "queries", "round2", r["collected"])
            with open(os.path.join(run, "result.json"), encoding="utf-8") as f:
                codes = json.load(f)["codes"]
            part += ["实际执行的命令：\n", block("tcl", txt(r["executed"])),
                     f"机械改写：{'无' if r['rewrites'] == '-' else r['rewrites']}\n",
                     f"结果代码：{'；'.join(codes)}\n"]
            if WHATIF in codes:
                part.append("说明：这条查询改变了分析模型，结果只作对照，不代表冻结模型。\n")
            part += ["输出：\n", block("text", read_bytes(os.path.join(run, "query_return.txt")).decode("utf-8"))]
        else:
            part.append(f"结果代码：{r['fixed_code']}\n")
        parts.append("".join(part))
    return "\n".join(parts)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in ("A", "B", "C"):
        print("usage: build_results.py <A|B|C>")
        return 2
    data = render(argv[0]).encode("utf-8")
    write_new_or_same(os.path.join(DIAG, "round2", f"{argv[0]}_results.md"), data)
    print(f"RESULTS OK: round2/{argv[0]}_results.md ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
