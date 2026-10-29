"""Apply the pre-registered mechanical rewrites (rules/rewrite_table.md section 3) to one round-2 query. Copied and
adapted from tasks/CASE-01/diag/scripts/rewrite_query.py (rules/copied_from.tsv): the error triggers now match the
CASE02- error lines; the two rules are unchanged.
  python3 -B scripts/rewrite_query.py <qid> <run dir of its as-written run>
Reads round2/q/<qid>.tcl and the run's query_full.txt. A rule applies only when its trigger matches an OpenSTA error
line of the as-written run; the rewritten text goes to round2/q/<qid>_rw.tcl (only when something changed). Prints
the applied rule ids ("R2,R3") or "NONE". The rewritten query is executed once more in the same context; both runs
are kept (translation.tsv run_id_first / run_id_rewritten)."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2paths import CASE, write_new_or_same  # noqa: E402

RULES = [
    ("R2", re.compile(r"^CASE02-ERROR: Error 514: .*'-corners' is not a known keyword or flag\.", re.M),
     [(re.compile(r"(?<![\w-])-corners(?![\w-])"), "-scenes")]),
    ("R3", re.compile(r'^CASE02-ERROR: invalid command name "report_timing"', re.M),
     [(re.compile(r"(?<![\w:])report_timing(?!\w)"), "report_checks"),
      (re.compile(r"(?<![\w-])-max_paths\s+(\S+)"), r"-group_path_count \1"),
      (re.compile(r"(?<![\w-])-nworst\s+(\S+)"), r"-endpoint_path_count \1"),
      (re.compile(r"(?<![\w-])-delay_type\s+(max|min)\b"), r"-path_delay \1")]),
]


def rewrite(query, output):
    applied = []
    for rid, trigger, subs in RULES:
        if trigger.search(output):
            new = query
            for pattern, repl in subs:
                new = pattern.sub(repl, new)
            if new != query:
                query, applied = new, applied + [rid]
    return query, applied


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: rewrite_query.py <qid> <run dir>")
        return 2
    qid, run = argv
    with open(os.path.join(CASE, "round2", "q", f"{qid}.tcl"), encoding="utf-8") as f:
        query = f.read()
    run = run if os.path.isabs(run) else os.path.join(CASE, run)
    with open(os.path.join(run, "query_full.txt"), encoding="utf-8") as f:
        output = f.read()
    new, applied = rewrite(query, output)
    if applied:
        write_new_or_same(os.path.join(CASE, "round2", "q", f"{qid}_rw.tcl"), new.encode("utf-8"))
    print(",".join(applied) if applied else "NONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
