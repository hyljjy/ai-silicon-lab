"""Copy CASE-02 query runs into the repository (protocol v0.3 sections 6.4, 9). Copied and adapted from
tasks/CASE-01/diag/scripts/collect_runs.py (rules/copied_from.tsv).
  python3 -B scripts/collect_runs.py <group> runs/<run dir> [...]
For each run directory: copies the query, outputs, per-call records and result.json to queries/<group>/<qid>_<ctx>/
(a second run of the same instance, e.g. after a mechanical rewrite, gets a numbered suffix), with the version name
stripped from result.json, then rewrites queries/<group>/SHA256SUMS. Refuses self-test runs and runs made with an
uncommitted executor. A run whose environment check failed IS collected (the failure record is kept for the
attribution and the instance table) but flagged; build_results never returns its output."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2paths import CASE, QUERIES, read_bytes, sha256_bytes, write_new_or_same  # noqa: E402

FILES = ("query.tcl", "query_full.txt", "query_return.txt", "env_part.log", "snapshot.log", "calls.jsonl", "tops.jsonl")


def collect(group, run_dirs, case=CASE, dest_root=QUERIES, allow_invalid_env=True):
    group_root = os.path.join(dest_root, group)
    for rd in run_dirs:
        src = rd if os.path.isabs(rd) else os.path.join(case, rd)
        with open(os.path.join(src, "result.json"), encoding="utf-8") as f:
            result = json.load(f)
        if result.get("selftest") or result.get("uncommitted_ok") or not result.get("executor_committed"):
            raise SystemExit(f"COLLECT FAIL: {rd} is a self-test or ran with an uncommitted executor")
        if not result.get("env_relation_ok") and not allow_invalid_env:
            raise SystemExit(f"COLLECT FAIL: {rd} has env_relation_ok false")
        result.pop("version", None)
        base = f"{result['id']}_{result['ctx']}"
        dest = os.path.join(group_root, base)
        n = 2
        while os.path.exists(dest) and read_bytes(os.path.join(dest, "result.json")) != _dump(result):
            dest = os.path.join(group_root, f"{base}_{n}")
            n += 1
        write_new_or_same(os.path.join(dest, "result.json"), _dump(result))
        for name in FILES:
            p = os.path.join(src, name)
            if os.path.exists(p):
                write_new_or_same(os.path.join(dest, name), read_bytes(p))
    lines = []
    for root, _, names in os.walk(group_root):
        for name in names:
            p = os.path.join(root, name)
            rel = os.path.relpath(p, group_root).replace(os.sep, "/")
            if rel != "SHA256SUMS":
                lines.append(f"{sha256_bytes(read_bytes(p))}  {rel}\n")
    with open(os.path.join(group_root, "SHA256SUMS"), "w", newline="\n") as f:
        f.writelines(sorted(lines, key=lambda l: l.split("  ", 1)[1]))
    return len(lines)


def _dump(result):
    return (json.dumps(result, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


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
