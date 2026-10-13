"""Build the exact prompt bytes for both rounds (protocol v0.5 sections 5.3 and 8).

  python3 -B diag/scripts/build_prompt.py round1            -> diag/prompts/round1_user.md
  python3 -B diag/scripts/build_prompt.py round2 <A|B|C>    -> diag/prompts/round2/<code>.md
  add --check to compare with the existing file instead of writing it.

Round 1: the template with every package file inserted with line numbers, in a fixed order.
Round 2: the template with the round-1 prompt, the model's own round-1 answer (diag/outputs/round1/<code>.md) and its
query results (diag/round2/<code>_results.md) inserted. One-pass substitution, so text inside an inserted part can
never be mistaken for a placeholder. The system prompt (diag/prompts/system.md) is passed separately, never inserted.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagpaths import DIAG, OUTPUTS, PACKAGE, PROMPTS, read_bytes, write_new_or_same  # noqa: E402

ORDER = ("context.md", "path_report.rpt", "case01_sdc.tcl", "values.txt", "slack_summary.tsv", "dot4sat.v")
CODES = ("A", "B", "C")
PLACEHOLDER = re.compile(r"\{\{(材料|第1轮题目|第1轮答复|执行结果)\}\}")


def numbered(name, data):
    lines = data.decode("utf-8").splitlines()
    body = "".join(f"{i:>4}| {line}\n" for i, line in enumerate(lines, 1))
    return f"=== 文件：{name}（共 {len(lines)} 行）===\n{body}=== 文件结束：{name} ===\n"


def fill(template, values):
    missing = set(PLACEHOLDER.findall(template)) - set(values)
    if missing:
        raise SystemExit(f"DIAG FAIL: no value for placeholder(s) {sorted(missing)}")
    return PLACEHOLDER.sub(lambda m: values[m.group(1)], template)


def round1_bytes():
    template = read_bytes(os.path.join(PROMPTS, "round1_template.md")).decode("utf-8")
    material = "\n".join(numbered(n, read_bytes(os.path.join(PACKAGE, n))) for n in ORDER)
    return fill(template, {"材料": material.rstrip("\n")}).encode("utf-8")


def round2_bytes(code):
    if code not in CODES:
        raise SystemExit(f"DIAG FAIL: bad code {code!r}")
    template = read_bytes(os.path.join(PROMPTS, "round2_template.md")).decode("utf-8")
    values = {"第1轮题目": round1_bytes().decode("utf-8").rstrip("\n"),
              "第1轮答复": read_bytes(os.path.join(OUTPUTS, "round1", f"{code}.md")).decode("utf-8").rstrip("\n"),
              "执行结果": read_bytes(os.path.join(DIAG, "round2", f"{code}_results.md")).decode("utf-8").rstrip("\n")}
    return fill(template, values).encode("utf-8")


def target(kind, code=None):
    return os.path.join(PROMPTS, "round1_user.md") if kind == "round1" else os.path.join(PROMPTS, "round2", f"{code}.md")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    if not args or args[0] not in ("round1", "round2") or (args[0] == "round2" and len(args) != 2):
        print("usage: build_prompt.py round1 | round2 <A|B|C> [--check]")
        return 2
    kind, code = args[0], (args[1] if len(args) > 1 else None)
    data = round1_bytes() if kind == "round1" else round2_bytes(code)
    path = target(kind, code)
    if check:
        same = os.path.exists(path) and read_bytes(path) == data
        print(f"PROMPT {'OK' if same else 'DIFFERS'}: {os.path.relpath(path, DIAG)}")
        return 0 if same else 1
    write_new_or_same(path, data)
    print(f"PROMPT OK: {os.path.relpath(path, DIAG)} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
