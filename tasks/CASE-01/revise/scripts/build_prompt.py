"""Build the exact prompt bytes of CASE-01 stage B (implementation plan Task 9; protocol v0.5 sections 5.2, 5.3,
6.3, 11; author checkpoint 1, revise/revisions.md).

  python -B revise/scripts/build_prompt.py round1 <code>           -> revise/prompts/r1/<code>_prompt.md
  python -B revise/scripts/build_prompt.py round2 <r1_code>        -> revise/prompts/r2/<r2 code>_prompt.md
  python -B revise/scripts/build_prompt.py smoke-rehearsal <model> -> runs/revise-smoke/prompts/rehearsal_<model>.md
  python -B revise/scripts/build_prompt.py smoke-canary            -> runs/revise-smoke/prompts/canary_user.md
  python -B revise/scripts/build_prompt.py cap-probe               -> runs/revise-smoke/prompts/cap_probe_user.md
  add --check to compare with the existing file instead of writing it. Files are never rewritten.

The system prompts (revise/prompts/system.md, smoke_system.md) are passed separately (--system-prompt), never
inserted. The smoke prompts are not committed; the smoke records keep their sha256.

round1 <code>: mapping.load(1) gives the model of the code ("claude", "kimi" or "deepseek", the run_order names);
  round1_template.md with {{材料}} = every package file of revise/package/ (checked against its SHA256SUMS) with line
  numbers, in build_package.ORDER, and {{附件}} = the model's own stage A round-2 answer
  diag/outputs/round2/<ATTACHMENT[model]>.md, also with line numbers, under the name ATTACHMENT_NAME.
round2 <r1_code>: mapping.load(1) and load(2); the round-2 code is the one whose prev_code is r1_code. One order for
  every round-1 state: the full round-1 prompt -> the own answer (when there is one) -> the round-2 rules -> the
  mechanical feedback -> its fixed ending; the round-1 prompt appears exactly once, first (checked). The round-1
  state (revise/results/r1/<r1_code>/status.json "state", one of ROUND1_STATES) selects a section of round2_template.md:
    answered     {{第1轮题目}} the committed round-1 prompt, {{第1轮答复}} the committed public answer
                 revise/outputs/r1/<r1_code>.md, {{第2轮规则}} the rules section, {{反馈}} the feedback file
    unavailable  the same without {{第1轮答复}} (there is no answer)
  The feedback file revise/prompts/r2/<r1_code>_feedback.md (feedback.py) holds the feedback and the ending
  (protocol 11) and never the round-1 prompt (a feedback containing it is refused); nothing is appended after it.
smoke-rehearsal <model>: round1_template.md up to (not including) the line TASK_HEADING, filled as for round 1,
  inserted as {{题目前部}} into smoke_rehearsal_template.md (protocol 6.3 part 2: the ending is replaced by the fixed
  rehearsal task).
Substitution is one pass, so text inside an inserted part is never taken for a placeholder.
Python standard library only; Windows and WSL."""
import os
import re
import sys

import build_package as bp
import feedback
import mapping
import prereg
import revpaths as rp

ATTACHMENT = {"claude": "A", "kimi": "B", "deepseek": "C"}
ATTACHMENT_NAME = "阶段A答复.md"
STAGE_A_ROUND2 = os.path.join(rp.CASE, "diag", "outputs", "round2")
SMOKE_PROMPTS = os.path.join(rp.CASE, "runs", "revise-smoke", "prompts")
PLACEHOLDERS = ("材料", "附件", "第1轮题目", "第1轮答复", "第2轮规则", "反馈", "题目前部")
PLACEHOLDER = re.compile(r"\{\{(" + "|".join(PLACEHOLDERS) + r")\}\}")
TASK_HEADING = "## 作答要求"
ROUND2_KEYS = ("answered", "unavailable", "rules")
ROUND1_STATES = frozenset(feedback.TEMPLATE_OF)      # the final round-1 states, each with a feedback template


class PromptError(Exception):
    pass


def _text(path):
    try:
        return rp.read_bytes(path).decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise PromptError(f"PROMPT FAIL: cannot read {path} ({e.__class__.__name__})") from None


def numbered(name, data):
    lines = data.decode("utf-8").splitlines()
    body = "".join(f"{i:>4}| {line}\n" for i, line in enumerate(lines, 1))
    return f"=== 文件：{name}（共 {len(lines)} 行）===\n{body}=== 文件结束：{name} ===\n"


def fill(template, values):
    used = set(PLACEHOLDER.findall(template))
    if used != set(values):
        raise PromptError(f"PROMPT FAIL: placeholders {sorted(used)} do not match the values {sorted(values)}")
    return PLACEHOLDER.sub(lambda m: values[m.group(1)], template)


def package_files(package=None):
    """{name: bytes} of the package files in build_package.ORDER, each checked against the package SHA256SUMS."""
    package = package or rp.PACKAGE
    sums = {}
    for ln in _text(os.path.join(package, "SHA256SUMS")).splitlines():
        parts = ln.split("  ")
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]) or parts[1] in sums:
            raise PromptError(f"PROMPT FAIL: package SHA256SUMS: malformed line {ln!r}")
        sums[parts[1]] = parts[0]
    if list(sums) != list(bp.ORDER):
        raise PromptError("PROMPT FAIL: package SHA256SUMS does not list exactly the package files in order")
    files = {}
    for n in bp.ORDER:
        try:
            data = rp.read_bytes(os.path.join(package, n))
        except OSError as e:
            raise PromptError(f"PROMPT FAIL: cannot read package file {n} ({e.__class__.__name__})") from None
        if rp.sha256_bytes(data) != sums[n]:
            raise PromptError(f"PROMPT FAIL: package file {n} differs from the package SHA256SUMS")
        files[n] = data
    return files


def _round1_values(model, package):
    if model not in ATTACHMENT:
        raise PromptError(f"PROMPT FAIL: unknown model name {model!r} (expected one of {sorted(ATTACHMENT)})")
    files = package_files(package)
    material = "\n".join(numbered(n, files[n]) for n in bp.ORDER).rstrip("\n")
    att_path = os.path.join(STAGE_A_ROUND2, ATTACHMENT[model] + ".md")
    try:
        att = rp.read_bytes(att_path)
        att.decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise PromptError(f"PROMPT FAIL: cannot read the stage A attachment {att_path} "
                          f"({e.__class__.__name__})") from None
    return {"材料": material, "附件": numbered(ATTACHMENT_NAME, att).rstrip("\n")}


def _template(name, templates):
    return _text(os.path.join(templates or rp.PROMPTS, name))


def round1_for_model(model, package=None, templates=None):
    return fill(_template("round1_template.md", templates), _round1_values(model, package)).encode("utf-8")


def round1_bytes(code, revise=None, sealed=None, package=None, templates=None):
    """The round-1 prompt of `code` (its model from the committed round-1 mapping)."""
    m1 = mapping.load(1, revise=revise, sealed=sealed)
    return round1_for_model(mapping.model_of(m1, code), package, templates)


def rehearsal_bytes(model, package=None, templates=None):
    t = _template("round1_template.md", templates)
    lines = t.split("\n")
    hits = [i for i, ln in enumerate(lines) if ln == TASK_HEADING]
    if len(hits) != 1:
        raise PromptError(f"PROMPT FAIL: round1_template.md must have exactly one line {TASK_HEADING!r}")
    head = "\n".join(lines[:hits[0]]).rstrip("\n")
    prefix = fill(head, _round1_values(model, package))
    return fill(_template("smoke_rehearsal_template.md", templates), {"题目前部": prefix}).encode("utf-8")


def canary_bytes(templates=None):
    """(system prompt bytes, user prompt bytes) of the canary (protocol 6.3 part 1)."""
    return (_template("smoke_system.md", templates).encode("utf-8"),
            _template("smoke_user.md", templates).encode("utf-8"))


def cap_probe_bytes(templates=None):
    return _template("cap_probe_user.md", templates).encode("utf-8")


def round2_sections(templates=None):
    """{key: text} of round2_template.md: one '## <key>' section per key of ROUND2_KEYS; the text before the first
    section is a note for the operator and not part of any prompt; each text without its surrounding blank lines."""
    sections, key = {}, None
    for line in _template("round2_template.md", templates).split("\n"):
        m = re.match(r"^## (\S+)\s*$", line)
        if m and m.group(1) in ROUND2_KEYS:
            key = m.group(1)
            if key in sections:
                raise PromptError(f"PROMPT FAIL: round2_template.md repeats the section {key}")
            sections[key] = []
        elif key is not None:
            sections[key].append(line)
    out = {k: "\n".join(v).strip("\n") for k, v in sections.items()}
    if set(out) != set(ROUND2_KEYS) or not all(out.values()):
        raise PromptError(f"PROMPT FAIL: round2_template.md must have the non-empty sections {' '.join(ROUND2_KEYS)}")
    return out


def round2_bytes(r1_code, revise=None, sealed=None, templates=None):
    """(round-2 code, prompt bytes) for round-1 candidate r1_code (see the module doc)."""
    revise = revise or rp.REVISE
    m1 = mapping.load(1, revise=revise, sealed=sealed)
    m2 = mapping.load(2, revise=revise, sealed=sealed)
    mapping.model_of(m1, r1_code)
    hits = [e["code"] for e in m2["entries"] if e["prev_code"] == r1_code]
    if len(hits) != 1:
        raise mapping.MappingError(f"MAPPING FAIL: no single round-2 code has the previous code {r1_code}")
    r2_code = hits[0]
    st_path = os.path.join(revise, "results", "r1", r1_code, "status.json")
    try:
        state = rp.load_json_decimal(st_path).get("state")
    except (OSError, ValueError, AttributeError) as e:
        raise PromptError(f"PROMPT FAIL: round-1 status.json of {r1_code} cannot be read ({e.__class__.__name__})") \
            from None
    if state not in ROUND1_STATES:
        raise PromptError(f"PROMPT FAIL: round-1 state {state!r} of {r1_code} is not a known final round-1 state")
    prompt = os.path.join(revise, "prompts", "r1", f"{r1_code}_prompt.md")
    if not prereg.committed_unchanged(prompt):
        raise PromptError(f"PROMPT FAIL: the round-1 prompt of {r1_code} is missing, untracked or differs from HEAD")
    fb_path = os.path.join(revise, "prompts", "r2", f"{r1_code}_feedback.md")
    if not os.path.isfile(fb_path):
        raise PromptError(f"PROMPT FAIL: the feedback {fb_path} is missing (feedback.py writes it)")
    fb = rp.read_bytes(fb_path)
    r1 = rp.read_bytes(prompt)
    sec = round2_sections(templates)
    feedback_text = fb.decode("utf-8").rstrip("\n")
    r1_text = r1.decode("utf-8").rstrip("\n")
    if r1_text in feedback_text:
        raise PromptError(f"PROMPT FAIL: the feedback of {r1_code} contains the round-1 prompt; the round-1 prompt "
                          f"is placed once, first, by build_prompt (regenerate the feedback with feedback.py)")
    values = {"第1轮题目": r1_text, "第2轮规则": sec["rules"], "反馈": feedback_text}
    if state == "unavailable":
        text = fill(sec["unavailable"], values)
    else:
        answer = os.path.join(revise, "outputs", "r1", f"{r1_code}.md")
        if not prereg.committed_unchanged(answer):
            raise PromptError(f"PROMPT FAIL: the public round-1 answer of {r1_code} is missing, untracked or "
                              f"differs from HEAD")
        values["第1轮答复"] = rp.read_bytes(answer).decode("utf-8").rstrip("\n")
        text = fill(sec["answered"], values)
    if not text.startswith(r1_text + "\n") or text.count(r1_text) != 1 or not text.endswith(feedback_text):
        raise PromptError(f"PROMPT FAIL: the round-2 prompt of {r1_code} must start with the round-1 prompt, hold it "
                          f"exactly once and end with the feedback")
    data = (text + "\n").encode("utf-8")
    if b"\r" in data:
        raise PromptError(f"PROMPT FAIL: the round-2 prompt of {r1_code} would not be LF-only text")
    return r2_code, data


def _write_or_check(path, data, check, base):
    rel = os.path.relpath(path, base)
    if check:
        same = os.path.isfile(path) and rp.read_bytes(path) == data
        print(f"PROMPT {'OK' if same else 'DIFFERS'}: {rel}", flush=True)
        return 0 if same else 1
    if os.path.exists(path) and rp.read_bytes(path) != data:
        print(f"PROMPT FAIL: {rel} exists with different content; it is not rewritten", flush=True)
        return 1
    rp.write_new_or_same(path, data)
    print(f"PROMPT OK: {rel} ({len(data)} bytes, sha256 {rp.sha256_bytes(data)})", flush=True)
    return 0


USAGE = ("usage: build_prompt.py round1 <code> | round2 <r1_code> | smoke-rehearsal <model> | smoke-canary | "
         "cap-probe [--check]")


def main(argv=None, revise=None, sealed=None, package=None, templates=None, smoke_dir=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in argv
    args = [a for a in argv if a != "--check"]
    arity = {"round1": 2, "round2": 2, "smoke-rehearsal": 2, "smoke-canary": 1, "cap-probe": 1}
    if not args or args[0] not in arity or len(args) != arity[args[0]]:
        print(USAGE, file=sys.stderr)
        return 2
    kind = args[0]
    revise_dir = revise or rp.REVISE
    smoke = smoke_dir or SMOKE_PROMPTS
    try:
        if kind == "round1":
            if not mapping.CODE_RE.fullmatch(args[1]):
                print(USAGE, file=sys.stderr)
                return 2
            data = round1_bytes(args[1], revise=revise, sealed=sealed, package=package, templates=templates)
            path = os.path.join(revise_dir, "prompts", "r1", f"{args[1]}_prompt.md")
        elif kind == "round2":
            if not mapping.CODE_RE.fullmatch(args[1]):
                print(USAGE, file=sys.stderr)
                return 2
            r2_code, data = round2_bytes(args[1], revise=revise, sealed=sealed, templates=templates)
            path = os.path.join(revise_dir, "prompts", "r2", f"{r2_code}_prompt.md")
        elif kind == "smoke-rehearsal":
            data = rehearsal_bytes(args[1], package=package, templates=templates)
            path = os.path.join(smoke, f"rehearsal_{args[1]}.md")
        elif kind == "smoke-canary":
            data = canary_bytes(templates)[1]
            path = os.path.join(smoke, "canary_user.md")
        else:
            data = cap_probe_bytes(templates)
            path = os.path.join(smoke, "cap_probe_user.md")
        base = revise_dir if kind in ("round1", "round2") else smoke
        return _write_or_check(path, data, check, base)
    except (PromptError, mapping.MappingError, rp.RevpathsError, prereg.PreregError) as e:
        print(str(e), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
