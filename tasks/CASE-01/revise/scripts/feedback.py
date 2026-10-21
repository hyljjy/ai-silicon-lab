"""Round-2 feedback of CASE-01 stage B (implementation plan Task 8; protocol v0.4 section 11).

The feedback carries only mechanical evaluation results. mechanical_view(code, rnd) reads exactly the field-source
table of the plan (paths relative to tasks/CASE-01; a missing value is "not_available", a step that did not run
"not_run"):
  revise/results/r<rnd>/<code>/status.json        grade_status rtl_sim gl_sim sta_analysis checked_rtl checked_gl
                                                   cfg_L area_um2 within_cap numeric_target_met; selected_attempt
                                                   (which attempt directory to read)
  revise/compare/r<rnd>_<code>.json               "cells" (6 global setup/hold values; the three categories with
                                                   start and end) and candidate "summary" (worst setup / hold and
                                                   corner); read only when sta_analysis is "pass" (and required then)
  attempt<selected>/verdict.json                  worst_setup / worst_hold when there is no matrix
  attempt<selected>/attempt.json, steps.json, the archived logs, stdout.txt, stderr.txt
                                                   failure location, exit code, timed_out, log summary
  revise/outputs/r<rnd>/<code>.call.json          "final" and, per call, "categories" (see below)
  revise/outputs/r<rnd>/<code>.parsed.json        "status", "reason", "trigger_lines" (content delivery failure)
  revise/results/r<rnd>/<code>/gate.json          "passed", "hits": [{"rule", "line", "kind"}] (GateResult, Task 4)
  revise/rules/gate_rules.md                      the rule texts (format below)
Never read: the author's review table, status.json "state" (only render() reads it, to choose the template),
"flags", "author_veto", "improvement", "eligible_target_met".

call.json (written by run_revise, Task 10) is expected as
  {"final": "unavailable" | "delivery_fail" | "parse",
   "calls": [{"categories": [<classify flag category>, ...], "delivery", "retry_allowed", "global_stop"}, ...]}
in call order; only "final" and "categories" are read here.

gate_rules.md (written by Task 4): one Markdown table row per rule whose first cell is the rule id (G1 ... G8, and
"unrecognized" for "门槛无法识别") and whose second cell is the rule text given to the model, e.g.
  | G4 | 不用 `parameter`（可以用 `localparam`） | 附加提交格式限制 | ... |
Other lines are ignored; an id must not appear in two rows; "\\|" inside a cell is a literal "|".

render(r1_code): mapping.load(1) and mapping.load(2) first (MappingError when either is not committed); the code
must be in the round-1 mapping and be the prev_code of exactly one round-2 code. The round-1 state selects the
template (TEMPLATE_OF) and the ending (endings.md); unavailable also gets the full committed round-1 prompt.
Writes revise/prompts/r2/<r1_code>_feedback.md (new, or the same bytes already there; never rewritten).
Python standard library only; Windows and WSL."""
import os
import re
import sys
from decimal import Decimal, InvalidOperation

import baseline
import mapping
import prereg
import revpaths as rp

TEMPLATES = os.path.join(rp.PROMPTS, "feedback")
NA = "not_available"
NOT_RUN = "not_run"
NAPP = "not_applicable"
CORNERS = baseline.CORNERS
CHECKS = ("setup", "hold")
CATEGORIES = ("in2reg", "reg2reg", "reg2out")
TEMPLATE_OF = {"unavailable": "unavailable", "delivery_fail": "delivery_fail", "gate_reject": "gate_reject",
               "infra_fail": "infra_fail", "grade_fail": "grade_fail", "ineligible": "grade_ok",
               "eligible_no_gain": "grade_ok", "eligible_gain": "grade_ok"}
ENDING_KEYS = ("evaluated_valid", "evaluated_no_analysis", "not_evaluated", "r1_prompt_header")
STATUS_KEYS = ("grade_status rtl_sim gl_sim sta_analysis checked_rtl checked_gl cfg_L area_um2 within_cap "
               "numeric_target_met").split()
TAIL_LINES = 40
PROBLEMS_HEADER = "日志检查发现的问题："
TAIL_HEADER = f"日志最后 {TAIL_LINES} 行："
CAP_CATEGORY = "输出上限"                          # classify.F_LIMIT
NO_LINE = "无可定位的原文行"
NO_RTL_LINE = "无可定位的 RTL 行"
MAX_LINES = 10
CHECK_NAMES = {"no_verilog_block": "没有找到 verilog 代码块",
               "unclosed_block": "第一个 verilog 代码块没有结束围栏",
               "no_declared_L": "没有 `DECLARED_L = <n>` 行",
               "conflicting_declared_L": "`DECLARED_L` 行给出了不同的值",
               "no_submission_with_code": "`NO_SUBMISSION` 与 verilog 代码块同时出现"}
_PLACEHOLDER = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")
_RULE_ID = re.compile(r"^(G[1-9][0-9]*|unrecognized)$")


class FeedbackError(Exception):
    pass


# ------------------------------------------------------------------------------------------------ files
def _load(path, what, required=True):
    if not os.path.isfile(path):
        if required:
            raise FeedbackError(f"FEEDBACK FAIL: {what} is missing ({path})")
        return None
    try:
        return rp.load_json_decimal(path)
    except (OSError, ValueError) as e:
        raise FeedbackError(f"FEEDBACK FAIL: {what} cannot be read ({e.__class__.__name__}: {e})") from None


def _text(path):
    return rp.read_bytes(path).decode("utf-8", "replace")


def load_endings(templates=None):
    """{key: text} of endings.md: one '## <key>' section per ending; the text is the section without its
    surrounding blank lines."""
    path = os.path.join(templates or TEMPLATES, "endings.md")
    sections, key = {}, None
    for line in _text(path).split("\n"):
        m = re.match(r"^## (\S+)\s*$", line)
        if m:
            key = m.group(1)
            if key in sections:
                raise FeedbackError(f"FEEDBACK FAIL: endings.md repeats the section {key}")
            sections[key] = []
        elif key is not None:
            sections[key].append(line)
    out = {k: "\n".join(v).strip("\n") for k, v in sections.items()}
    if set(out) != set(ENDING_KEYS) or not all(out.values()):
        raise FeedbackError(f"FEEDBACK FAIL: endings.md must have exactly the non-empty sections "
                            f"{' '.join(ENDING_KEYS)}")
    return out


def _cells(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    parts = re.split(r"(?<!\\)\|", s[1:])
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.replace("\\|", "|").strip() for p in parts]


def gate_rule_texts(path):
    """{rule id: rule text} from gate_rules.md (format in the module doc)."""
    if not os.path.isfile(path):
        raise FeedbackError(f"FEEDBACK FAIL: revise/rules/gate_rules.md is missing ({path}); it is written by "
                            f"Task 4 (gate)")
    out = {}
    for line in _text(path).split("\n"):
        c = _cells(line)
        if not c or len(c) < 2 or not _RULE_ID.match(c[0]):
            continue
        if c[0] in out:
            raise FeedbackError(f"FEEDBACK FAIL: gate_rules.md has two rows for {c[0]}")
        out[c[0]] = c[1]
    return out


# ------------------------------------------------------------------------------------------------ log summary
def _wsl_form(path):
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
    if m:
        return f"/mnt/{m.group(1).lower()}/" + m.group(2).replace("\\", "/")
    return path


def _normalizer(repo, run_id):
    repo = repo.rstrip("/")
    roots = []
    if run_id:
        roots.append((f"{repo}/tasks/CASE-01/runs/{run_id}", "<RUN>"))   # longer first (protocol 11, step 3)
    roots.append((repo, "<REPO>"))

    def norm(text):
        for path, tag in roots:
            text = text.replace(path + "/", tag + "/")
            text = re.sub(re.escape(path) + r"(?![A-Za-z0-9_.\-])", tag, text)
        return text
    return norm


def log_summary(attempt_dir, repo=None):
    """Protocol 11 'log summary' of one attempt: the failing step's logs in steps.json "logs" order (a missing file
    becomes the line '<日志未生成：<name>>'), or stdout.txt then stderr.txt when the location is outside the steps
    (outside_steps / no_final_line); paths normalized (run directory -> <RUN>/, then repository root -> <REPO>/);
    the last 40 physical lines; the failing step's log_problems (normalized, never cut) as a prefix.
    repo: the repository root as it appears in the logs (default: the WSL form of this repository)."""
    att = _load(os.path.join(attempt_dir, "attempt.json"), "attempt.json")
    loc = att.get("failure_location")
    norm = _normalizer(repo or _wsl_form(rp.REPO), att.get("run_id"))
    problems = []
    if loc in ("outside_steps", "no_final_line"):
        sources = ["stdout.txt", "stderr.txt"]
    elif not isinstance(loc, str) or loc in ("none", NOT_RUN, ""):
        raise FeedbackError(f"FEEDBACK FAIL: {attempt_dir}: no failure location ({loc!r})")
    else:
        steps = _load(os.path.join(attempt_dir, "steps.json"), "steps.json")
        step = next((s for s in steps or [] if isinstance(s, dict) and s.get("step") == loc), None)
        if step is None:
            raise FeedbackError(f"FEEDBACK FAIL: {attempt_dir}: step {loc} is not in steps.json")
        sources = [str(x) for x in step.get("logs") or []]
        problems = [str(p) for p in step.get("log_problems") or []]
    body = ""
    for rel in sources:
        path = os.path.join(attempt_dir, *rel.replace("\\", "/").split("/"))
        piece = _text(path) if os.path.isfile(path) else f"<日志未生成：{rel}>\n"
        if piece and not piece.endswith("\n"):
            piece += "\n"
        body += piece
    body = norm(body)
    lines = body.split("\n")[:-1] if body else []
    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in lines]
    out = []
    if problems:
        out += [PROBLEMS_HEADER] + [norm(p) for p in problems] + [""]
    out += [TAIL_HEADER] + lines[-TAIL_LINES:]
    return "\n".join(out)


# ------------------------------------------------------------------------------------------------ the view
def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, Decimal)):
        return Decimal(v)
    if isinstance(v, str):
        try:
            d = Decimal(v)
        except InvalidOperation:
            return None
        return d if d.is_finite() else None
    return None


def _worst(obj):
    if isinstance(obj, dict) and _num(obj.get("slack")) is not None and isinstance(obj.get("corner"), str):
        return {"slack": _num(obj["slack"]), "corner": obj["corner"]}
    return None


def _first_lines(values):
    lines = sorted({v for v in values if isinstance(v, int) and not isinstance(v, bool) and v > 0})
    return lines[:MAX_LINES]


def mechanical_view(code, rnd, case=None, repo=None, rules=None):
    """The mechanical fields of one candidate (see the module doc); never reads the state or research fields."""
    case = case or rp.CASE
    revise = os.path.join(case, "revise")
    cdir = os.path.join(revise, "results", f"r{rnd}", code)
    out_dir = os.path.join(revise, "outputs", f"r{rnd}")
    st = _load(os.path.join(cdir, "status.json"), f"status.json of {code}")
    v = {k: st.get(k, NA) for k in STATUS_KEYS}
    absent = NOT_RUN if v["sta_analysis"] == NOT_RUN else NA

    sel = st.get("selected_attempt")
    adir = os.path.join(cdir, f"attempt{sel}") if isinstance(sel, int) and not isinstance(sel, bool) else None
    att = _load(os.path.join(adir, "attempt.json"), "attempt.json", required=False) if adir else None

    # matrix (only with a valid analysis)
    v["global"], v["categories"], v["worst_setup"], v["worst_hold"] = absent, absent, absent, absent
    if v["sta_analysis"] == "pass":
        doc = _load(os.path.join(revise, "compare", f"r{rnd}_{code}.json"), f"compare/r{rnd}_{code}.json")
        if doc.get("code") != code or doc.get("rnd") != rnd:
            raise FeedbackError(f"FEEDBACK FAIL: compare/r{rnd}_{code}.json is not the record of {code} r{rnd}")
        cells = {}
        for x in doc.get("cells") or []:
            cells[(x.get("corner"), x.get("check"), x.get("scope"))] = x.get("cand") or {}
        glob, cats = {}, {}
        for c in CORNERS:
            for chk in CHECKS:
                g = cells.get((c, chk, "global"), {})
                glob[(c, chk)] = _num(g.get("slack")) if _num(g.get("slack")) is not None else NA
                for cat in CATEGORIES:
                    x = cells.get((c, chk, cat))
                    if x is None:
                        cats[(c, chk, cat)] = {"slack": NA, "start": NA, "end": NA}
                    elif x.get("slack") == NAPP:
                        cats[(c, chk, cat)] = {"slack": NAPP, "start": NAPP, "end": NAPP}
                    else:
                        s = _num(x.get("slack"))
                        cats[(c, chk, cat)] = {"slack": s if s is not None else NA,
                                               "start": x.get("start") if isinstance(x.get("start"), str) else NA,
                                               "end": x.get("end") if isinstance(x.get("end"), str) else NA}
        v["global"], v["categories"] = glob, cats
        summ = (doc.get("candidate") or {}).get("summary") or {}
        v["worst_setup"] = _worst(summ.get("worst_setup")) or NA
        v["worst_hold"] = _worst(summ.get("worst_hold")) or NA
    elif adir:
        verdict = _load(os.path.join(adir, "verdict.json"), "verdict.json", required=False)
        if isinstance(verdict, dict):
            v["worst_setup"] = _worst(verdict.get("worst_setup")) or absent
            v["worst_hold"] = _worst(verdict.get("worst_hold")) or absent

    # failure location and log summary (the selected attempt)
    if isinstance(att, dict):
        v["failure_location"] = att.get("failure_location", NA)
        v["exit_code"] = att.get("exit_code", NA)
        v["timed_out"] = att.get("timed_out", NA)
        v["log_summary"] = log_summary(adir, repo) if v["failure_location"] not in ("none", NA, None) else NA
    else:
        v["failure_location"] = NOT_RUN if adir is None else NA
        v["exit_code"], v["timed_out"], v["log_summary"] = NA, NA, NA

    # delivery failure: truncation (call.json) or content (parsed.json)
    call = _load(os.path.join(out_dir, f"{code}.call.json"), "call.json", required=False)
    parsed = _load(os.path.join(out_dir, f"{code}.parsed.json"), "parsed.json", required=False)
    final = call.get("final") if isinstance(call, dict) else None
    calls = [c for c in (call.get("calls") or []) if isinstance(c, dict)] if isinstance(call, dict) else []
    v["delivery_check"], v["delivery_lines"] = NA, NA
    if final == "delivery_fail":
        last = calls[-1].get("categories") if calls else None
        if not isinstance(last, list) or CAP_CATEGORY not in last:
            raise FeedbackError(f"FEEDBACK FAIL: {code}.call.json: final delivery_fail without the category "
                                f"{CAP_CATEGORY} in the last call")
        v["delivery_check"], v["delivery_lines"] = CAP_CATEGORY, []
    elif isinstance(parsed, dict) and parsed.get("status") == "delivery_fail":
        reason = parsed.get("reason")
        if reason not in CHECK_NAMES:
            raise FeedbackError(f"FEEDBACK FAIL: {code}.parsed.json: unknown delivery_fail reason {reason!r}")
        v["delivery_check"] = reason
        v["delivery_lines"] = _first_lines(parsed.get("trigger_lines") or [])

    # unavailable: the categories of every call
    v["unavailable_categories"] = NA
    if final == "unavailable" and calls:
        v["unavailable_categories"] = [list(dict.fromkeys(str(x) for x in c.get("categories") or []))
                                       for c in calls]

    # gate
    gate = _load(os.path.join(cdir, "gate.json"), "gate.json", required=False)
    v["gate_rules"], v["gate_lines"] = NA, NA
    if isinstance(gate, dict) and gate.get("passed") is False:
        hits = [h for h in gate.get("hits") or [] if isinstance(h, dict)]
        texts = gate_rule_texts(rules or os.path.join(revise, "rules", "gate_rules.md"))
        ids = []
        for h in hits:
            r = h.get("rule")
            if r not in texts:
                raise FeedbackError(f"FEEDBACK FAIL: gate.json rule {r!r} has no row in gate_rules.md")
            if r not in ids:
                ids.append(r)
        ids.sort(key=lambda r: (1, 0) if r == "unrecognized" else (0, int(r[1:])))
        v["gate_rules"] = [(r, texts[r]) for r in ids]
        lines = _first_lines([h.get("line") for h in hits])
        v["gate_lines"] = [(ln, [r for r in ids if any(h.get("rule") == r and h.get("line") == ln for h in hits)])
                           for ln in lines]
    return v


# ------------------------------------------------------------------------------------------------ rendering
def _s(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Decimal):
        return rp.fmt6(v)
    return str(v)


def _yes_no(v, invert=False):
    if isinstance(v, bool):
        return "是" if v != invert else "否"
    return _s(v)


def _stage(value, checked):
    if value != "pass" or checked is None:
        return _s(value)
    c = _s(checked)
    return f"pass（{c if c.startswith('checked=') else 'checked=' + c}）"


def _area(v):
    n = _num(v)
    return rp.fmt6(n) if n is not None else _s(v)


def _worst_text(w):
    return f"{rp.fmt6(w['slack'])}（{w['corner']}）" if isinstance(w, dict) else _s(w)


def _global_table(g):
    if not isinstance(g, dict):
        return _s(g)
    rows = ["| corner | setup | hold |", "|---|---|---|"]
    rows += [f"| {c} | {_s(g[(c, 'setup')])} | {_s(g[(c, 'hold')])} |" for c in CORNERS]
    return "\n".join(rows)


def _category_table(cats):
    if not isinstance(cats, dict):
        return _s(cats)
    rows = ["| corner | 检查 | 类别 | slack | 起点 | 终点 |", "|---|---|---|---|---|---|"]
    for c in CORNERS:
        for chk in CHECKS:
            for cat in CATEGORIES:
                x = cats[(c, chk, cat)]
                rows.append(f"| {c} | {chk} | {cat} | {_s(x['slack'])} | {_s(x['start'])} | {_s(x['end'])} |")
    return "\n".join(rows)


def _location(v):
    loc = v["failure_location"]
    if loc == "outside_steps":
        return "步骤之外"
    if loc == "no_final_line":
        return f"步骤之外（没有最终判定行；退出码 {_s(v['exit_code'])}，超时 {_s(v['timed_out'])}）"
    if loc in (NA, NOT_RUN, "none", None):
        return _s(loc)
    return f"步骤 {loc}"


def _fenced(text):
    if text == NA:
        return NA
    run = max((len(m) for m in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, run + 1)
    return f"{fence}text\n{text}\n{fence}"


def _values(v):
    lines = v["delivery_lines"]
    cats = v["unavailable_categories"]
    gl = v["gate_lines"]
    return {
        "grade_status": _s(v["grade_status"]),
        "rtl_sim": _stage(v["rtl_sim"], v["checked_rtl"]),
        "gl_sim": _stage(v["gl_sim"], v["checked_gl"]),
        "sta_analysis": _s(v["sta_analysis"]),
        "cfg_L": _s(v["cfg_L"]),
        "area_um2": _area(v["area_um2"]),
        "over_cap": _yes_no(v["within_cap"], invert=True),
        "numeric_target_met": _yes_no(v["numeric_target_met"]),
        "worst_setup": _worst_text(v["worst_setup"]),
        "worst_hold": _worst_text(v["worst_hold"]),
        "global_table": _global_table(v["global"]),
        "category_table": _category_table(v["categories"]),
        "failure_location": _location(v),
        "log_summary": _fenced(v["log_summary"]),
        "delivery_check": (_s(v["delivery_check"]) if v["delivery_check"] not in CHECK_NAMES else
                           f"{CHECK_NAMES[v['delivery_check']]}（{v['delivery_check']}）"),
        "delivery_lines": ("、".join(f"第 {n} 行" for n in lines) or NO_LINE) if isinstance(lines, list)
        else _s(lines),
        "unavailable_categories": ("；".join(f"第 {i} 次调用：{'、'.join(c) or NA}" for i, c in enumerate(cats, 1))
                                   if isinstance(cats, list) else _s(cats)),
        "gate_rules": ("\n".join(f"- {r}：{t}" for r, t in v["gate_rules"]) if isinstance(v["gate_rules"], list)
                       else _s(v["gate_rules"])),
        "gate_lines": (("\n".join(f"- 第 {n} 行（{'、'.join(rs)}）" for n, rs in gl) or NO_RTL_LINE)
                       if isinstance(gl, list) else _s(gl)),
    }


def _fill(template, values, name):
    def sub(m):
        if m.group(1) not in values:
            raise FeedbackError(f"FEEDBACK FAIL: template {name} uses an unknown placeholder {{{m.group(1)}}}")
        return values[m.group(1)]
    return _PLACEHOLDER.sub(sub, template)


def _r2_code(m2, r1_code):
    hits = [e["code"] for e in m2["entries"] if e["prev_code"] == r1_code]
    if len(hits) != 1:
        raise mapping.MappingError(f"MAPPING FAIL: no single round-2 code has the previous code {r1_code}")
    return hits[0]


def render(r1_code, case=None, sealed=None, templates=None, repo=None):
    """Bytes of the round-2 feedback for round-1 candidate r1_code; written to
    revise/prompts/r2/<r1_code>_feedback.md (see the module doc)."""
    case = case or rp.CASE
    revise = os.path.join(case, "revise")
    templates = templates or TEMPLATES
    m1 = mapping.load(1, revise=revise, sealed=sealed)
    m2 = mapping.load(2, revise=revise, sealed=sealed)
    mapping.model_of(m1, r1_code)                      # the code must be in the round-1 mapping
    _r2_code(m2, r1_code)
    st = _load(os.path.join(revise, "results", "r1", r1_code, "status.json"), f"status.json of {r1_code}")
    state = st.get("state")
    if state not in TEMPLATE_OF:
        raise FeedbackError(f"FEEDBACK FAIL: {r1_code}: round-1 state {state!r} has no feedback template")
    v = mechanical_view(r1_code, 1, case=case, repo=repo)
    name = TEMPLATE_OF[state]
    body = _fill(_text(os.path.join(templates, f"{name}.md")), _values(v), f"{name}.md")
    endings = load_endings(templates)
    if state in ("unavailable", "delivery_fail", "gate_reject"):
        key = "not_evaluated"
    elif state == "infra_fail":
        key = "evaluated_no_analysis"
    elif state == "grade_fail":
        key = "evaluated_valid" if v["sta_analysis"] == "pass" else "evaluated_no_analysis"
    else:
        key = "evaluated_valid"
    data = (body.rstrip("\n") + "\n\n" + endings[key] + "\n").encode("utf-8")
    if state == "unavailable":
        p = os.path.join(revise, "prompts", "r1", f"{r1_code}_prompt.md")
        if not prereg.committed_unchanged(p):
            raise FeedbackError(f"FEEDBACK FAIL: the round-1 prompt {p} is missing, untracked or differs from HEAD")
        data += ("\n" + endings["r1_prompt_header"] + "\n\n").encode("utf-8") + rp.read_bytes(p)
    if b"\r" in data.replace(b"\r\n", b"") or b"\r\n" in data:
        raise FeedbackError(f"FEEDBACK FAIL: {r1_code}: the feedback would not be LF-only text")
    rp.write_new_or_same(os.path.join(revise, "prompts", "r2", f"{r1_code}_feedback.md"), data)
    return data


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or not mapping.CODE_RE.fullmatch(args[0]):
        print("usage: feedback.py <round-1 code>", file=sys.stderr)
        return 2
    try:
        render(args[0])
    except (FeedbackError, mapping.MappingError, rp.RevpathsError) as e:
        print(str(e), flush=True)
        return 1
    print(f"FEEDBACK {args[0]}: revise/prompts/r2/{args[0]}_feedback.md", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
