"""Internal-label check of the model-visible files (protocol v0.3 section 6.2; R5 M4, R6 M13). The ban covers what the
OPERATOR generates: path names, title lines and metadata lines of the materials, prompts and returned results.
Model prose (between the round-1 answer markers), tool output (lines between QUERY BEGIN and QUERY END markers) and
CLOSED fenced code blocks are left as they are: a model may well write "missing", and check_setup prints it. An
unclosed fence hides nothing. Every skipped segment is reported with its kind and line range.
  python -B scripts/label_check.py <file>...        exit 1 when a label word is found in an operator-generated part
"""
import fnmatch
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
DEFAULT_VISIBLE = ["package/intent.md", "package/values.txt", "package/summary_R1.tsv", "package/summary_R2.tsv",
                   "package/path_R1.rpt", "package/path_R2.rpt", "package/dot4sat.v", "package/context.md", "prompts/system.md",
                   "prompts/round1_user.md", "prompts/round2/*.md", "round2/*_results.md"]


def words(path=None):
    path = path or os.path.join(c2paths.RULES, "label_words.txt")
    if not os.path.exists(path):
        return list(DEFAULT_WORDS)
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def visible_patterns(path=None):
    path = path or os.path.join(c2paths.RULES, "model_visible.txt")
    if not os.path.exists(path):
        return list(DEFAULT_VISIBLE)
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def is_model_visible(rel_path, patterns=None):
    rel = rel_path.replace("\\", "/")
    return any(fnmatch.fnmatchcase(rel, p) for p in (patterns or visible_patterns()))


def _pattern(ws):
    # "_" separates words on purpose: summary_missing.tsv must be caught; min_block (no label word) is not
    return re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(w) for w in ws) + r")(?![A-Za-z0-9])", re.I)


def segments(text):
    """Classify every line: ('operator'|'model_answer'|'fence'|'tool_output'). Fences count only when closed; inside a
    model answer or tool output the fence state is not touched (R6 M13)."""
    lines = text.splitlines()
    kind = ["operator"] * len(lines)
    i = 0
    while i < len(lines):
        line = lines[i]
        if ANSWER_BEGIN in line:
            j = i + 1
            while j < len(lines) and ANSWER_END not in lines[j]:
                j += 1
            for k in range(i, min(j + 1, len(lines))):
                kind[k] = "model_answer"
            i = j + 1
            continue
        if "QUERY BEGIN" in line and line.startswith("==="):
            j = i + 1
            while j < len(lines) and not ("QUERY END" in lines[j] and lines[j].startswith("===")):
                j += 1
            for k in range(i, min(j + 1, len(lines))):
                kind[k] = "tool_output"
            i = j + 1
            continue
        if FENCE.match(line):
            j = i + 1
            while j < len(lines) and not FENCE.match(lines[j]) and ANSWER_BEGIN not in lines[j]:
                j += 1
            if j < len(lines) and FENCE.match(lines[j]):          # closed fence: skip it
                for k in range(i, j + 1):
                    kind[k] = "fence"
                i = j + 1
                continue
            # unclosed fence: the opening line and everything after it stay operator text
        i += 1
    return lines, kind


def scan_report(text, logical_path, ws=None):
    pat = _pattern(ws or words())
    findings = []
    parts = logical_path.replace("\\", "/").split("/")
    for part in parts[-2:]:
        if pat.search(part):
            findings.append(f"{logical_path}: path component {part!r} contains an internal label")
    lines, kind = segments(text)
    skipped, cur = [], None
    for n, (line, k) in enumerate(zip(lines, kind), 1):
        if k == "operator":
            if cur:
                skipped.append(cur)
                cur = None
            m = pat.search(line)
            if m:
                findings.append(f"{logical_path}:{n}: operator-generated line contains {m.group(0)!r}: {line.strip()[:80]}")
        else:
            if cur and cur["kind"] == k:
                cur["end"] = n
            else:
                if cur:
                    skipped.append(cur)
                cur = {"kind": k, "start": n, "end": n}
    if cur:
        skipped.append(cur)
    return {"path": logical_path, "findings": findings, "skipped": skipped}


def scan_text(text, logical_path, ws=None):
    return scan_report(text, logical_path, ws)["findings"]


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
