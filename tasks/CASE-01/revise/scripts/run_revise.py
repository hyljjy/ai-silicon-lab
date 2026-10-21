"""Windows run shell of CASE-01 stage B (implementation plan Task 10; protocol v0.4 sections 6, 7.1, 16).

Run from Git Bash in the repository root with Windows Python (claude.exe is a Windows program); a round can take
up to 3 x 2 x 30 minutes, so start it in the background with its output in a log file:
  python -B tasks/CASE-01/revise/scripts/run_revise.py --smoke probe|canary|rehearsal
  python -B tasks/CASE-01/revise/scripts/run_revise.py --commit-codes <r> [--dry-run]
  python -B tasks/CASE-01/revise/scripts/run_revise.py --round <r>
  python -B tasks/CASE-01/revise/scripts/run_revise.py --resume <r>
<r> is 1 or 2 (anything else: exit 2). Tests only: --claude-cmd <json list>, --sandbox-root <dir>, --repo-root <dir>,
--no-tags (skips the pre-registration tag check; refused once any revise-prereg* tag exists).

Exit codes: 0 done; 1 refused (PREREG / PREFLIGHT / DISK / STOPPED / LOCKED / MAPPING / PROMPT / ATTEMPTS ...;
in round modes nothing was called and no attempt was used) or a smoke run that failed (an ordinary per-model smoke
failure, or a disk shortage found before a later smoke call: earlier smoke calls may then have run); 2 usage; 3 a global stop was raised (prompt hash mismatch, KILL FAIL,
old call not confirmed gone, ISOLATION FAIL, disk short before a formal call); 4 the public-answer
redaction hit inside the first verilog block.

Preconditions (round modes): round_lock(r, "call"); no open stop on either side; prereg.problems("formal") (smoke:
"smoke"); reused files; disk; mapping.load(r); committed prompts; preflight (CLI sha256 vs revise/rules/cli.sha256,
--version, the settings files' sha256 vs revise/models/originals.sha256, `auth status --json` loggedIn), each command
under run_limited(kind="preflight"). Expected values: expected_tentative.json (smoke), expected.json (rounds).

State machine (revise/outputs/r<r>/attempts.json, codes sorted, no times and no model names): per code "state"
(pending | running1 | await_retry | running2 | final), "consumed" (calls started; incremented and saved before the
call, never decreased, never above 2), "final" (null | "parse" | "delivery_fail" | "unavailable") and "calls"
(categories and decisions per call). Raw stdout/stderr go chunk by chunk to <sandbox>/raw/r<r>/<code>/call<n>.jsonl /
.err, the lifecycle record to call<n>.proc.json, details to call<n>.meta.json. The repository gets only <code>.call.json
(categories and decisions), <code>.md (redacted public answer, for final parse or delivery_fail), <code>.parsed.json,
the candidate (extract.write_candidate from the RAW answer), r<r>_extracted.jsonl rows and status.md.
Text and hashes follow the plan ("文本和哈希" 1-5). Python standard library only.

Call failures (Codex BC1-03): OSError / limits.IsolationFail from run_limited = the CLI never ran (launch problem,
REASON_ISOLATION stop); limits.SupervisionError = the CLI had started and supervising it failed: the call counts as an
interrupted call (classified from the output captured so far), and a failed or unconfirmed emergency cleanup raises
REASON_KILL. Recovery (--resume, Codex BC1-01): without a usable lifecycle record (call<n>.proc.json) the old call
cannot be confirmed gone -> REASON_RESUME stop (there is no "never started" inference); a record that itself says the
cleanup failed (alive_after / cleanup_unconfirmed) -> REASON_KILL; a "not_started" record -> REASON_ISOLATION (as when
the launch failure is seen live).

Batch D (Codex BC1-08..11): a process ownership or cleanup failure (ISOLATION FAIL, KILL FAIL, a supervision failure
whose cleanup failed) in a smoke call or a preflight command writes a persistent stop at once and nothing else is
launched (exit 3); smoke and smoke-preflight stops are round-1 call-side stops with details["smoke"] = kind (no model
name), checked by every smoke run and every formal run (check_stops). Ordinary smoke failures stay per model. Both
disk volumes are checked before every model call (formal, retry, smoke) and before "consumed" moves; a shortage in a
formal round raises REASON_DISK with the measured values and no other code is called. Preflight commands must exit 0;
revise/models/originals.sha256 is parsed strictly and every model's settings hash is verified. Smoke prompt bytes
(system prompt and stdin) are rebuilt from the frozen sources with build_prompt.py and must match before any launch;
the canary words come from smoke_system.md / smoke_user.md.

Batch C: a disk measurement whose process cleanup failed (revpaths.kill_fail_problems: the WSL df left processes or
their exit cannot be confirmed) writes a REASON_KILL stop (round setup, before a formal call, smoke) instead of a
plain DISK FAIL, prints the instruction to commit it now (ruling R12) and exits 3."""
import argparse
import dataclasses
import datetime
import json
import os
import re
import secrets
import sys

import build_prompt          # before classify: classify puts diag/scripts (it also has a build_prompt.py) first
import classify
import extract
import limits
import mapping
import prereg
import revpaths as rp
import stops

sys.path.insert(0, rp.DIAG_SCRIPTS)
_HERE = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
for _mod in (build_prompt, build_prompt.bp):
    if os.path.normcase(os.path.dirname(os.path.abspath(_mod.__file__))) != _HERE:
        raise ImportError(f"run_revise needs revise/scripts/{os.path.basename(_mod.__file__)}, not the stage A one")
import privacy_check  # noqa: E402  (read-only reuse of stage A: account e-mail and user-directory pattern)

CLI_PATH = r"D:\study\diag_sandbox\bin\claude-2.1.296.exe"
CLI_VERSION = "2.1.296"
MAX_OUTPUT_TOKENS = "32000"
CAP_PROBE_TOKENS = "64"
CANARY_RE = re.compile(r"暗号是：([^。\s]+)。")   # the canary words of smoke_system.md / smoke_user.md
SMOKE_STOP_ROUND = 1      # smoke stops are written as round-1 call-side stops (details["smoke"] = kind)
SMOKE_KINDS = ("probe", "canary", "rehearsal")
HIDDEN = "<已隐去>"
WORKDIR_RE = re.compile(r"rv-[0-9a-f]{12}")
STATES = ("pending", "running1", "await_retry", "running2", "final")
FINALS = ("parse", "delivery_fail", "unavailable")
EXIT_OK, EXIT_REFUSED, EXIT_USAGE, EXIT_STOP, EXIT_PRIVATE = 0, 1, 2, 3, 4
CLI_FLAGS = ["--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
             "--output-format", "stream-json", "--verbose"]
REASON_PROMPT = "系统提示或题目的字节哈希与预期不符（外壳可能有问题，先排查再重试）"
REASON_PRIVATE = "公开答复脱敏时在第一个 verilog 代码块内有命中"
REASON_RESUME = "续跑时无法确认旧调用已退出"
REASON_KILL = "KILL FAIL：调用结束后仍有存活进程或无法确认"
REASON_ISOLATION = "ISOLATION FAIL：无法建立进程归属，调用未启动"
SYSTEM_NO_TAG = "sent from tier-1 file (no tag)"
REASON_DISK = "DISK FAIL：模型调用前磁盘可用空间不足（规程 16）"
NOTE_OVER = "超限，输出不完整"
NOTE_SUPERVISION = "监督失败，输出不完整"
_SUM_LINE = re.compile(r"^([0-9a-f]{64}) [ *](\S.*)$")


class Refused(Exception):
    """A precondition failed: print the lines, exit 1, nothing called."""

    def __init__(self, lines):
        super().__init__("; ".join(lines) if isinstance(lines, list) else lines)
        self.lines = list(lines) if isinstance(lines, list) else [lines]


class Stopped(Exception):
    """A persistent stop record was written (process ownership or cleanup failure): print the lines, exit 3."""

    def __init__(self, lines):
        super().__init__("; ".join(lines))
        self.lines = list(lines)


class Ctx:
    def __init__(self, repo=None, sandbox=None, claude_cmd=None, no_tags=False, base_env=None, free_bytes=None):
        self.repo = repo or rp.REPO
        self.case = os.path.join(self.repo, "tasks", "CASE-01")
        self.revise = os.path.join(self.case, "revise")
        self.rules = os.path.join(self.revise, "rules")
        self.models_dir = os.path.join(self.revise, "models")
        self.sandbox = sandbox or rp.SANDBOX
        self.sealed = os.path.join(self.sandbox, "sealed")
        self.raw = os.path.join(self.sandbox, "raw")
        self.work = os.path.join(self.sandbox, "work")
        self.claude_cmd = list(claude_cmd) if claude_cmd else [CLI_PATH]
        self.no_tags = no_tags
        self.base_env = dict(os.environ if base_env is None else base_env)
        self.free_bytes = free_bytes
        self._email = None

    def email(self):
        if self._email is None:
            self._email = privacy_check.account_email()
        return self._email


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _dump(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True, default=str) + "\n").encode("utf-8")


def _write(path, data):
    """Atomic replace (records that are updated: attempts.json, call.json, meta, status.md)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def _load_json(path):
    try:
        with open(path, "rb") as f:
            return json.loads(f.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def clean_env(base, tokens=MAX_OUTPUT_TOKENS):
    env = {k: v for k, v in base.items() if not k.upper().startswith(("ANTHROPIC_", "CLAUDE"))}
    env.update({"CLAUDE_CODE_MAX_OUTPUT_TOKENS": tokens, "DISABLE_AUTOUPDATER": "1"})
    return env


def _rel(ctx, path):
    return os.path.relpath(path, ctx.case).replace(os.sep, "/")


# ------------------------------------------------------------------------------------- preconditions
def check_tags(ctx, mode):
    if ctx.no_tags:
        rc, out = prereg.git(["tag", "-l", "revise-prereg*"], ctx.repo)
        if rc != 0 or out.strip():
            raise Refused("PREREG FAIL: --no-tags is for tests only and is refused once a revise-prereg* tag exists")
        return
    probs = prereg.problems(mode, repo=ctx.repo)
    if probs:
        raise Refused(probs + [f"PREREG FAIL: pre-registration ({mode}) does not match; nothing was called"])


def check_reused():
    probs = rp.reused_problems()
    if probs:
        raise Refused([f"PREREG {p}" for p in probs])


def check_disk(ctx, rnd, stop_details=None):
    """Both volumes (protocol 16). A measurement whose process cleanup failed (revpaths.kill_fail_problems) writes a
    REASON_KILL call-side stop of round rnd at once (exit 3), like any other cleanup failure."""
    probs = rp.disk_problems(free_bytes=ctx.free_bytes)
    kill = rp.kill_fail_problems(probs)
    if kill:
        _stop_now(ctx, rnd, REASON_KILL, dict(stop_details or {}, disk_measurement=kill))
    if probs:
        raise Refused(probs + ["DISK FAIL: not started (protocol 16)"])


def _is_smoke_stop(rec):
    return isinstance(rec.get("details"), dict) and "smoke" in rec["details"]


def check_stops(ctx, rnd):
    """Refuse on an open stop of round rnd (either side). Smoke stops live in round SMOKE_STOP_ROUND; every other
    round also refuses while one of them is open (Codex BC1-08)."""
    found = [(rnd, s) for s in stops.open_stops(rnd, revise=ctx.revise)]
    if rnd != SMOKE_STOP_ROUND:
        found += [(SMOKE_STOP_ROUND, s) for s in stops.open_stops(SMOKE_STOP_ROUND, revise=ctx.revise)
                  if _is_smoke_stop(s)]
    if found:
        raise Refused([f"STOPPED: round {r} has open stop {s['stop_id']} (side {s.get('side')}"
                       f"{', smoke ' + str(s['details']['smoke']) if _is_smoke_stop(s) else ''}: "
                       f"{s.get('reason')}; {s.get('why_open')})" for r, s in found]
                      + [f"STOPPED: commit revise/stops/r{r}/<stop_id>.cleared.md for each open stop first"
                         for r in sorted({r for r, _ in found})])


def run_order(ctx):
    doc = _load_json(os.path.join(ctx.rules, "run_order.json"))
    try:
        models = doc["models"]
        assert models and all(isinstance(m, dict) and {"name", "model", "settings"} <= set(m) for m in models)
    except (TypeError, KeyError, AssertionError):
        raise Refused("PREFLIGHT FAIL: revise/rules/run_order.json is missing or malformed") from None
    return models


def load_expect(ctx, mode, models):
    name = "expected_tentative.json" if mode == "smoke" else "expected.json"
    doc = _load_json(os.path.join(ctx.rules, name))
    if not isinstance(doc, dict) or any(not isinstance(doc.get(m["name"]), dict) for m in models):
        raise Refused(f"PREFLIGHT FAIL: revise/rules/{name} is missing or lacks a model entry")
    return doc


def _fresh_workdir(ctx, sub):
    while True:
        d = os.path.join(ctx.work, sub, "rv-" + secrets.token_hex(6))
        try:
            os.makedirs(d)
            return d
        except FileExistsError:
            continue


def parse_originals(data):
    """({settings file name: sha256}, problems) of revise/models/originals.sha256 ("<sha256>  <path>" lines).
    Strict (Codex BC1-10, BC2 2.4): an empty list, a malformed line or a repeated file name is a problem; a model of
    run_order without an entry is reported by originals_problems. Extra entries (files no model uses) are accepted."""
    probs, out = [], {}
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {}, ["PREFLIGHT FAIL: revise/models/originals.sha256 is not UTF-8 text"]
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()                                                   # the final newline
    if not lines:
        return {}, ["PREFLIGHT FAIL: revise/models/originals.sha256 is empty"]
    for i, ln in enumerate(lines, 1):
        m = _SUM_LINE.match(ln)
        if not m:
            probs.append(f"PREFLIGHT FAIL: revise/models/originals.sha256 line {i} is malformed")
            continue
        name = m.group(2).strip().replace("\\", "/").rsplit("/", 1)[-1]
        if name in out:
            probs.append(f"PREFLIGHT FAIL: revise/models/originals.sha256 lists {name} more than once")
            continue
        out[name] = m.group(1)
    return out, probs


def _settings_name(entry):
    return os.path.expandvars(entry["settings"]).replace("\\", "/").rsplit("/", 1)[-1]


def originals_problems(ctx, models):
    """Every model's settings file against revise/models/originals.sha256 (hash only; the content is never read
    here). Every model is checked whatever the state of the list; a model without a usable entry is a problem."""
    try:
        data = rp.read_bytes(os.path.join(ctx.models_dir, "originals.sha256"))
    except OSError:
        data = None
    if data is None:
        originals, probs = {}, ["PREFLIGHT FAIL: revise/models/originals.sha256 is missing (model configuration "
                                "not yet confirmed by the author)"]
    else:
        originals, probs = parse_originals(data)
    for m in models:
        name = _settings_name(m)
        try:
            got = rp.sha256(os.path.expandvars(m["settings"]))
        except OSError:
            got = None
        if name not in originals:
            probs.append(f"PREFLIGHT FAIL: settings file {name} has no entry in revise/models/originals.sha256; "
                         f"it cannot be verified")
        elif got != originals[name]:
            probs.append(f"PREFLIGHT FAIL: settings file {name} differs from revise/models/originals.sha256")
    return probs


def _stop_now(ctx, rnd, reason, details):
    """Write a persistent stop at once and end the run (Codex BC1-08): nothing else is launched."""
    sid = stops.raise_stop(rnd, "call", reason, None, details, revise=ctx.revise)
    line = f"STOP {sid}: {reason} — commit revise/stops/r{rnd}/{sid}.json now"
    print(line, flush=True)
    raise Stopped([line, "STOPPED: nothing else is launched; clear the stop before any further run"])


def preflight(ctx, models, stop_rnd, stop_details=None):
    """Problems of the preflight (no attempt is used). A preflight command whose processes were not cleaned up (or
    whose cleanup cannot be confirmed: REASON_KILL) or that could not be launched under a job (IsolationFail or a
    launch OSError: REASON_ISOLATION) writes a round-stop_rnd stop at once and raises Stopped."""
    probs = []
    try:
        ctx.email()                                   # the redaction needs it; resolve it before any attempt
    except SystemExit:
        probs.append("PREFLIGHT FAIL: git config user.email is empty; the public answers cannot be redacted")
    try:
        want = rp.read_bytes(os.path.join(ctx.rules, "cli.sha256")).decode("ascii").split()[0].lower()
    except (OSError, IndexError, UnicodeDecodeError):
        want = None
        probs.append("PREFLIGHT FAIL: revise/rules/cli.sha256 is missing or malformed")
    if want:
        try:
            if rp.sha256(ctx.claude_cmd[-1]) != want:
                probs.append("PREFLIGHT FAIL: CLI file sha256 differs from revise/rules/cli.sha256")
        except OSError:
            probs.append("PREFLIGHT FAIL: CLI file cannot be read")
    cwd = _fresh_workdir(ctx, "preflight")

    def run(args):
        cmd = " ".join(args)
        try:
            res = limits.run_limited(ctx.claude_cmd + args, "preflight", cwd=cwd, env=clean_env(ctx.base_env))
        except limits.SupervisionError as e:
            if e.killed_pids_alive or e.cleanup_unconfirmed:
                _stop_now(ctx, stop_rnd, REASON_KILL,
                          dict(stop_details or {}, phase="preflight", command=cmd, cause=e.cause_type,
                               alive=e.killed_pids_alive, unconfirmed=e.cleanup_unconfirmed))
            probs.append(f"PREFLIGHT FAIL: {cmd} failed after it had started ({e.cause_type})")
            return None
        except (OSError, limits.IsolationFail) as e:
            # a launch failure may leave a suspended process outside any job: stop as for a model call
            _stop_now(ctx, stop_rnd, REASON_ISOLATION,
                      dict(stop_details or {}, phase="preflight", command=cmd, cause=e.__class__.__name__))
        if res.killed_pids_alive or res.cleanup_unconfirmed:
            _stop_now(ctx, stop_rnd, REASON_KILL,
                      dict(stop_details or {}, phase="preflight", command=cmd, cause=None,
                           alive=res.killed_pids_alive, unconfirmed=res.cleanup_unconfirmed))
        if res.incomplete:
            probs.append(f"PREFLIGHT FAIL: {cmd}: over the preflight limits")
            return None
        if res.rc != 0:
            probs.append(f"PREFLIGHT FAIL: {cmd} exited with {res.rc}")
            return None
        return res.stdout.decode("utf-8", "replace")

    out = run(["--version"])
    if out is not None and (not out.split() or out.split()[0] != CLI_VERSION):
        probs.append(f"PREFLIGHT FAIL: CLI version is not {CLI_VERSION}")
    probs += originals_problems(ctx, models)
    out = run(["auth", "status", "--json"])
    if out is not None:
        try:
            logged = json.loads(out).get("loggedIn") is True
        except (ValueError, AttributeError):
            logged = False
        if not logged:
            probs.append("PREFLIGHT FAIL: auth status is not logged in")
    return probs


def check_preflight(ctx, models, stop_rnd, stop_details=None):
    probs = preflight(ctx, models, stop_rnd, stop_details)
    if probs:
        raise Refused(probs + ["PREFLIGHT FAIL: no model was called and no attempt was used"])


# ------------------------------------------------------------------------------------- text, redaction
def _split_lines(text):
    return re.findall(r"[^\n]*\n|[^\n]+", text)


def _patterns(email):
    return [re.compile(re.escape(email), re.I), privacy_check.USER_DIR, WORKDIR_RE]


def redact(text, email):
    """(redacted text, number of hits)."""
    n = 0
    for pat in _patterns(email):
        text, k = pat.subn(HIDDEN, text)
        n += k
    return text, n


def redact_obj(obj, email):
    if isinstance(obj, str):
        return redact(obj, email)[0]
    if isinstance(obj, list):
        return [redact_obj(v, email) for v in obj]
    if isinstance(obj, dict):
        return {k: redact_obj(v, email) for k, v in obj.items()}
    return obj


def block_hits(text, parsed, email):
    """Redaction hits inside the first verilog block of the raw answer text (to its end when it is unclosed)."""
    if not parsed.lines:
        return 0
    lines = _split_lines(text)
    end = parsed.lines[1] - 1 if len(parsed.lines) > 1 else len(lines)
    body = "".join(lines[parsed.lines[0]:end])
    return sum(len(p.findall(body)) for p in _patterns(email))


def answer_of(stdout):
    return classify.answer_text(classify.parse_stream(stdout.decode("utf-8", errors="replace")))


def memory_clean(stdout):
    events = classify.parse_stream(stdout.decode("utf-8", errors="replace"))
    init = next((e for e in events if isinstance(e, dict) and e.get("type") == "system"
                 and e.get("subtype") == "init"), None)
    mem = ((init or {}).get("memory_paths") or {}).get("auto") if isinstance(init, dict) else None
    if not mem:
        return None
    return not os.path.isdir(mem) or not os.listdir(mem)


# ------------------------------------------------------------------------------------- one call
def read_call_inputs(ctx, rnd, code):
    """(system bytes, stdin bytes, prompt_ok) of a formal call: both must equal their HEAD versions."""
    sys_path = os.path.join(ctx.revise, "prompts", "system.md")
    prompt_path = os.path.join(ctx.revise, "prompts", f"r{rnd}", f"{code}_prompt.md")
    system, stdin = rp.read_bytes(sys_path), rp.read_bytes(prompt_path)
    ok = prereg.blob_at("HEAD", sys_path) == system and prereg.blob_at("HEAD", prompt_path) == stdin
    return system, stdin, ok


def one_call(ctx, entry, system, stdin, prompt_ok, raw_dir, n, expect, tokens, work_sub):
    """Run one model call; returns (verdict, meta, stdout bytes, launch problem or None, kill problem bool).
    meta["interrupted"] is True when supervision failed after the CLI had started (limits.SupervisionError)."""
    os.makedirs(raw_dir, exist_ok=True)
    workdir = _fresh_workdir(ctx, work_sub)
    settings = os.path.expandvars(entry["settings"])
    argv = ctx.claude_cmd + ["-p", "--model", entry["model"], "--tools", "", "--system-prompt",
                             system.decode("utf-8"), "--settings", settings] + CLI_FLAGS
    base = os.path.join(raw_dir, f"call{n}")
    meta_path = base + ".meta.json"
    meta = {"n": n, "model": entry["model"], "name": entry["name"], "settings": entry["settings"],
            "argv": ctx.claude_cmd + ["-p", "--model", entry["model"], "--tools", "", "--system-prompt",
                                      f"<sha256 {rp.sha256_bytes(system)}>", "--settings", entry["settings"]]
            + CLI_FLAGS, "workdir": workdir, "max_output_tokens_env": tokens,
            "system_sha": rp.sha256_bytes(system), "stdin_sha": rp.sha256_bytes(stdin), "prompt_ok": prompt_ok,
            "start": _now(), "completed": False}
    _write(meta_path, _dump(meta))
    launch, kill, interrupted = None, False, False
    try:
        res = limits.run_limited(argv, "model", cwd=workdir, env=clean_env(ctx.base_env, tokens), stdin_bytes=stdin,
                                 stdout_path=base + ".jsonl", stderr_path=base + ".err",
                                 proc_path=base + ".proc.json")
        rc, timed_out = res.rc, res.timed_out
        over = bool(res.stdout_over or res.stderr_over)               # an output limit, not a failed write
        limit_hit = bool(timed_out or over)
        kill = bool(res.killed_pids_alive or res.cleanup_unconfirmed)
        if res.output_error:
            # writing stdout/stderr failed and run_limited stopped the run: a record problem, not an over-limit;
            # classify gets it as an interrupted call (record incomplete), meta keeps the write error
            interrupted = True
            meta.update(interrupted=True, output_error=str(res.output_error))
        meta.update(kill={"alive": res.killed_pids_alive, "unconfirmed": res.cleanup_unconfirmed},
                    captured={"stdout": res.stdout_bytes, "stderr": res.stderr_bytes},
                    incomplete=NOTE_OVER if limit_hit else (NOTE_SUPERVISION if res.output_error else None))
    except limits.SupervisionError as e:
        # the CLI had started: not a launch problem; the call counts as interrupted, the cleanup result decides KILL
        rc, timed_out, over, interrupted = None, e.timed_out, bool(e.stdout_over or e.stderr_over), True
        kill = bool(e.killed_pids_alive or e.cleanup_unconfirmed)
        meta.update(supervision_error=f"{e.cause_type}: {e.__cause__}", interrupted=True,
                    kill={"alive": e.killed_pids_alive, "unconfirmed": e.cleanup_unconfirmed},
                    captured={"stdout": e.stdout_bytes, "stderr": e.stderr_bytes},
                    incomplete=NOTE_OVER if (e.timed_out or over) else NOTE_SUPERVISION)
    except (OSError, limits.IsolationFail) as e:
        rc, timed_out, over = None, False, False
        launch = f"{e.__class__.__name__}: {e}"
        meta["launch_error"] = launch
    stdout = rp.read_bytes(base + ".jsonl") if os.path.isfile(base + ".jsonl") else b""
    stderr = rp.read_bytes(base + ".err") if os.path.isfile(base + ".err") else b""
    mem = memory_clean(stdout)
    verdict = classify.classify(stdout, expect, rc, timed_out, over, interrupted, prompt_ok, mem)
    meta.update(end=_now(), exit=rc, timed_out=timed_out, over_limit=over, memory_dir_clean=mem, completed=True,
                stdout_sha=rp.sha256_bytes(stdout), stderr_sha=rp.sha256_bytes(stderr),
                flags=verdict.flags, delivery=verdict.delivery, retry_allowed=verdict.retry_allowed,
                global_stop=verdict.global_stop, api_retries=verdict.api_retries)
    _write(meta_path, _dump(meta))
    return verdict, meta, stdout, launch, kill


# ------------------------------------------------------------------------------------- round records
def out_dir(ctx, rnd):
    return os.path.join(ctx.revise, "outputs", f"r{rnd}")


def attempts_path(ctx, rnd):
    return os.path.join(out_dir(ctx, rnd), "attempts.json")


def new_attempts(rnd, codes):
    return {"round": rnd, "codes": {c: {"state": "pending", "consumed": 0, "final": None, "calls": []}
                                    for c in codes}}


def save_attempts(ctx, rnd, att):
    _write(attempts_path(ctx, rnd), _dump(att))


def attempts_problems(att, codes):
    probs = []
    if not isinstance(att, dict) or not isinstance(att.get("codes"), dict):
        return ["ATTEMPTS FAIL: attempts.json is unreadable"]
    if set(att["codes"]) != set(codes):
        probs.append("ATTEMPTS FAIL: attempts.json does not list exactly the codes of the mapping")
    allowed = {"pending": (0,), "running1": (1,), "await_retry": (1,), "running2": (2,), "final": (1, 2)}
    for code, e in sorted(att["codes"].items()):
        st, used = e.get("state"), e.get("consumed")
        if isinstance(used, bool) or not isinstance(used, int) or used > 2 or used < 0:
            probs.append(f"ATTEMPTS FAIL: {code}: consumed {used!r} is not 0, 1 or 2")
        elif st not in allowed or used not in allowed[st]:
            probs.append(f"ATTEMPTS FAIL: {code}: state {st!r} with consumed {used} is inconsistent")
        elif (st == "final") != (e.get("final") in FINALS):
            probs.append(f"ATTEMPTS FAIL: {code}: final {e.get('final')!r} does not fit state {st!r}")
    return probs


def write_call_json(ctx, rnd, code, e):
    doc = {"code": code, "rnd": rnd, "final": e["final"], "calls": e["calls"]}
    _write(os.path.join(out_dir(ctx, rnd), f"{code}.call.json"), _dump(doc))


def write_status(ctx, rnd, att):
    lines = [f"# 第 {rnd} 轮调用核查表（按编号；异常只列类别）", "",
             "| 编号 | 状态 | 已开始的调用 | 最终决定 | 各次调用的异常类别 |", "|---|---|---|---|---|"]
    for code, e in sorted(att["codes"].items()):
        cats = "；".join(f"第 {c['n']} 次：{'、'.join(c['categories']) or '无'}" for c in e["calls"]) or "—"
        lines.append(f"| {code} | {e['state']} | {e['consumed']} | {e['final'] or '—'} | {cats} |")
    _write(os.path.join(out_dir(ctx, rnd), "status.md"), ("\n".join(lines) + "\n").encode("utf-8"))


def _append_extracted(ctx, rnd, code, rows):
    path = os.path.join(ctx.revise, "predictions", f"r{rnd}_extracted.jsonl")
    old = []
    if os.path.isfile(path):
        old = [json.loads(ln) for ln in rp.read_bytes(path).decode("utf-8").splitlines() if ln.strip()]
    mine = [r for r in old if r.get("code") == code]
    if mine:
        if mine != rows:
            raise rp.RevpathsError(f"{path} already holds different rows of {code}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "ab") as f:
        for r in rows:
            f.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))


def write_answers(ctx, rnd, code, stdout, raw_dir, meta, parse):
    """answer_raw.md, the public answer and (parse) parsed.json, candidate, extracted rows. Returns the number of
    redaction hits inside the first verilog block (parse only)."""
    text = answer_of(stdout)
    raw_bytes = text.encode("utf-8")                                  # no newline conversion
    rp.write_new_or_same(os.path.join(raw_dir, "answer_raw.md"), raw_bytes)
    public, hits = redact(text.replace("\r\n", "\n").replace("\r", "\n"), ctx.email())
    public_bytes = public.encode("utf-8")
    rp.write_new_or_same(os.path.join(out_dir(ctx, rnd), f"{code}.md"), public_bytes)
    meta.update(answer_sha_raw=rp.sha256_bytes(raw_bytes), public_sha=rp.sha256_bytes(public_bytes),
                public_redaction_hits=hits)
    if not parse:
        return 0
    parsed = extract.parse_answer(text, rnd)
    cand = None
    if parsed.status == "ok":
        cf = extract.write_candidate(code, parsed, dest_root=ctx.case)
        cand = {"rtl_path": _rel(ctx, cf.rtl_path), "cfg_path": _rel(ctx, cf.cfg_path), "rtl_sha_raw": cf.rtl_sha_raw,
                "rtl_sha_lf": cf.rtl_sha_lf, "cfg_sha": cf.cfg_sha}
    in_block = block_hits(text, parsed, ctx.email())
    fields = dataclasses.asdict(parsed)
    del fields["rtl"]                                                 # RTL only as its hashes
    doc = redact_obj(fields, ctx.email())
    doc.update(code=code, rnd=rnd, candidate=cand,
               hashes={"answer_sha_raw": meta["answer_sha_raw"], "public_sha": meta["public_sha"],
                       "stdin_sha": meta["stdin_sha"], "system_sha": meta["system_sha"],
                       "stdout_sha": meta.get("stdout_sha"), "stderr_sha": meta.get("stderr_sha")})
    rp.write_new_or_same(os.path.join(out_dir(ctx, rnd), f"{code}.parsed.json"), _dump(doc))
    _append_extracted(ctx, rnd, code, redact_obj(extract.extracted_rows(code, parsed), ctx.email()))
    meta.update(parsed_status=parsed.status, rtl_redaction_hits=in_block)
    return in_block


def apply_verdict(ctx, rnd, code, e, n, verdict, stdout, raw_dir, meta, interrupted=False, extra_stop=None):
    """Decide the state after call n, write the records; returns [(reason, details)] of stops to raise."""
    cats = list(dict.fromkeys(c for c, _ in verdict.flags))
    e["calls"].append({"n": n, "categories": cats, "delivery": verdict.delivery,
                       "retry_allowed": verdict.retry_allowed, "global_stop": verdict.global_stop,
                       "interrupted": interrupted})
    private = 0
    if verdict.delivery == "delivery_fail":
        e["state"], e["final"] = "final", "delivery_fail"
        write_answers(ctx, rnd, code, stdout, raw_dir, meta, parse=False)
    elif verdict.delivery == "retry":
        if n == 1:
            e["state"], e["final"] = "await_retry", None
        else:
            e["state"], e["final"] = "final", "unavailable"
    else:
        e["state"], e["final"] = "final", "parse"
        private = write_answers(ctx, rnd, code, stdout, raw_dir, meta, parse=True)
    _write(os.path.join(raw_dir, f"call{n}.meta.json"), _dump(meta))
    write_call_json(ctx, rnd, code, e)
    out = []
    if verdict.global_stop:
        out.append((REASON_PROMPT, {"call": n, "categories": cats}))
    if extra_stop:
        out.append((extra_stop, {"call": n, "categories": cats}))
    if private:
        out.append((REASON_PRIVATE, {"call": n, "hits_in_block": private}))
    return out


def _raise(ctx, rnd, code, stops_to_raise):
    exit_code = EXIT_OK
    for reason, details in stops_to_raise:
        sid = stops.raise_stop(rnd, "call", reason, code, details, revise=ctx.revise)
        print(f"STOP {sid}: {reason} — commit revise/stops/r{rnd}/{sid}.json now", flush=True)
        exit_code = max(exit_code, EXIT_PRIVATE if reason == REASON_PRIVATE else EXIT_STOP)
    return exit_code


def call_code(ctx, rnd, code, e, entry, expect, att):
    """One call of `code` (state pending or await_retry). Returns the list of stops to raise; the caller raises them
    and only then saves the decided state (a crash in between leaves running<n>, never a decided state without its
    stop record; recovery may then raise a duplicate stop, the conservative failure)."""
    n = e["consumed"] + 1
    disk = rp.disk_problems(free_bytes=ctx.free_bytes)               # before every call, before consumed moves
    if disk:
        for p in disk:
            print(p, flush=True)
        kill = rp.kill_fail_problems(disk)
        if kill:
            return [(REASON_KILL, {"before_call": n, "disk_measurement": kill})]
        return [(REASON_DISK, {"before_call": n, "problems": disk})]
    e["consumed"], e["state"] = n, f"running{n}"
    save_attempts(ctx, rnd, att)                                      # before the call; never decreased
    print(f"CALL started (call {n} of at most 2 for this code)", flush=True)
    system, stdin, ok = read_call_inputs(ctx, rnd, code)
    raw_dir = os.path.join(ctx.raw, f"r{rnd}", code)
    verdict, meta, stdout, launch, kill = one_call(ctx, entry, system, stdin, ok, raw_dir, n, expect,
                                                   MAX_OUTPUT_TOKENS, f"r{rnd}")
    extra = REASON_ISOLATION if launch else REASON_KILL if kill else None
    return apply_verdict(ctx, rnd, code, e, n, verdict, stdout, raw_dir, meta,
                         interrupted=bool(meta.get("interrupted")), extra_stop=extra)


def recover(ctx, rnd, code, e, expect, att):
    """A code found in running1/running2 on --resume (the shell stopped mid-call). Returns stops to raise."""
    n = e["consumed"]
    raw_dir = os.path.join(ctx.raw, f"r{rnd}", code)
    base = os.path.join(raw_dir, f"call{n}")
    proc = _load_json(base + ".proc.json")
    if not isinstance(proc, dict) or ("root_pid" not in proc and proc.get("phase") not in
                                      ("launching", "not_started")):
        # no record (the shell may have stopped before run_limited wrote it, or between Popen and the record): an
        # old CLI process cannot be ruled out
        return [(REASON_RESUME, {"call": n, "why": "no usable lifecycle record"})], False
    try:
        alive, unconfirmed = limits.still_alive(proc)
    except Exception:                                                 # noqa: BLE001 - any failure = unconfirmed
        alive, unconfirmed = [], True
    if unconfirmed:
        return [(REASON_RESUME, {"call": n, "why": "process state cannot be confirmed"})], False
    if alive:
        res = limits.cleanup(proc, "model")
        if res.killed_pids_alive or res.cleanup_unconfirmed:
            return [(REASON_RESUME, {"call": n, "why": "old processes still alive or unconfirmed after cleanup"})], \
                False
        print(f"RESUME: old call processes cleaned up ({len(alive)})", flush=True)
    extra = None
    if proc.get("phase") == "not_started":
        extra = REASON_ISOLATION                                      # the launch failed, as if seen live
    elif limits.record_cleanup_failed(proc):
        extra = REASON_KILL                                           # the old run's own cleanup failed
    meta = _load_json(base + ".meta.json") or {"n": n, "prompt_ok": True}
    stdout = rp.read_bytes(base + ".jsonl") if os.path.isfile(base + ".jsonl") else b""
    if meta.get("completed"):
        # the call ended and was classified, the shell stopped before the decision was saved: same decision and
        # same stops as on the live path
        interrupted = bool(meta.get("interrupted"))
        verdict = classify.classify(stdout, expect, meta.get("exit"), meta.get("timed_out", False),
                                    meta.get("over_limit", False), interrupted, meta.get("prompt_ok", True),
                                    meta.get("memory_dir_clean"))
        kill = meta.get("kill") or {}
        if meta.get("launch_error"):
            extra = REASON_ISOLATION
        elif extra is None and (kill.get("alive") or kill.get("unconfirmed")):
            extra = REASON_KILL
    else:
        verdict = classify.classify(stdout, expect, None, bool(proc.get("timed_out")), False, True,
                                    meta.get("prompt_ok", True), memory_clean(stdout))
        interrupted = True
        meta.update(recovered=_now(), completed=True, interrupted=True, exit=None,
                    stdout_sha=rp.sha256_bytes(stdout), flags=verdict.flags, delivery=verdict.delivery)
    if interrupted and verdict.delivery == "parse":                  # cannot happen (interrupted is a flag)
        raise AssertionError("an interrupted call was classified as parse")
    return apply_verdict(ctx, rnd, code, e, n, verdict, stdout, raw_dir, meta, interrupted=interrupted,
                         extra_stop=extra), True


# ------------------------------------------------------------------------------------- modes
def _round_setup(ctx, rnd):
    check_stops(ctx, rnd)
    check_tags(ctx, "formal")
    check_reused()
    check_disk(ctx, rnd)
    try:
        m = mapping.load(rnd, revise=ctx.revise, sealed=ctx.sealed)
    except mapping.MappingError as err:
        raise Refused(str(err)) from None
    models = run_order(ctx)
    try:
        order = [(entry, mapping.code_of(m, entry["name"])) for entry in models]
    except mapping.MappingError as err:
        raise Refused(f"MAPPING FAIL: {err}") from None
    if sorted(c for _, c in order) != sorted(x["code"] for x in m["entries"]):
        raise Refused("MAPPING FAIL: the mapping does not cover exactly the models of run_order.json")
    return models, order


def _check_prompts(ctx, rnd, codes):
    probs = []
    paths = [os.path.join(ctx.revise, "prompts", "system.md")]
    paths += [os.path.join(ctx.revise, "prompts", f"r{rnd}", f"{c}_prompt.md") for c in codes]
    for p in paths:
        if not prereg.committed_unchanged(p):
            probs.append(f"PROMPT FAIL: {_rel(ctx, p)} is missing, untracked or differs from HEAD")
    if probs:
        raise Refused(probs)


def run_round(ctx, rnd, resume):
    with stops.round_lock(rnd, "call", revise=ctx.revise):
        models, order = _round_setup(ctx, rnd)
        codes = [c for _, c in order]
        exists = os.path.exists(attempts_path(ctx, rnd))
        if not resume and exists:
            raise Refused(f"REFUSED: round {rnd} has already started (attempts.json exists); use --resume {rnd}")
        if resume and not exists:
            raise Refused(f"REFUSED: round {rnd} has not started; nothing to resume (use --round {rnd})")
        att = _load_json(attempts_path(ctx, rnd)) if resume else new_attempts(rnd, codes)
        probs = attempts_problems(att, codes)
        if probs:
            raise Refused(probs + ["ATTEMPTS FAIL: nothing was called"])
        expect = load_expect(ctx, "formal", models)
        todo = [c for c in codes if att["codes"][c]["state"] != "final"]
        _check_prompts(ctx, rnd, todo)
        check_preflight(ctx, models, rnd)
        if not resume:
            save_attempts(ctx, rnd, att)
        exit_code = EXIT_OK
        try:
            for entry, code in order:                                 # running* first (resume)
                e = att["codes"][code]
                if e["state"] in ("running1", "running2"):
                    raised, decided = recover(ctx, rnd, code, e, expect[entry["name"]], att)
                    rc = _raise(ctx, rnd, code, raised) if raised else EXIT_OK
                    if decided:
                        save_attempts(ctx, rnd, att)
                    if raised:
                        return rc
            for entry, code in order:
                e = att["codes"][code]
                while e["state"] in ("pending", "await_retry"):
                    raised = call_code(ctx, rnd, code, e, entry, expect[entry["name"]], att)
                    rc = _raise(ctx, rnd, code, raised) if raised else EXIT_OK
                    save_attempts(ctx, rnd, att)
                    if raised:
                        return rc
        finally:
            write_status(ctx, rnd, att)
            for code, e in sorted(att["codes"].items()):
                print(f"{code}: state={e['state']} consumed={e['consumed']} final={e['final']}", flush=True)
        print(f"ROUND {rnd}: every code is final" if all(e["state"] == "final" for e in att["codes"].values())
              else f"ROUND {rnd}: not finished", flush=True)
        return exit_code


def commit_codes(ctx, rnd, dry_run):
    with stops.round_lock(rnd, "call", revise=ctx.revise):
        check_stops(ctx, rnd)
        check_tags(ctx, "formal")
        check_reused()
        models = run_order(ctx)
        codes_path = os.path.join(out_dir(ctx, rnd), "codes.txt")
        sha_path = os.path.join(ctx.revise, "outputs", f"mapping_r{rnd}.sha256")
        if os.path.exists(codes_path) or os.path.exists(sha_path):
            raise Refused(f"REFUSED: round {rnd} codes already exist ({_rel(ctx, codes_path)}); codes are committed "
                          f"once per round")
        prev = None
        if rnd == 2:
            done = os.path.join(out_dir(ctx, 1), "round_complete.json")
            if not prereg.committed_unchanged(done):
                raise Refused("REFUSED: round 2 codes need revise/outputs/r1/round_complete.json committed")
            try:
                m1 = mapping.load(1, revise=ctx.revise, sealed=ctx.sealed)
                prev = {e["name"]: mapping.code_of(m1, e["name"]) for e in models}
            except mapping.MappingError as err:
                raise Refused(str(err)) from None
        names = [e["name"] for e in models]
        if dry_run:
            print(f"DRY RUN：将为 {len(names)} 个模型生成第 {rnd} 轮编号；不写任何文件。正式运行后请提交这两个文件："
                  f"{_rel(ctx, codes_path)}、{_rel(ctx, sha_path)}", flush=True)
            return EXIT_OK
        try:
            mapping.commit_codes(rnd, names, prev, revise=ctx.revise, sealed=ctx.sealed)
        except mapping.MappingError as err:
            raise Refused(str(err)) from None
        print(f"CODES r{rnd} written. 请提交这两个文件：{_rel(ctx, codes_path)}、{_rel(ctx, sha_path)}", flush=True)
        return EXIT_OK


def smoke_expected(ctx, kind, entry, sys_path):
    """(expected system bytes or None, how the system prompt was checked, expected stdin bytes) of a smoke call
    (Codex BC1-11). stdin is rebuilt from the frozen sources with build_prompt.py's smoke builders: probe =
    cap_probe_user.md, canary = smoke_user.md, rehearsal = the rehearsal prompt built from round1_template.md, the
    package and the model's stage A answer. The system prompt (smoke_system.md; rehearsal: system.md) has no builder:
    its expected bytes are the bytes in tag revise-prereg-smoke; with --no-tags (tests only) there is no independent
    source, so no system check is claimed (expected None, SYSTEM_NO_TAG)."""
    templates = os.path.join(ctx.revise, "prompts")
    if ctx.no_tags:
        want_sys, how = None, SYSTEM_NO_TAG
    else:
        tag = prereg.TAGS["smoke"]
        want_sys = prereg.blob_at(f"refs/tags/{tag}", sys_path)
        if want_sys is None:
            raise Refused(f"SMOKE PROMPT FAIL: {_rel(ctx, sys_path)} is not in tag {tag}; nothing was called")
        how = f"tag {tag}"
    if kind == "rehearsal":
        stdin = build_prompt.rehearsal_bytes(entry["name"], package=os.path.join(ctx.revise, "package"),
                                             templates=templates)
    elif kind == "canary":
        stdin = build_prompt.canary_bytes(templates)[1]
    else:
        stdin = build_prompt.cap_probe_bytes(templates)
    return want_sys, how, stdin


def smoke_canaries(ctx):
    """The two canary words, taken from smoke_system.md and smoke_user.md (one '暗号是：<word>。' each)."""
    words = []
    for data in build_prompt.canary_bytes(os.path.join(ctx.revise, "prompts")):
        found = CANARY_RE.findall(data.decode("utf-8"))
        if len(found) != 1:
            raise Refused("SMOKE PROMPT FAIL: smoke_system.md and smoke_user.md must each hold exactly one canary "
                          "word ('暗号是：<word>。')")
        words.append(found[0])
    return words


def run_smoke(ctx, kind):
    """Smoke calls (protocol 6.3). An ordinary failure of one model's call stays with that model; a process
    ownership or cleanup failure (ISOLATION FAIL, KILL FAIL, a supervision failure whose cleanup failed) writes a
    persistent stop at once (round SMOKE_STOP_ROUND, side call, details["smoke"] = kind, no model name) and nothing
    else is launched; that stop blocks later smoke runs and every formal run (check_stops). Refused once round
    SMOKE_STOP_ROUND is complete (outputs/r1/round_complete.json exists)."""
    done = os.path.join(out_dir(ctx, SMOKE_STOP_ROUND), "round_complete.json")
    if os.path.exists(done):
        raise Refused(f"REFUSED: smoke runs write their stops into round {SMOKE_STOP_ROUND}, which is closed "
                      f"({_rel(ctx, done)} exists); no smoke run after round {SMOKE_STOP_ROUND} is complete")
    check_stops(ctx, SMOKE_STOP_ROUND)
    check_tags(ctx, "smoke")
    check_reused()
    check_disk(ctx, SMOKE_STOP_ROUND, {"smoke": kind})
    models = run_order(ctx)
    expect = load_expect(ctx, "smoke", models)
    prompts = os.path.join(ctx.case, "runs", "revise-smoke", "prompts")
    sys_name = "system.md" if kind == "rehearsal" else "smoke_system.md"
    sys_path = os.path.join(ctx.revise, "prompts", sys_name)
    user_of = {"probe": lambda m: "cap_probe_user.md", "canary": lambda m: "canary_user.md",
               "rehearsal": lambda m: f"rehearsal_{m['name']}.md"}[kind]
    missing = [p for p in [sys_path] + [os.path.join(prompts, user_of(m)) for m in models] if not os.path.isfile(p)]
    if missing:
        raise Refused([f"SMOKE FAIL: prompt file {_rel(ctx, p)} is missing (build_prompt.py)" for p in missing])
    canaries = smoke_canaries(ctx) if kind == "canary" else None
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2) + "-" + kind
    raw_base = os.path.join(ctx.raw, "smoke", stamp)
    rec_dir = os.path.join(ctx.case, "runs", "revise-smoke", stamp)
    # the bytes actually sent, checked against the bytes rebuilt from the sources, before any launch
    inputs, checks, bad = [], [], []
    for m in models:
        system, stdin = rp.read_bytes(sys_path), rp.read_bytes(os.path.join(prompts, user_of(m)))
        try:
            want_sys, how, want_stdin = smoke_expected(ctx, kind, m, sys_path)
        except (build_prompt.PromptError, OSError, rp.RevpathsError) as err:
            raise Refused(f"SMOKE PROMPT FAIL: the expected prompt bytes cannot be rebuilt: {err}") from None
        sys_ok = None if want_sys is None else system == want_sys      # None: not independently checked
        stdin_ok = stdin == want_stdin
        chk = {"name": m["name"], "system_sha": rp.sha256_bytes(system), "expected_system_sha":
               None if want_sys is None else rp.sha256_bytes(want_sys), "system_check": how,
               "stdin_sha": rp.sha256_bytes(stdin), "expected_stdin_sha": rp.sha256_bytes(want_stdin),
               "system_ok": sys_ok, "stdin_ok": stdin_ok, "prompt_ok": sys_ok is not False and stdin_ok}
        inputs.append((system, stdin))
        checks.append(chk)
        if not chk["prompt_ok"]:
            bad.append(chk)
    if bad:
        _write(os.path.join(rec_dir, "summary.json"), _dump({"kind": kind, "time": _now(), "refused": True,
                                                             "rows": checks}))
        raise Refused([f"SMOKE PROMPT FAIL: {c['name']}: "
                       + "; ".join(f"{what} sha256 {c[what + '_sha']} != expected {c['expected_' + what + '_sha']}"
                                   for what in ("system", "stdin") if c[what + "_ok"] is False) for c in bad]
                      + [f"SMOKE PROMPT FAIL: nothing was called -> {_rel(ctx, rec_dir)}"])
    check_preflight(ctx, models, SMOKE_STOP_ROUND, {"smoke": kind, "stamp": stamp})
    tokens = CAP_PROBE_TOKENS if kind == "probe" else MAX_OUTPUT_TOKENS
    summary, all_ok, exit_code = [], True, None
    for i, (m, (system, stdin), chk) in enumerate(zip(models, inputs, checks)):
        disk = rp.disk_problems(free_bytes=ctx.free_bytes)           # before every call (Codex BC1-09)
        if disk:
            for p in disk:
                print(p, flush=True)
            summary.append(dict(chk, ok=False, disk=disk))
            kill = rp.kill_fail_problems(disk)
            if kill:                                                  # the measurement's own cleanup failed
                all_ok = False
                exit_code = _raise(ctx, SMOKE_STOP_ROUND, None, [(REASON_KILL, {
                    "smoke": kind, "stamp": stamp, "run_order_index": i, "disk_measurement": kill})])
                print("STOPPED: nothing else is launched; clear the stop before any further run", flush=True)
                break
            print(f"DISK FAIL: smoke stopped before {m['name']}; no further call", flush=True)
            all_ok, exit_code = False, EXIT_REFUSED
            break
        raw_dir = os.path.join(raw_base, m["name"])
        verdict, meta, stdout, launch, kill = one_call(ctx, m, system, stdin, chk["prompt_ok"], raw_dir, 1,
                                                       expect[m["name"]], tokens, "smoke")
        cats = list(dict.fromkeys(c for c, _ in verdict.flags))
        text = answer_of(stdout)
        row = dict(chk, categories=cats, delivery=verdict.delivery, stdout_sha=meta["stdout_sha"],
                   launch_error=bool(launch), kill_fail=kill)
        if launch or kill:
            # process ownership / cleanup failure: persistent stop now, nothing else launched (Codex BC1-08)
            row["ok"] = False
            summary.append(row)
            all_ok = False
            _write(os.path.join(rec_dir, "summary.json"), _dump({"kind": kind, "time": _now(), "rows": summary}))
            exit_code = _raise(ctx, SMOKE_STOP_ROUND, None,
                               [(REASON_ISOLATION if launch else REASON_KILL,
                                 {"smoke": kind, "stamp": stamp, "run_order_index": i,
                                  "interrupted": bool(meta.get("interrupted"))})])
            print("STOPPED: nothing else is launched; clear the stop before any further run", flush=True)
            break
        if kind == "probe":
            ok = classify.F_LIMIT in cats
        elif kind == "canary":
            row["canaries"] = [c in text for c in canaries]
            ok = verdict.delivery == "parse" and all(row["canaries"])
        else:
            ok = verdict.delivery == "parse"
            if ok:
                parsed = extract.parse_answer(text, 1)
                row["parsed_status"], row["reason"] = parsed.status, parsed.reason
                ok = parsed.status == "ok"
                if ok:
                    cf = extract.write_candidate(m["name"], parsed, dest_root=os.path.join(rec_dir, "candidates"))
                    same = rp.read_bytes(cf.rtl_path) == parsed.rtl and rp.sha256(cf.rtl_path) == parsed.rtl_sha_lf
                    row.update(rtl_sha_raw=cf.rtl_sha_raw, rtl_sha_lf=cf.rtl_sha_lf, cfg_sha=cf.cfg_sha,
                               candidate_equals_block=same)
                    ok = same
        row["ok"] = ok
        all_ok &= ok
        summary.append(row)
        print(f"{m['name']}: {kind} ok={ok} delivery={verdict.delivery} categories={'、'.join(cats) or '无'}",
              flush=True)
    _write(os.path.join(rec_dir, "summary.json"), _dump({"kind": kind, "time": _now(), "rows": summary}))
    print(f"SMOKE {kind} {'OK' if all_ok else 'FAIL'} -> {_rel(ctx, rec_dir)}", flush=True)
    if exit_code is not None:
        return exit_code
    return EXIT_OK if all_ok else EXIT_REFUSED


def _round_arg(text):
    return int(text) if text in ("1", "2") else None


def main(argv=None, free_bytes=None, base_env=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="run_revise.py")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--smoke", choices=SMOKE_KINDS)
    g.add_argument("--commit-codes", metavar="R")
    g.add_argument("--round", metavar="R")
    g.add_argument("--resume", metavar="R")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--claude-cmd", help="tests only: JSON list replacing the pinned claude executable")
    ap.add_argument("--sandbox-root", help="tests only: replaces D:\\study\\revise_sandbox")
    ap.add_argument("--repo-root", help="tests only: a temporary repository")
    ap.add_argument("--no-tags", action="store_true", help="tests only: refused once a revise-prereg* tag exists")
    args = ap.parse_args(argv)
    if (args.repo_root or args.no_tags) and not (args.sandbox_root and args.claude_cmd):
        print("usage: --repo-root and --no-tags are for tests only and need --sandbox-root and --claude-cmd", flush=True)
        return EXIT_USAGE
    r_text = args.commit_codes or args.round or args.resume
    rnd = _round_arg(r_text) if r_text is not None else None
    if r_text is not None and rnd is None:
        print(f"usage: the round must be 1 or 2, not {r_text!r}", flush=True)
        return EXIT_USAGE
    if args.dry_run and args.commit_codes is None:
        print("usage: --dry-run goes with --commit-codes", flush=True)
        return EXIT_USAGE
    try:
        claude_cmd = json.loads(args.claude_cmd) if args.claude_cmd else None
    except ValueError:
        print("usage: --claude-cmd must be a JSON list", flush=True)
        return EXIT_USAGE
    ctx = Ctx(repo=args.repo_root, sandbox=args.sandbox_root, claude_cmd=claude_cmd, no_tags=args.no_tags,
              base_env=base_env, free_bytes=free_bytes)
    try:
        if args.smoke:
            return run_smoke(ctx, args.smoke)
        if args.commit_codes is not None:
            return commit_codes(ctx, rnd, args.dry_run)
        return run_round(ctx, rnd, resume=args.resume is not None)
    except Refused as e:
        for line in e.lines:
            print(line, flush=True)
        return EXIT_REFUSED
    except Stopped as e:                                              # the STOP line was printed when written
        for line in e.lines[1:]:
            print(line, flush=True)
        return EXIT_STOP
    except stops.LockError as e:
        print(str(e), flush=True)
        return EXIT_REFUSED
    except (stops.StopsError, prereg.PreregError, rp.RevpathsError) as e:
        print(f"REFUSED: {e}", flush=True)
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
