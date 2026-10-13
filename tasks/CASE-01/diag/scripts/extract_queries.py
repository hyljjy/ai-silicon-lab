"""Extract the round-2 query units from one model's round-1 answer (protocol v0.5 section 8;
rules/rewrite_table.md section 1). Deterministic; the author reviews the result before round 2.

  python3 -B diag/scripts/extract_queries.py <A|B|C>

Reads diag/outputs/round1/<code>.md and writes diag/round2/q/<code><n>.tcl (a query to run) or <code><n>.txt (not
runnable), plus diag/round2/extracted_<code>.tsv with columns: qid kind line file fixed_code.
Part 4 runs from the line matching "四、下一步查询" (、 . or ．) to the line before the one matching "五、".
Command words = rules/allow_query.txt + allow_whatif.txt + setup_commands.txt + OTHER_STA (timing commands of other
tools, which run and come back as 语法错误); inside code (blocks and inline spans) also TCL_BASIC words followed by
an argument. Plain text lines never count Tcl basics, so prose such as "set the load ..." is not a command.
Units, numbered in order of appearance:
  codeblock  each fenced code block whose first command line starts with a command word, whatever its language tag;
             also every block tagged tcl, sdc or not tagged                                         -> .tcl
  nontcl     any other fenced code block (a shell, Python or Yosys script)                           -> .txt, 需要模型外数据
  inline     outside code blocks, a line holding `inline code` spans that start with a command word: all such spans
             of the line, in order, form one query (one line = one list item)                       -> .tcl
  line       outside code blocks, a line without command spans that starts with a command word once the list marker
             and a leading label ("**确认扇出**：", "步骤 1:") are removed                              -> .tcl
  text       outside code blocks, a list item that contains no command                              -> .txt, 未执行：未指明可执行的对象或命令
Exit 1 if part 4 is not found.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagpaths import DIAG, OUTPUTS, RULES, write_new_or_same  # noqa: E402

PART4 = re.compile(r"四\s*[、.．]\s*下一步查询")
PART5 = re.compile(r"五\s*[、.．]")
FENCE = re.compile(r"^\s*```\s*([A-Za-z0-9_+-]*)\s*$")
LIST = re.compile(r"^\s*(?:[-*•]|\d+[.)、]|（\d+）|\(\d+\))\s+")
LABEL = re.compile(r"^(?:\*\*[^*]+\*\*|__[^_]+__|[^`:：\s][^`:：]{0,29})\s*[:：]\s*")
INLINE = re.compile(r"`([^`\n]+)`")
TCL_TAGS = {"", "tcl", "sdc"}
OTHER_STA = {"report_timing", "get_timing_paths", "report_constraint", "report_global_timing", "report_qor",
             "all_fanin", "all_fanout", "get_attribute", "report_timing_summary", "report_design"}
TCL_BASIC = {"set", "puts", "foreach", "for", "if", "while", "expr", "llength", "lindex", "lsort", "catch"}
NOT_RUN = "未执行：未指明可执行的对象或命令"
OUTSIDE = "需要模型外数据"


def commands(rules=RULES):
    out = set(OTHER_STA)
    for name in ("allow_query.txt", "allow_whatif.txt", "setup_commands.txt"):
        with open(os.path.join(rules, name), encoding="utf-8") as f:
            out |= {w.strip() for w in f if w.strip() and not w.startswith("#")}
    return out


def starts_with_command(text, cmds, basic=True):
    """The first word is a command word; Tcl basics count only inside code (basic=True) and with an argument."""
    words = text.strip().split()
    if not words:
        return False
    return words[0] in cmds or (basic and words[0] in TCL_BASIC and len(words) > 1)


def part4(lines):
    start = next((i for i, l in enumerate(lines) if PART4.search(l)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if PART5.search(l := lines[i]) and l.lstrip(" #*").startswith("五")),
               len(lines))
    return start + 1, end


def block_kind(tag, body, cmds):
    first = next((l for l in body if l.strip() and not l.strip().startswith("#")), "")
    return "codeblock" if tag in TCL_TAGS or starts_with_command(first, cmds) else "nontcl"


def extract(answer, cmds):
    """Return [(kind, first line number, text)] for the part-4 units of one answer."""
    lines = answer.splitlines()
    span = part4(lines)
    if span is None:
        raise ValueError("part 4 heading not found")
    units, i = [], span[0]
    while i < span[1]:
        line = lines[i]
        fence = FENCE.match(line)
        if fence:
            tag, body, j = fence.group(1).lower(), [], i + 1
            while j < span[1] and not FENCE.match(lines[j]):
                body.append(lines[j])
                j += 1
            units.append((block_kind(tag, body, cmds), i + 1, "\n".join(body)))
            i = j + 1
            continue
        spans = INLINE.findall(line)
        cmd_spans = [s.strip() for s in spans if starts_with_command(s, cmds)]
        stripped = LIST.sub("", line, count=1).strip()
        if not starts_with_command(stripped, cmds, basic=False):
            stripped = LABEL.sub("", stripped, count=1)
        if cmd_spans:
            units.append(("inline", i + 1, "\n".join(cmd_spans)))
        elif not spans and starts_with_command(stripped, cmds, basic=False):
            units.append(("line", i + 1, stripped))
        elif LIST.match(line):
            units.append(("text", i + 1, line.strip()))
        i += 1
    return units


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in ("A", "B", "C"):
        print("usage: extract_queries.py <A|B|C>")
        return 2
    code = argv[0]
    with open(os.path.join(OUTPUTS, "round1", f"{code}.md"), encoding="utf-8") as f:
        answer = f.read()
    try:
        units = extract(answer, commands())
    except ValueError as e:
        print(f"EXTRACT FAIL: {code}: {e}; the author decides how to proceed")
        return 1
    rows = ["qid\tkind\tline\tfile\tfixed_code"]
    for n, (kind, line_no, text) in enumerate(units, 1):
        qid = f"{code}{n}"
        ext = ".tcl" if kind in ("codeblock", "inline", "line") else ".txt"
        rel = f"round2/q/{qid}{ext}"
        write_new_or_same(os.path.join(DIAG, rel), (text.rstrip("\n") + "\n").encode("utf-8"))
        fixed = {"nontcl": OUTSIDE, "text": NOT_RUN}.get(kind, "-")
        rows.append(f"{qid}\t{kind}\t{line_no}\t{rel}\t{fixed}")
    write_new_or_same(os.path.join(DIAG, "round2", f"extracted_{code}.tsv"), ("\n".join(rows) + "\n").encode())
    print(f"EXTRACT OK: {code}: {len(units)} unit(s), "
          f"{sum(k in ('codeblock', 'inline', 'line') for k, _, _ in units)} to run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
