"""Copy diag query runs into the repository (protocol v0.5 section 7.1, last paragraph).

  python3 -B diag/scripts/collect_runs.py <group> runs/<ts>-diag-<id> [...]

For each run directory: copies query.tcl, query_full.txt, query_return.txt, result.json, env_part.log and
snapshot.log to diag/queries/<group>/<id>/, then rewrites diag/queries/<group>/SHA256SUMS over every file in the
group. The env/ record files are not copied: result.json's env_ok says they matched F1 byte for byte, and F1's
records are already committed under evidence/F1. Refuses a run whose env_ok is false, a self-test, a run whose
executor manifest was not committed, a --strict-log run whose query log is not clean, and an id that is already
collected with different content. A run whose query crashed or timed out (query_status) is accepted: that is the
query's result (protocol v0.5 section 8 f).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagpaths import CASE, DIAG, read_bytes, sha256_bytes, write_new_or_same  # noqa: E402

FILES = ("query.tcl", "query_full.txt", "query_return.txt", "result.json", "env_part.log", "snapshot.log")


def collect(group, run_dirs, case=CASE, diag=DIAG):
    dest_root = os.path.join(diag, "queries", group)
    for rd in run_dirs:
        src = rd if os.path.isabs(rd) else os.path.join(case, rd)
        with open(os.path.join(src, "result.json"), encoding="utf-8") as f:
            result = json.load(f)
        if not result.get("env_ok"):
            raise SystemExit(f"COLLECT FAIL: {rd} has env_ok false; its output cannot be used")
        if result.get("selftest") or not result.get("executor_committed"):
            raise SystemExit(f"COLLECT FAIL: {rd} is a self-test or ran with an uncommitted executor")
        if result.get("strict_log") and not result.get("query_log_ok"):
            raise SystemExit(f"COLLECT FAIL: {rd} was a --strict-log run and its query log is not clean")
        for name in FILES:
            write_new_or_same(os.path.join(dest_root, result["id"], name), read_bytes(os.path.join(src, name)))
    lines = []
    for root, _, names in os.walk(dest_root):
        for n in names:
            p = os.path.join(root, n)
            rel = os.path.relpath(p, dest_root).replace(os.sep, "/")
            if rel != "SHA256SUMS":
                lines.append(f"{sha256_bytes(read_bytes(p))}  {rel}\n")
    with open(os.path.join(dest_root, "SHA256SUMS"), "w", newline="\n") as f:
        f.writelines(sorted(lines, key=lambda l: l.split("  ", 1)[1]))
    return len(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        print("usage: collect_runs.py <group> <run dir>...")
        return 2
    n = collect(argv[0], argv[1:])
    print(f"COLLECT OK: {len(argv) - 1} run(s); group {argv[0]} now has {n} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
