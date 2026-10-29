"""Internal-label check of the model-visible files (protocol v0.3 section 6.2; R5 M4). The ban covers what the
OPERATOR generates: path names, title lines and metadata lines of the materials, prompts and returned results.
Model prose (between the round-1 answer markers) and tool output (fenced code blocks, and lines after a QUERY BEGIN
marker up to QUERY END) are left as they are: a model may well write "missing", and check_setup prints it.
  python -B scripts/label_check.py <file>...        exit 1 when a label word is found in an operator-generated part
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2paths  # noqa: E402

DEFAULT_WORDS = ["correct", "missing", "restored", "mutation", "case02_missing"]
ANSWER_BEGIN = "<<<第 1 轮回答开始>>>"
ANSWER_END = "<<<第 1 轮回答结束>>>"
FENCE = re.compile(r"^\s*```")


def words(path=None):
    path = path or os.path.join(c2paths.RULES, "label_words.txt")
    if not os.path.exists(path):
        return list(DEFAULT_WORDS)
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def _pattern(ws):
    # "_" separates words on purpose: summary_missing.tsv must be caught; min_block (no label word) is not
    return re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(w) for w in ws) + r")(?![A-Za-z0-9])", re.I)


def operator_lines(text):
    """(line number, line) of the operator-generated lines of a text."""
    out, in_answer, in_fence, in_tool = [], False, False, False
    for i, line in enumerate(text.splitlines(), 1):
        if ANSWER_BEGIN in line:
            in_answer = True
            continue
        if ANSWER_END in line:
            in_answer = False
            continue
        if "QUERY BEGIN" in line and line.startswith("==="):
            in_tool = True
            continue
        if "QUERY END" in line and line.startswith("==="):
            in_tool = False
            continue
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_answer or in_fence or in_tool:
            continue
        out.append((i, line))
    return out


def scan_text(text, logical_path, ws=None):
    pat = _pattern(ws or words())
    found = []
    parts = logical_path.replace("\\", "/").split("/")
    for part in parts[-2:]:
        if pat.search(part):
            found.append(f"{logical_path}: path component {part!r} contains an internal label")
    for n, line in operator_lines(text):
        m = pat.search(line)
        if m:
            found.append(f"{logical_path}:{n}: operator-generated line contains {m.group(0)!r}")
    return found


def scan_prompt_bytes(data, logical_path, ws=None):
    return scan_text(data.decode("utf-8", errors="replace"), logical_path, ws)


def scan_operator_files(paths, ws=None):
    found = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as f:
            found += scan_text(f.read(), p, ws)
    return found


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: label_check.py <file>...")
        return 2
    found = scan_operator_files(argv)
    for f in found:
        print(f"LABEL {f}")
    print(f"LABEL {'FAIL: ' + str(len(found)) + ' finding(s)' if found else 'OK'}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
