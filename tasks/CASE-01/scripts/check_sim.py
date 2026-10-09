"""Grader-side check of one simulation log (spec 6): never trust the TB's own verdict alone.

check(log_text, returncode, expected) -> (ok, message)
"""
import re

PASS_RE = re.compile(r"^SIM PASS checked=(\d+)$")


def check(log_text, returncode, expected):
    if returncode != 0:
        return False, f"simulator exit code {returncode}"
    lines = log_text.splitlines()
    fails = [l for l in lines if l.startswith("SIM FAIL") or l.startswith("FATAL")]
    if fails:
        return False, f"failure record: {fails[0]}"
    passes = [m for m in (PASS_RE.match(l) for l in lines) if m]
    if len(passes) != 1:
        return False, f"expected exactly one 'SIM PASS checked=<n>' line, found {len(passes)}"
    n = int(passes[0].group(1))
    if n <= 0:
        return False, "checked count is not positive"
    if n != expected:
        return False, f"checked {n} != manifest expected {expected}"
    return True, f"checked={n}"
