"""Log validity check shared by grade.py and calibrate.py (spec 6, P1 M5).

Every line that looks like a warning must match a reviewed whitelist rule for that tool; error/fatal lines never
pass. Whitelist file: one rule per line, <tool><TAB><python regex><TAB><reason>; '#' lines are comments.
"""
import re

WARNING = re.compile(r"\bwarning\b", re.I)
# Python warning categories (RuntimeWarning, DeprecationWarning, UserWarning, ...). Case-sensitive, so identifiers
# such as set_warning echoed in tool logs stay unmatched (task review of Tasks 1-4).
WARNING_CATEGORY = re.compile(r"\b[A-Z]\w*Warning\b")
# Tool errors ("Error: ...", "Error 1520: ...", "ERROR: ...", "x.v:5: error: ...", "FATAL: ...") and Python
# tracebacks. Python exception names such as "ValueError:" alone are NOT matched (no word boundary inside the
# name): a step that prints one is caught by its non-zero exit code or by the "Traceback" line (P2 review).
ERROR = re.compile(r"\berror\b\s*(\d+\s*)?:|^\s*error\b|\bfatal\b\s*:|^Traceback \(most recent call last\):", re.I)
TOOLS = ("iverilog", "yosys", "sta", "python", "shell")


class RuleError(ValueError):
    pass


def load_rules(path):
    rules = []
    with open(path) as f:
        for n, raw in enumerate(f, 1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            parts = raw.rstrip("\n").split("\t")
            if len(parts) != 3 or parts[0] not in TOOLS or not parts[2].strip():
                raise RuleError(f"{path}:{n}: need <tool><TAB><regex><TAB><reason>, tool in {TOOLS}")
            rules.append({"tool": parts[0], "pattern": parts[1], "regex": re.compile(parts[1]), "reason": parts[2],
                          "line": n})
    return rules


def scan(tool, path, rules):
    """Return (problems, hits): unreviewed warnings and errors in the log; whitelist hits by rule line."""
    problems, hits = [], {}
    with open(path, errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if ERROR.search(line):
                problems.append(f"{tool} error: {line.strip()}")
            elif WARNING.search(line) or WARNING_CATEGORY.search(line):
                rule = next((r for r in rules if r["tool"] == tool and r["regex"].search(line)), None)
                if rule is None:
                    problems.append(f"{tool} unreviewed warning: {line.strip()}")
                else:
                    hits[rule["line"]] = hits.get(rule["line"], 0) + 1
    return problems, hits
