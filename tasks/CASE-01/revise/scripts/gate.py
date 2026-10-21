"""Contract gate G1-G8 of CASE-01 stage B (implementation plan Task 4; protocol v0.5 section 7.2; revisions RV-01).

Rules (texts and recognition method: revise/rules/gate_rules.md):
  G1 module dot4sat with exactly the 7 ports of contract section 1 (name, direction, width)   contract
  G2 no lint-listed system task (grade.LINT_SYSTF, names without "$"), no `include             contract
  G3 one module in the file; G4 no parameter; G5 no compiler directive; G6 sequential always only @(posedge clk),
     combinational only assign / wire with assignment / always @* / always @(*); no initial, # delay, negedge (an
     event control "@" anywhere else than directly after "always" is also G6); G7 clk only in the module header port
     list, in port declarations and directly after posedge                                      extra (stage B)
  G8 DECLARED_L in 1..3                                                                          extra
  unrecognized ("门槛无法识别"): a character the tokenizer does not know, a failed or unusable Yosys read, or Yosys and
     the tokenizer disagreeing on the number of modules. Also a gate_reject, reported separately, never as a proven
     rule violation.
G1 and the module set come from Yosys, in two separate fresh processes (RV-01), both via limits.run_limited(kind=
"yosys") from the directory of the RTL file (so diagnostics name the file by its base name only):
  stage 1: yosys -q -p "read_verilog <file>"                         front-end read check only
  stage 2 (only after stage 1 succeeded): yosys -q -p "read_verilog -lib <file>; write_json <work>/ports.json"
No proc, hierarchy, synth, flatten or clean-up pass is ever run. A non-zero exit, timeout, output over the limit or
otherwise incomplete, or a JSON that is missing or not a usable module description (RV-01 item 4) sets yosys_problem
and an "unrecognized" hit; a JSON from an earlier run is never used (every call works in a new directory).
Infrastructure faults are not candidate verdicts and raise GateInfraError instead (never written into gate.json):
failed or unconfirmed process cleanup (kill_fail True: KILL FAIL, round.py writes a stop), Yosys not startable
(IsolationFail, OSError e.g. yosys missing from PATH), a supervision failure, an unusable path, a work directory or
evidence write failure. Stage-1 warnings are kept as evidence only (no rule rejects on
warnings). The tokenizer rules are recorded in every case, also when Yosys failed or the module counts disagree.
Evidence: every call writes <work_dir>/<new dir>/ with stage<n>.out, stage<n>.err, stage<n>.proc.json, ports.json and
evidence.json (argv, rc, flags, stderr text); work_dir defaults to tasks/CASE-01/runs/gate/ (git-ignored, kept).
gate.json (round.py ingest; format read by feedback.py): {"passed", "hits": [{"rule", "line", "kind", "text"}],
"yosys_problem"}; text is the RTL line verbatim without its line ending (None for line 0 = no RTL line).
grade.LINT_SYSTF is read from the frozen scripts/grade.py by explicit path under an alias, with its two sibling
imports (check_sim, logcheck) served from the same directory by explicit path; nothing is put on sys.path, no bare
module name is registered and no bytecode is written (ruling R25).
CLI (WSL): python3 -B revise/scripts/gate.py <rtl> <L> [--json <out>] [--work-dir <dir>]
  prints "GATE PASS" or one "GATE FAIL <rule> line <n> (<contract|extra>)" per hit; exit 0 / 1 (plan Task 4).
  Extensions beyond the plan's CLI (for the revisions record): --work-dir <dir> (where the per-run evidence
  directories go; default tasks/CASE-01/runs/gate/); a "YOSYS PROBLEM: <text>" line after the GATE FAIL lines when
  yosys_problem is set; exit 2 with "KILL FAIL: ..." (cleanup failed / unconfirmed) or "GATE ERROR: ..." (other
  infrastructure fault, unreadable RTL file, bad arguments) and no --json output. Python standard library only."""
import argparse
import builtins
import datetime
import importlib.util
import json
import os
import re
import secrets
import sys
from dataclasses import dataclass, field

import limits
import revpaths as rp

CASE = rp.CASE
GRADE_PY = os.path.join(CASE, "scripts", "grade.py")
DEFAULT_WORK = os.path.join(CASE, "runs", "gate")
EXPECTED_PORTS = (("clk", "input", 1), ("rst", "input", 1), ("in_valid", "input", 1), ("in_a", "input", 64),
                  ("in_b", "input", 64), ("out_valid", "output", 1), ("out_data", "output", 32))
TOP = "dot4sat"
L_RANGE = (1, 3)                                     # config/f1.cfg L_max = 3
RULE_ORDER = {f"G{i}": i for i in range(1, 9)}
RULE_ORDER["unrecognized"] = 9
DIRECTIONS = ("input", "output", "inout")

# Verilog-2005 keywords (IEEE 1364-2005 Annex B); listed in gate_rules.md
KEYWORDS = tuple("""always and assign automatic begin buf bufif0 bufif1 case casex casez cell cmos config deassign
default defparam design disable edge else end endcase endconfig endfunction endgenerate endmodule endprimitive
endspecify endtable endtask event for force forever fork function generate genvar highz0 highz1 if ifnone incdir
include initial inout input instance integer join large liblist library localparam macromodule medium module nand
negedge nmos nor noshowcancelled not notif0 notif1 or output parameter pmos posedge primitive pull0 pull1 pulldown
pullup pulsestyle_ondetect pulsestyle_onevent rcmos real realtime reg release repeat rnmos rpmos rtran rtranif0
rtranif1 scalared showcancelled signed small specify specparam strong0 strong1 supply0 supply1 table task time tran
tranif0 tranif1 tri tri0 tri1 triand trior trireg unsigned use uwire vectored wait wand weak0 weak1 while wire wor
xnor xor""".split())
_KW = frozenset(KEYWORDS)
MODULE_KW = ("module", "macromodule")
OPS3 = ("<<<", ">>>", "===", "!==")
OPS2 = ("<=", ">=", "==", "!=", "&&", "||", "<<", ">>", "**", "~&", "~|", "~^", "^~", "+:", "-:", "->")
OPS1 = set("+-*/%<>=!&|^~?:;,.()[]{}@")
_WS = " \t\r\n\f\v"
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
_SYSTASK = re.compile(r"\$[A-Za-z0-9_$]+")
_BASED = re.compile(r"(?:[0-9][0-9_]*)?'[sS]?[bBoOdDhH][ \t]*[0-9a-fA-FxXzZ?][0-9a-fA-FxXzZ?_]*")
_REAL = re.compile(r"[0-9][0-9_]*\.[0-9][0-9_]*(?:[eE][+-]?[0-9][0-9_]*)?|[0-9][0-9_]*[eE][+-]?[0-9][0-9_]*")
_DEC = re.compile(r"[0-9][0-9_]*")
_SAFE_PATH = re.compile(r"^[A-Za-z0-9_./+-]+$")
_ERR_LINE = re.compile(r":(\d+):\s*ERROR")


class GateError(Exception):
    pass


class GateInfraError(GateError):
    """An infrastructure fault of the gate run, never a verdict on the candidate (fix round 1): Yosys could not be
    started (IsolationFail, OSError such as yosys missing from PATH), its supervision failed (SupervisionError), its
    process cleanup failed or is unconfirmed (kill_fail True: killed_pids_alive / cleanup_unconfirmed), the work
    directory or the evidence could not be written, or a path cannot be used in a Yosys command. It is raised, so it
    can never be written into gate.json; round.py writes a KILL FAIL stop for kill_fail and otherwise refuses.
    evidence: a dict of plain values (stage, dir, argv, rc, pid, killed_pids_alive, cleanup_unconfirmed, error)."""

    def __init__(self, message, kill_fail=False, evidence=None):
        super().__init__(message)
        self.kill_fail = bool(kill_fail)
        self.evidence = dict(evidence or {})


@dataclass
class Token:
    kind: str
    text: str
    line: int


@dataclass
class Hit:
    rule: str
    line: int
    kind: str
    text: object = None


@dataclass
class GateResult:
    passed: bool
    hits: list
    yosys_problem: object
    evidence: dict = field(default_factory=dict)      # not part of gate.json


# ------------------------------------------------------------------------------------------------ grade.LINT_SYSTF
_LINT = None


def _exec_frozen(path, alias, provided):
    """Execute a frozen script by explicit path as module <alias>: source compiled in memory (no bytecode file), the
    names in `provided` served to its import statements, nothing registered in sys.modules."""
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    with open(path, "rb") as f:
        code = compile(f.read(), path, "exec", dont_inherit=True)

    def _import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in provided:
            return provided[name]
        return builtins.__import__(name, globals, locals, fromlist, level)

    b = dict(builtins.__dict__)
    b["__import__"] = _import
    mod.__dict__["__builtins__"] = b
    exec(code, mod.__dict__)
    return mod


def lint_systf():
    """grade.LINT_SYSTF (names without "$") read from the frozen scripts/grade.py (see the module doc)."""
    global _LINT
    if _LINT is None:
        d = os.path.dirname(GRADE_PY)
        sib = {n: _exec_frozen(os.path.join(d, n + ".py"), f"frozen_{n}_for_gate", {}) for n in ("check_sim",
                                                                                                    "logcheck")}
        g = _exec_frozen(GRADE_PY, "frozen_grade_for_gate", sib)
        lint = g.LINT_SYSTF
        if not isinstance(lint, tuple) or not lint or not all(isinstance(x, str) for x in lint):
            raise GateError("grade.LINT_SYSTF is not a non-empty tuple of names")
        _LINT = lint
    return _LINT


# ------------------------------------------------------------------------------------------------ tokenizer
def tokenize(src):
    """Tokens of the Verilog text (table in gate_rules.md); comments and strings are dropped."""
    toks, i, n, line = [], 0, len(src), 1

    def add(kind, text, ln):
        toks.append(Token(kind, text, ln))

    while i < n:
        c = src[i]
        if c in _WS:
            if c == "\n":
                line += 1
            i += 1
            continue
        start_line = line
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                add("unknown", "/*", start_line)
                line += src.count("\n", i)
                i = n
                continue
            line += src.count("\n", i, j + 2)
            i = j + 2
            continue
        if c == '"':
            j = i + 1
            while j < n and src[j] not in '"\n':
                j += 2 if src[j] == "\\" and j + 1 < n and src[j + 1] != "\n" else 1
            if j < n and src[j] == '"':
                i = j + 1
            else:
                add("unknown", '"', start_line)
                i = j
            continue
        if src.startswith("(*", i):
            k = i + 2
            while k < n and src[k] in _WS:
                k += 1
            if not (k < n and src[k] == ")"):
                j = src.find("*)", i + 2)
                if j < 0:
                    add("unknown", "(*", start_line)
                    line += src.count("\n", i)
                    i = n
                    continue
                add("attr", src[i:j + 2], start_line)
                line += src.count("\n", i, j + 2)
                i = j + 2
                continue
        if c == "\\":
            j = i + 1
            while j < n and src[j] not in _WS:
                j += 1
            if j == i + 1:
                add("unknown", "\\", start_line)
            else:
                add("esc_ident", src[i + 1:j], start_line)
            i = j
            continue
        if c == "$":
            m = _SYSTASK.match(src, i)
            if m:
                add("systask", m.group(), start_line)
                i = m.end()
            else:
                add("unknown", "$", start_line)
                i += 1
            continue
        if c == "`":
            m = _IDENT.match(src, i + 1)
            if m:
                add("directive", "`" + m.group(), start_line)
                i = m.end()
            else:
                add("unknown", "`", start_line)
                i += 1
            continue
        if c.isascii() and (c.isdigit() or c == "'"):
            m = _BASED.match(src, i) or _REAL.match(src, i) or _DEC.match(src, i)
            if m:
                add("number", m.group(), start_line)
                i = m.end()
            else:
                add("unknown", c, start_line)
                i += 1
            continue
        m = _IDENT.match(src, i) if c.isascii() else None
        if m:
            w = m.group()
            add("kw" if w in _KW else "ident", w, start_line)
            i = m.end()
            continue
        if c == "#":
            add("delay", "#", start_line)
            i += 1
            continue
        for op in OPS3 + OPS2:
            if src.startswith(op, i):
                add("op", op, start_line)
                i += len(op)
                break
        else:
            add("op" if c in OPS1 else "unknown", c, start_line)
            i += 1
    return toks


# ------------------------------------------------------------------------------------------------ structure
def _is(t, kind, text=None):
    return t is not None and t.kind == kind and (text is None or t.text == text)


def _is_clk(t):
    return t is not None and t.kind in ("ident", "esc_ident") and t.text == "clk"


def _scan(toks):
    """Module declarations [(name or None, kw line, kw index)], and per token index the region: "header" (module
    keyword up to the ';' ending the header), "portdecl" (input/output/inout up to ';'), or None; plus the square
    bracket depth before each token."""
    modules, region, depth = [], [None] * len(toks), [0] * len(toks)
    sq, mode, paren = 0, None, 0
    for i, t in enumerate(toks):
        depth[i] = sq
        if _is(t, "kw") and t.text in MODULE_KW:
            nxt = toks[i + 1] if i + 1 < len(toks) else None
            name = nxt.text if nxt is not None and nxt.kind in ("ident", "esc_ident") else None
            modules.append((name, t.line, i))
            mode, paren = "header", 0
        elif mode is None and _is(t, "kw") and t.text in DIRECTIONS:
            mode = "portdecl"
        region[i] = mode
        if _is(t, "op", "["):
            sq += 1
        elif _is(t, "op", "]"):
            sq = max(0, sq - 1)
        elif _is(t, "op", "("):
            paren += 1
        elif _is(t, "op", ")"):
            paren = max(0, paren - 1)
        elif _is(t, "op", ";") and (mode == "portdecl" or (mode == "header" and paren == 0)):
            mode = None
    return modules, region, depth


def token_rules(tokens):
    """Hits of G2-G7 and unrecognized from the tokens (attributes take no part); deduplicated, sorted."""
    lint = set(lint_systf())
    toks = [t for t in tokens if t.kind != "attr"]
    modules, region, depth = _scan(toks)
    hits = []
    if len(modules) != 1:
        hits.append(Hit("G3", modules[1][1] if len(modules) > 1 else 0, "extra"))
    for i, t in enumerate(toks):
        prev = toks[i - 1] if i > 0 else None
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if t.kind == "systask" and t.text[1:] in lint:
            hits.append(Hit("G2", t.line, "contract"))
        elif t.kind == "directive":
            if t.text == "`include":
                hits.append(Hit("G2", t.line, "contract"))
            hits.append(Hit("G5", t.line, "extra"))
        elif _is(t, "kw", "parameter"):
            hits.append(Hit("G4", t.line, "extra"))
        elif _is(t, "kw", "always"):
            if not _always_ok(toks, i):
                hits.append(Hit("G6", t.line, "extra"))
        elif (_is(t, "kw", "initial") or t.kind == "delay" or _is(t, "kw", "negedge")
              or (_is(t, "op", "@") and not _is(prev, "kw", "always"))):
            hits.append(Hit("G6", t.line, "extra"))
        elif t.kind == "unknown":
            hits.append(Hit("unrecognized", t.line, "extra"))
        if _is_clk(t) and not _clk_ok(prev, nxt, region[i], depth[i]):
            hits.append(Hit("G7", t.line, "extra"))
    return _sorted(hits)


def _always_ok(toks, i):
    seq = toks[i + 1:i + 6]

    def at(k, kind, text=None):
        return k < len(seq) and _is(seq[k], kind, text)

    if not at(0, "op", "@"):
        return False
    if at(1, "op", "*"):
        return True
    if at(1, "op", "(") and at(2, "op", "*") and at(3, "op", ")"):
        return True
    return (at(1, "op", "(") and at(2, "kw", "posedge") and len(seq) > 3 and _is_clk(seq[3])
            and at(4, "op", ")"))


def _clk_ok(prev, nxt, region, depth):
    if _is(prev, "kw", "posedge"):
        return True
    if region not in ("header", "portdecl") or depth != 0:
        return False
    prev_ok = prev is not None and (prev.kind == "kw" or (prev.kind == "op" and prev.text in (",", "(", "]")))
    return prev_ok and nxt is not None and nxt.kind == "op" and nxt.text in (",", ")", ";")


def _sorted(hits):
    seen, out = set(), []
    for h in hits:
        k = (h.rule, h.line, h.kind)
        if k not in seen:
            seen.add(k)
            out.append(h)
    return sorted(out, key=lambda h: (h.line, RULE_ORDER[h.rule], h.kind))


def _port_line(toks, name, modules, region):
    """Line of the declaration of port <name> in module dot4sat: a port declaration statement first, then the
    header; None when not found."""
    starts = [m for m in modules if m[0] == TOP]
    if not starts:
        return None
    lo = starts[0][2]
    later = [m[2] for m in modules if m[2] > lo]
    hi = later[0] if later else len(toks)
    for want in ("portdecl", "header"):
        for i in range(lo + 2, hi):
            t = toks[i]
            if region[i] == want and t.kind in ("ident", "esc_ident") and t.text == name:
                return t.line
    return None


def structure_rules(ports, tokens):
    """G1 from the Yosys module description {module: {port: (direction, width)}}; a module count different from the
    tokenizer's -> unrecognized (line 0). The full module set is used: no top selection, no removal."""
    toks = [t for t in tokens if t.kind != "attr"]
    modules, region, _ = _scan(toks)
    hits = []
    if len(ports) != len(modules):
        hits.append(Hit("unrecognized", 0, "extra"))
    mod_line = modules[0][1] if modules else 0
    top = ports.get(TOP)
    if top is None:
        hits.append(Hit("G1", mod_line, "contract"))
        return _sorted(hits)
    top_line = next((m[1] for m in modules if m[0] == TOP), mod_line)
    expected = {p: (d, w) for p, d, w in EXPECTED_PORTS}
    for p, (d, w) in expected.items():
        if top.get(p) != (d, w):
            ln = _port_line(toks, p, modules, region) if p in top else None
            hits.append(Hit("G1", ln or top_line, "contract"))
    for p in top:
        if p not in expected:
            hits.append(Hit("G1", _port_line(toks, p, modules, region) or top_line, "contract"))
    return _sorted(hits)


# ------------------------------------------------------------------------------------------------ Yosys
def _new_dir(work_dir):
    base = os.path.abspath(work_dir or DEFAULT_WORK)  # Yosys runs from the RTL directory: never relative
    os.makedirs(base, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    d = os.path.join(base, f"{stamp}-{os.getpid()}-{secrets.token_hex(3)}")
    os.makedirs(d)                                   # new: an existing directory is an error, never reused
    return d


def _first_error(text):
    for ln in text.splitlines():
        if "ERROR" in ln:
            return ln.strip()
    return ""


def _infra(label, n, d, ev, message, kill_fail=False):
    info = {"stage": n, "dir": d, "argv": ev.get("argv"), "rc": ev.get("rc"), "pid": ev.get("pid"),
            "killed_pids_alive": list(ev.get("killed_pids_alive") or []),
            "cleanup_unconfirmed": bool(ev.get("cleanup_unconfirmed")), "error": ev.get("error")}
    return GateInfraError(f"{label}: {message}", kill_fail=kill_fail, evidence=info)


def _stage(n, argv, cwd, d, evidence):
    """Run one stage; returns a problem text (RV-01 item 4: non-zero exit, timeout, output over the limit or
    incomplete) or None; raises GateInfraError for infrastructure faults (KILL FAIL, start or supervision failure,
    evidence write failure). The evidence entry keeps rc, flags and the output texts."""
    label = {1: "stage 1 (read_verilog)", 2: "stage 2 (read_verilog -lib; write_json)"}[n]
    ev = {"argv": argv, "cwd": cwd}
    evidence[f"stage{n}"] = ev
    try:
        r = limits.run_limited(argv, "yosys", cwd=cwd, proc_path=os.path.join(d, f"stage{n}.proc.json"))
    except limits.SupervisionError as e:
        ev.update(error=f"SupervisionError: {e}", pid=e.pid, rc=e.rc, killed_pids_alive=e.killed_pids_alive,
                  cleanup_unconfirmed=e.cleanup_unconfirmed)
        if e.killed_pids_alive or e.cleanup_unconfirmed:
            raise _infra(label, n, d, ev, "KILL FAIL (supervision failed and the process cleanup is not confirmed)",
                         kill_fail=True) from e
        raise _infra(label, n, d, ev, f"supervision failed ({e.cause_type or 'error'})") from e
    except (limits.IsolationFail, OSError) as e:
        ev.update(error=f"{e.__class__.__name__}: {e}")
        raise _infra(label, n, d, ev, f"could not start ({e.__class__.__name__}: {e})") from e
    err = r.stderr.decode("utf-8", "replace")
    ev.update(rc=r.rc, timed_out=r.timed_out, stdout_over=r.stdout_over, stderr_over=r.stderr_over,
              stdout_bytes=r.stdout_bytes, stderr_bytes=r.stderr_bytes, killed_pids_alive=r.killed_pids_alive,
              cleanup_unconfirmed=r.cleanup_unconfirmed, output_error=r.output_error,
              stdout=r.stdout.decode("utf-8", "replace"), stderr=err)
    if r.killed_pids_alive or r.cleanup_unconfirmed:
        raise _infra(label, n, d, ev, "KILL FAIL (process cleanup failed or not confirmed)", kill_fail=True)
    try:
        for suffix, data in (("out", r.stdout), ("err", r.stderr)):
            with open(os.path.join(d, f"stage{n}.{suffix}"), "wb") as f:
                f.write(data)
    except OSError as e:
        ev.update(error=f"{e.__class__.__name__}: {e}")
        raise _infra(label, n, d, ev, f"evidence could not be written ({e.__class__.__name__})") from e
    if r.timed_out:
        return f"{label}: timed out (output incomplete)"
    if r.stdout_over or r.stderr_over:
        return f"{label}: output over the limit (output incomplete)"
    if r.output_error:
        return f"{label}: output incomplete"
    if r.rc != 0:
        e = _first_error(err)
        return f"{label}: rc={r.rc}" + (f": {e}" if e else "")
    return None


def _read_ports(path):
    """{module: {port: (direction, width)}} from the write_json output; raises ValueError when unusable."""
    if not os.path.isfile(path):
        raise ValueError("no JSON written")
    with open(path, "rb") as f:
        data = f.read()
    if not data:
        raise ValueError("JSON is empty")
    doc = json.loads(data.decode("utf-8"))
    mods = doc.get("modules") if isinstance(doc, dict) else None
    if not isinstance(mods, dict):
        raise ValueError("no modules object")
    out = {}
    for name, m in mods.items():
        ports = m.get("ports") if isinstance(m, dict) else None
        if not isinstance(ports, dict):
            raise ValueError(f"module {name}: no ports object")
        out[name] = {}
        for p, v in ports.items():
            if not isinstance(v, dict) or v.get("direction") not in DIRECTIONS or not isinstance(v.get("bits"), list):
                raise ValueError(f"module {name} port {p}: no usable direction / bits")
            out[name][p] = (v["direction"], len(v["bits"]))
    return out


def yosys_ports(rtl_path, work_dir=None, evidence=None):
    """(modules, None) or (None, problem): the two-stage read of RV-01 (module doc). evidence (a dict) receives the
    directory and per-stage records."""
    evidence = {} if evidence is None else evidence
    try:
        d = _new_dir(work_dir)
    except OSError as e:
        raise GateInfraError(f"work directory could not be created ({e.__class__.__name__}: {e})",
                             evidence={"dir": work_dir or DEFAULT_WORK, "error": str(e)}) from e
    evidence["dir"] = d
    rtl = os.path.abspath(rtl_path)
    cwd, base = os.path.dirname(rtl), os.path.basename(rtl)
    out = os.path.join(d, "ports.json")
    if not _SAFE_PATH.match(base) or not _SAFE_PATH.match(out):
        raise GateInfraError("file or work path not usable in a Yosys command",
                             evidence={"dir": d, "rtl": rtl, "error": "unsafe path"})
    prob = _stage(1, ["yosys", "-q", "-p", f"read_verilog {base}"], cwd, d, evidence)
    if prob:
        return None, prob
    prob = _stage(2, ["yosys", "-q", "-p", f"read_verilog -lib {base}; write_json {out}"], cwd, d, evidence)
    if prob:
        return None, prob
    try:
        return _read_ports(out), None
    except (ValueError, OSError, UnicodeDecodeError) as e:
        return None, f"stage 2 (read_verilog -lib; write_json): JSON unreadable ({e})"


# ------------------------------------------------------------------------------------------------ gate
def _problem_line(problem, nlines):
    m = _ERR_LINE.search(problem or "")
    if m and 1 <= int(m.group(1)) <= nlines:
        return int(m.group(1))
    return 0


def gate(rtl_path, declared_L, work_dir=None):
    """GateResult of one candidate file (module doc)."""
    with open(rtl_path, "rb") as f:
        text = f.read().decode("utf-8", "replace")
    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in text.split("\n")]
    tokens = tokenize(text)
    hits = list(token_rules(tokens))
    evidence = {}
    try:
        ports, problem = yosys_ports(rtl_path, work_dir, evidence)
    except GateInfraError as e:
        if evidence.get("dir"):                       # best effort: the fault is kept with the run's evidence
            try:
                _write_evidence(evidence["dir"], dict(evidence, infra_error=str(e), kill_fail=e.kill_fail))
            except OSError:
                pass
        raise
    if problem:
        hits.append(Hit("unrecognized", _problem_line(problem, len(lines)), "extra"))
    else:
        hits.extend(structure_rules(ports, tokens))
    if not (isinstance(declared_L, int) and not isinstance(declared_L, bool)
            and L_RANGE[0] <= declared_L <= L_RANGE[1]):
        hits.append(Hit("G8", 0, "extra"))
    hits = _sorted(hits)
    for h in hits:
        h.text = lines[h.line - 1] if 1 <= h.line <= len(lines) else None
    res = GateResult(passed=not hits and problem is None, hits=hits, yosys_problem=problem, evidence=evidence)
    if evidence.get("dir"):
        try:
            _write_evidence(evidence["dir"], dict(evidence, gate=to_doc(res),
                                                  declared_L=declared_L if isinstance(declared_L, (int, str))
                                                  else repr(declared_L)))
        except OSError as e:
            raise GateInfraError(f"evidence could not be written ({e.__class__.__name__}: {e})",
                                 evidence={"dir": evidence["dir"], "error": str(e)}) from e
    return res


def _write_evidence(d, rec):
    with open(os.path.join(d, "evidence.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1, ensure_ascii=False, default=str)
        f.write("\n")


def to_doc(res):
    return {"passed": res.passed,
            "hits": [{"rule": h.rule, "line": h.line, "kind": h.kind, "text": h.text} for h in res.hits],
            "yosys_problem": res.yosys_problem}


def doc_bytes(res):
    """gate.json bytes (the same serialization as round.gate_bytes)."""
    return (json.dumps(to_doc(res), indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="CASE-01 stage B contract gate G1-G8 (WSL)")
    ap.add_argument("rtl")
    ap.add_argument("L")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--work-dir")
    a = ap.parse_args(argv)
    try:
        L = int(a.L) if re.fullmatch(r"[+-]?[0-9]+", a.L) else a.L
        res = gate(a.rtl, L, a.work_dir)
    except GateInfraError as e:
        print(f"{'KILL FAIL' if e.kill_fail else 'GATE ERROR'}: {e}", flush=True)
        return 2
    except (OSError, GateError) as e:
        print(f"GATE ERROR: {e.__class__.__name__}: {e}", flush=True)
        return 2
    if res.passed:
        print("GATE PASS", flush=True)
    for h in res.hits:
        print(f"GATE FAIL {h.rule} line {h.line} ({h.kind})", flush=True)
    if res.yosys_problem:
        print(f"YOSYS PROBLEM: {res.yosys_problem}", flush=True)
    if a.json_out:
        with open(a.json_out, "wb") as f:
            f.write(doc_bytes(res))
    return 0 if res.passed else 1


if __name__ == "__main__":
    sys.exit(main())
