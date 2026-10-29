"""Run one round of model diagnoses through the thin Claude Code shell (protocol v0.3 sections 6.1, 6.3). Copied and
adapted from tasks/CASE-01/diag/scripts/run_round.py (rules/copied_from.tsv, rules/diff/run_round.py.diff).

Run from Git Bash in the repository root (Windows Python: claude.exe is a Windows program). A round can take up to
3 x 30 minutes, so the operator always starts it in the background with its output in a log file:
  python -B tasks/CASE-02/scripts/run_round.py --probe          # Task 6 budget probe (before tier 1; not blinded)
  python -B tasks/CASE-02/scripts/run_round.py --smoke          # protocol step 8 (not blinded)
  python -B tasks/CASE-02/scripts/run_round.py --init-mapping   # code mapping + commitment, before round 1
  python -B tasks/CASE-02/scripts/run_round.py --round 1        # all three models, one call
  python -B tasks/CASE-02/scripts/run_round.py --round 1 --resume
  python -B tasks/CASE-02/scripts/run_round.py --round 1 --rerun B
  python -B tasks/CASE-02/scripts/run_round.py --round 2

CASE-02 changes against stage A: paths under tasks/CASE-02; tags case02-prereg / case02-prereg-round; sealed
directory <sandbox>/sealed-case02; every model call runs under run_limited_win (wall clock, stdout and stderr size
limits from rules/contract.json shell_limits, polled every second, two-stage termination; proc.json per attempt);
the prompt bytes pass label_check before any call (internal version labels in operator-generated parts refuse the
run); --probe sends the three fixed budget-probe prompts to every model and keeps only the usage fields.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c2paths  # noqa: E402
import label_check as lc  # noqa: E402
from c2paths import write_new_or_same  # noqa: E402

sys.path.insert(0, os.path.join(c2paths.CASE01_DIAG, "scripts"))
import void_check as vc  # noqa: E402  (read-only reuse)
from privacy_check import USER_DIR, account_email  # noqa: E402  (read-only reuse)

CODES = ("A", "B", "C")
HIDDEN = "<已隐去>"
SMOKE_CANARIES = ("青松-0427", "白鹭-1010")
CAP_PROBE_TOKENS = 64
CAP_HIT = "output token maximum"
CLI_PATH = r"D:\study\diag_sandbox\bin\claude-2.1.296.exe"
CLI_VERSION = "2.1.296"
RUN_DIR = re.compile(r"run-[0-9a-f]{8}")
TAGS = {"smoke": "case02-prereg", "round": "case02-prereg-round"}
DEFAULT_LIMITS = {"process_seconds": 1800, "stdout_bytes": 52428800, "stderr_bytes": 1048576, "poll_seconds": 1,
                  "soft_kill_wait_seconds": 30, "hard_kill_wait_seconds": 30}
PROBES = ("blank", "prose", "report")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def clean_env(base):
    env = {k: v for k, v in base.items() if not k.upper().startswith(("ANTHROPIC_", "CLAUDE"))}
    env.update({"CLAUDE_CODE_MAX_OUTPUT_TOKENS": "32000", "DISABLE_AUTOUPDATER": "1"})
    return env


def redact(text, email):
    count = (len(re.findall(re.escape(email), text, re.I)) + len(USER_DIR.findall(text)) + len(RUN_DIR.findall(text)))
    text = re.sub(re.escape(email), HIDDEN, text, flags=re.I)
    return RUN_DIR.sub(HIDDEN, USER_DIR.sub(HIDDEN, text)), count


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)


def prereg_paths(list_path, mode):
    tiers = {"smoke": [], "round": []}
    with open(list_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("round "):
                tiers["round"].append(line[len("round "):].strip())
            else:
                tiers["smoke"].append(line)
    if mode == "smoke":
        tiers["round"] = []
    return tiers


def tracked_problems(repo, paths, tag=None):
    problems = []
    if tag and git(repo, "rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode != 0:
        return [f"tag {tag} does not exist"]
    for p in paths:
        if git(repo, "ls-files", "--error-unmatch", "--", p).returncode != 0:
            problems.append(f"not tracked: {p}")
        elif git(repo, "diff", "--quiet", "HEAD", "--", p).returncode != 0:
            problems.append(f"differs from HEAD: {p}")
        elif git(repo, "ls-files", "--others", "--exclude-standard", "--", p).stdout.strip():
            problems.append(f"untracked files under: {p}")
        elif tag and git(repo, "diff", "--quiet", tag, "HEAD", "--", p).returncode != 0:
            problems.append(f"changed since tag {tag}: {p}")
    return problems


def prereg_problems(repo, list_path, mode="round", use_tags=True):
    problems = []
    for tier, paths in prereg_paths(list_path, mode).items():
        if paths:
            problems += tracked_problems(repo, paths, TAGS[tier] if use_tags else None)
    return problems


def shell_limits(case):
    path = os.path.join(case, "rules", "contract.json")
    limits = dict(DEFAULT_LIMITS)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            sl = json.load(f).get("shell_limits") or {}
        limits.update({k: v for k, v in sl.items() if k in DEFAULT_LIMITS})
    return limits


def _descendants(pid):
    """All descendant pids of `pid` (Windows: Win32_Process via PowerShell; POSIX: pgrep -P), for the tree check."""
    found, todo = [], [pid]
    while todo:
        p = todo.pop()
        try:
            if os.name == "nt":
                out = subprocess.run(["powershell", "-NoProfile", "-Command",
                                      f"Get-CimInstance Win32_Process -Filter 'ParentProcessId={p}' | Select-Object -ExpandProperty ProcessId"],
                                     capture_output=True, text=True, timeout=30).stdout
            else:
                out = subprocess.run(["pgrep", "-P", str(p)], capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        for tok in out.split():
            if tok.isdigit() and int(tok) not in found:
                found.append(int(tok))
                todo.append(int(tok))
    return found


def _alive(pid):
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True, timeout=30).stdout
            return str(pid) in out.split()
        os.kill(pid, 0)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _kill(proc, hard, pids=()):
    try:
        if hard:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, timeout=30)
                for p in pids:
                    subprocess.run(["taskkill", "/F", "/PID", str(p)], capture_output=True, timeout=30)
            else:
                proc.kill()
                for p in pids:
                    try:
                        os.kill(p, 9)
                    except OSError:
                        pass
        else:
            proc.terminate()
    except (OSError, subprocess.SubprocessError):
        pass


def run_limited_win(argv, stdin_bytes, stdout_path, stderr_path, limits, cwd, env):
    """Run a model call with a wall-clock limit and stdout / stderr size limits, polled every poll_seconds; on a
    limit: soft termination, wait, then hard kill of the whole tree, wait (R5 M6, R6 M12). The size limits are
    checked once more after a normal exit (a burst shorter than one poll interval). Returns (exit_code, record):
    exit_code is the process's code, or "timeout" / "output_limit" when a limit was hit."""
    with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err)
        feeder = threading.Thread(target=_feed, args=(proc, stdin_bytes), daemon=True)
        feeder.start()
        start = time.monotonic()
        hit, stage, waits, kids = None, None, {}, []
        while True:
            try:
                proc.wait(timeout=limits["poll_seconds"])
                break
            except subprocess.TimeoutExpired:
                pass
            elapsed = time.monotonic() - start
            so, se = os.path.getsize(stdout_path), os.path.getsize(stderr_path)
            if elapsed >= limits["process_seconds"]:
                hit = "process_seconds"
            elif so > limits["stdout_bytes"]:
                hit = "stdout_bytes"
            elif se > limits["stderr_bytes"]:
                hit = "stderr_bytes"
            if hit:
                kids = _descendants(proc.pid)
                t0 = time.monotonic()
                _kill(proc, hard=False)
                stage = "soft"
                try:
                    proc.wait(timeout=limits["soft_kill_wait_seconds"])
                except subprocess.TimeoutExpired:
                    pass
                waits["soft_wait_seconds"] = round(time.monotonic() - t0, 3)
                if proc.poll() is None or any(_alive(k) for k in kids):
                    t1 = time.monotonic()
                    _kill(proc, hard=True, pids=kids)
                    stage = "hard"
                    try:
                        proc.wait(timeout=limits["hard_kill_wait_seconds"])
                    except subprocess.TimeoutExpired:
                        raise RuntimeError(f"pid {proc.pid} survived the kill; stop it by hand")
                    waits["hard_wait_seconds"] = round(time.monotonic() - t1, 3)
                break
        elapsed = time.monotonic() - start
    so, se = os.path.getsize(stdout_path), os.path.getsize(stderr_path)
    if hit is None:                                   # post-exit check (R6 M12)
        if so > limits["stdout_bytes"]:
            hit = "stdout_bytes"
        elif se > limits["stderr_bytes"]:
            hit = "stderr_bytes"
    deadline = time.monotonic() + 2
    while kids and any(_alive(k) for k in kids) and time.monotonic() < deadline:
        time.sleep(0.2)
    tree_clean = not any(_alive(k) for k in kids)
    record = {"limit_hit": hit, "terminated": stage is not None, "kill_stage": stage, "returncode": proc.returncode,
              "elapsed_seconds": round(elapsed, 3), "stdout_bytes": so, "stderr_bytes": se, "limits": dict(limits),
              "waits": waits, "descendants_seen": kids, "tree_clean": tree_clean}
    if hit == "process_seconds":
        return "timeout", record
    if hit:
        return "output_limit", record
    return proc.returncode, record


def _feed(proc, data):
    try:
        proc.stdin.write(data)
        proc.stdin.close()
    except (OSError, ValueError):
        pass


class RoundRunner:
    def __init__(self, repo, case, sandbox_root, claude_cmd, base_env=None, limits=None):
        self.repo, self.case, self.sandbox_root = repo, case, sandbox_root
        self.sealed = os.path.join(sandbox_root, "sealed-case02")
        self.claude_cmd = claude_cmd
        self.env = clean_env(dict(os.environ if base_env is None else base_env))
        self.email = account_email()
        self.limits = dict(shell_limits(case), **(limits or {}))
        self.models, self.expect = [], {}
        p = os.path.join(case, "rules", "run_order.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                self.models = json.load(f)["models"]
            with open(os.path.join(case, "rules", "expected.json"), encoding="utf-8") as f:
                self.expect = json.load(f)

    # ---- preflight (no attempt is used) ------------------------------------------------------------------------
    def preflight(self):
        problems = []
        cli_file = self.claude_cmd[-1]
        with open(os.path.join(self.case, "rules", "cli.sha256"), encoding="utf-8") as f:
            want = f.read().split()[0]
        with open(cli_file, "rb") as f:
            if sha256(f.read()) != want:
                problems.append("CLI file sha256 differs from rules/cli.sha256")
        run = lambda *a: subprocess.run(self.claude_cmd + list(a), env=self.env, capture_output=True, timeout=120)
        version = run("--version").stdout.decode("utf-8", "replace").split()
        if not version or version[0] != CLI_VERSION:
            problems.append(f"CLI version is not {CLI_VERSION}")
        with open(os.path.join(self.case, "models", "originals.sha256"), encoding="utf-8") as f:
            originals = {line.split()[1].replace("\\", "/").rsplit("/", 1)[-1]: line.split()[0] for line in f if line.strip()}
        for m in self.models:
            path = os.path.expandvars(m["settings"])
            name = path.replace("\\", "/").rsplit("/", 1)[-1]
            try:
                with open(path, "rb") as f:
                    ok = sha256(f.read()) == originals.get(name)
            except OSError:
                ok = False
            if not ok:
                problems.append(f"settings file of {m['name']} differs from models/originals.sha256")
        try:
            logged_in = json.loads(run("auth", "status", "--json").stdout.decode("utf-8")).get("loggedIn") is True
        except ValueError:
            logged_in = False
        if not logged_in:
            problems.append("auth status is not logged in")
        return problems

    # ---- one attempt -------------------------------------------------------------------------------------------
    def make_workdirs(self, n):
        dirs = []
        while len(dirs) < n:
            d = os.path.join(self.sandbox_root, "run-" + secrets.token_hex(4))
            os.makedirs(d)
            dirs.append(d)
        for i in range(len(dirs) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            dirs[i], dirs[j] = dirs[j], dirs[i]
        return dirs

    def attempt(self, entry, system_bytes, user_bytes, prompt_ok, sealed_dir, label, workdir, env=None):
        argv = self.claude_cmd + ["-p", "--model", entry["model"], "--tools", "", "--system-prompt",
                                  system_bytes.decode("utf-8"), "--settings", os.path.expandvars(entry["settings"]),
                                  "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
                                  "--output-format", "stream-json", "--verbose"]
        out_path, err_path = (os.path.join(sealed_dir, f"{label}.{x}") for x in ("jsonl", "err"))
        start = datetime.datetime.now().isoformat(timespec="seconds")
        exit_code, proc = run_limited_win(argv, user_bytes, out_path, err_path, self.limits, workdir, env or self.env)
        end = datetime.datetime.now().isoformat(timespec="seconds")
        with open(os.path.join(sealed_dir, f"{label}.proc.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(proc, f, ensure_ascii=False, indent=1)
        with open(out_path, encoding="utf-8", errors="replace") as f:
            events = vc.parse_stream(f.read())
        init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
        mem = (init.get("memory_paths") or {}).get("auto")
        memory_clean = None if not mem else (not os.path.isdir(mem) or not os.listdir(mem))
        problems = vc.check_run(events, self.expect[entry["name"]], exit_code, prompt_ok, memory_clean)
        answer, hidden = redact(vc.answer_text(events), self.email)
        result = next((e for e in events if e.get("type") == "result"), {})
        usage = (result.get("modelUsage") or {}).get(self.expect[entry["name"]]["init_model"], {})
        meta = {"label": label, "model": entry["name"], "start": start, "end": end, "exit": exit_code, "workdir": workdir,
                "argv": argv[:len(self.claude_cmd)] + ["-p", "--model", entry["model"], "--tools", "", "--system-prompt",
                        f"<system prompt sha256={sha256(system_bytes)}>", "--settings", entry["settings"],
                        "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
                        "--output-format", "stream-json", "--verbose"],
                "system_sha256": sha256(system_bytes), "user_sha256": sha256(user_bytes), "prompt_ok": prompt_ok,
                "valid": not problems, "problems": problems, "categories": vc.categories(problems),
                "per_turn_effort_active": init.get("per_turn_effort_active"),
                "max_output_tokens": usage.get("maxOutputTokens"), "hidden_in_answer": hidden,
                "api_retries": sum(e.get("subtype") == "api_retry" for e in events),
                "num_turns": result.get("num_turns"), "is_error": result.get("is_error"),
                "usage": result.get("usage"), "model_usage": usage, "proc": {k: proc[k] for k in ("limit_hit", "elapsed_seconds")}}
        with open(os.path.join(sealed_dir, f"{label}.meta.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        with open(os.path.join(sealed_dir, f"{label}.answer.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(answer)
        return meta

    # ---- sealed bookkeeping ------------------------------------------------------------------------------------
    def mapping_path(self):
        return os.path.join(self.sealed, "mapping.json")

    def commitment_path(self):
        return os.path.join(self.case, "outputs", "mapping.sha256")

    def init_mapping(self):
        if os.path.exists(self.mapping_path()):
            raise SystemExit("ROUND FAIL: a code mapping already exists")
        names = [m["name"] for m in self.models]
        for i in range(len(names) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            names[i], names[j] = names[j], names[i]
        data = (json.dumps({"salt": secrets.token_hex(32), "codes": dict(zip(CODES, names))}, indent=1) + "\n")
        os.makedirs(self.sealed, exist_ok=True)
        with open(self.mapping_path(), "x", encoding="utf-8", newline="\n") as f:
            f.write(data)
        commitment = sha256(data.encode("utf-8"))
        write_new_or_same(self.commitment_path(), f"{commitment}  sealed-case02/mapping.json\n".encode())
        return commitment

    def load_mapping(self):
        if not os.path.exists(self.mapping_path()) or not os.path.exists(self.commitment_path()):
            raise SystemExit("ROUND FAIL: run --init-mapping and commit outputs/mapping.sha256 first")
        with open(self.mapping_path(), "rb") as f:
            raw = f.read()
        with open(self.commitment_path(), encoding="utf-8") as f:
            if sha256(raw) != f.read().split()[0]:
                raise SystemExit("ROUND FAIL: the sealed mapping does not match outputs/mapping.sha256")
        return json.loads(raw)["codes"]

    def attempts_path(self, rnd):
        return os.path.join(self.sealed, f"round{rnd}", "attempts.json")

    def load_attempts(self, rnd):
        p = self.attempts_path(rnd)
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as f:
            return json.load(f)

    def save_attempts(self, rnd, attempts):
        os.makedirs(os.path.dirname(self.attempts_path(rnd)), exist_ok=True)
        tmp = self.attempts_path(rnd) + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(attempts, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.attempts_path(rnd))

    # ---- repository side (code-named only) ---------------------------------------------------------------------
    def write_status(self, rnd, attempts):
        lines = [f"# 第 {rnd} 轮运行状态（只按代号；作废原因只列类别）", ""]
        for code in CODES:
            mine = [a for a in attempts if a["code"] == code]
            if not mine:
                continue
            last = mine[-1]
            if last["valid"]:
                lines.append(f"- {code}：通过（第 {len(mine)} 次尝试）")
            else:
                note = "，可补跑 1 次" if len(mine) == 1 else "，已用完补跑，记为未完成"
                lines.append(f"- {code}：作废（原因类别：{'、'.join(last['categories'])}）{note}")
        out = os.path.join(self.case, "outputs", f"round{rnd}")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "status.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        return lines[2:]

    def finish(self, rnd, attempts):
        for code in CODES:
            mine = [a for a in attempts if a["code"] == code]
            if mine and mine[-1]["valid"]:
                with open(os.path.join(self.sealed, f"round{rnd}", f"{mine[-1]['label']}.answer.md"), encoding="utf-8") as f:
                    answer = f.read()
                write_new_or_same(os.path.join(self.case, "outputs", f"round{rnd}", f"{code}.md"),
                                  (answer.rstrip("\n") + "\n").encode("utf-8"))
        return self.write_status(rnd, attempts)

    # ---- rounds --------------------------------------------------------------------------------------------------
    def prompts(self, rnd, code):
        with open(os.path.join(self.case, "prompts", "system.md"), "rb") as f:
            system = f.read()
        if rnd == 1:
            path = os.path.join(self.case, "prompts", "round1_user.md")
            expected = self.round1_bytes()
        else:
            path = os.path.join(self.case, "prompts", "round2", f"{code}.md")
            expected = self.round2_bytes(code)
        with open(path, "rb") as f:
            user = f.read()
        return system, user, user == expected, path

    def round1_bytes(self):
        import build_prompt
        return build_prompt.round1_bytes()

    def round2_bytes(self, code):
        import build_prompt
        return build_prompt.round2_bytes(code)

    def runnable(self, rnd):
        if rnd == 1:
            return set(CODES)
        runnable = {c for c in CODES if os.path.exists(os.path.join(self.case, "outputs", "round1", f"{c}.md"))}
        rel = os.path.relpath(self.case, self.repo).replace(os.sep, "/")
        needed = [f"{rel}/{d}" for d in ("round2", "prompts/round2", "outputs/round1")]
        needed += [f"{rel}/{d}" for c in sorted(runnable)
                   for d in (f"prompts/round2/{c}.md", f"round2/{c}_results.md", f"outputs/round1/{c}.md")]
        needed.append(f"{rel}/round2/translation.tsv")
        if os.path.isdir(os.path.join(self.case, "queries", "round2")):
            needed += [f"{rel}/queries/round2", f"{rel}/queries/round2/SHA256SUMS"]
        problems = tracked_problems(self.repo, needed)
        if problems:
            raise SystemExit("ROUND FAIL: round-2 inputs not committed: " + "; ".join(problems))
        return runnable

    def run_attempts(self, rnd, attempts, todo):
        sealed_dir = os.path.join(self.sealed, f"round{rnd}")
        # label check of the exact system and user bytes BEFORE anything is recorded or called (protocol 6.2; R6 M13)
        reports = []
        for entry, code, n in todo:
            system, user, _, path = self.prompts(rnd, code)
            rel = os.path.relpath(path, self.case)
            if not lc.is_model_visible(rel):
                raise SystemExit(f"ROUND FAIL: {rel} is not in rules/model_visible.txt")
            reports.append(lc.scan_report(user.decode("utf-8", "replace"), rel))
            reports.append(lc.scan_report(system.decode("utf-8", "replace"), "prompts/system.md"))
        found = [f for r in reports for f in r["findings"]]
        os.makedirs(sealed_dir, exist_ok=True)
        with open(os.path.join(sealed_dir, "label_check.json"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": datetime.datetime.now().isoformat(timespec="seconds"), "reports": reports},
                               ensure_ascii=False) + "\n")
        if found:
            raise SystemExit("ROUND FAIL: internal label in an operator-generated part of the prompt: " + "; ".join(found))
        for (entry, code, n), workdir in zip(todo, self.make_workdirs(len(todo))):
            system, user, ok, _ = self.prompts(rnd, code)
            record = {"code": code, "model": entry["name"], "attempt": n, "label": f"{entry['name']}-{n}",
                      "state": "started", "valid": None, "categories": []}
            attempts.append(record)
            self.save_attempts(rnd, attempts)
            meta = self.attempt(entry, system, user, ok, sealed_dir, record["label"], workdir)
            record.update(state="done", valid=meta["valid"], categories=meta["categories"])
            self.save_attempts(rnd, attempts)

    def run_round(self, rnd):
        if self.load_attempts(rnd):
            raise SystemExit(f"ROUND FAIL: round {rnd} has already started; use --resume or --rerun <code>")
        codes = {v: k for k, v in self.load_mapping().items()}
        runnable = self.runnable(rnd)
        attempts = []
        self.run_attempts(rnd, attempts, [(e, codes[e["name"]], 1) for e in self.models if codes[e["name"]] in runnable])
        return self.finish(rnd, attempts)

    def resume(self, rnd):
        attempts = self.load_attempts(rnd)
        if not attempts:
            raise SystemExit(f"ROUND FAIL: round {rnd} has not started; nothing to resume")
        codes = {v: k for k, v in self.load_mapping().items()}
        for a in attempts:
            if a["state"] == "started":
                a.update(state="done", valid=False, categories=[vc.CAT_INTERRUPTED])
        self.save_attempts(rnd, attempts)
        started = {a["code"] for a in attempts}
        runnable = self.runnable(rnd)
        self.run_attempts(rnd, attempts, [(e, codes[e["name"]], 1) for e in self.models
                                          if codes[e["name"]] in runnable and codes[e["name"]] not in started])
        return self.finish(rnd, attempts)

    def rerun(self, rnd, code):
        attempts = self.load_attempts(rnd)
        if any(a["state"] != "done" for a in attempts):
            raise SystemExit("ROUND FAIL: an attempt was interrupted; run --resume first")
        mine = [a for a in attempts if a["code"] == code]
        if len(mine) != 1 or mine[0]["valid"]:
            raise SystemExit(f"ROUND FAIL: {code} cannot be rerun (only once, and only after a void attempt)")
        self.load_mapping()
        self.runnable(rnd)
        entry = next(m for m in self.models if m["name"] == mine[0]["model"])
        self.run_attempts(rnd, attempts, [(entry, code, 2)])
        return self.finish(rnd, attempts)

    def smoke(self):
        sealed_dir = os.path.join(self.sandbox_root, "smoke-case02-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.makedirs(sealed_dir)
        with open(os.path.join(self.case, "prompts", "smoke_system.md"), "rb") as f:
            system = f.read()
        with open(os.path.join(self.case, "prompts", "smoke_user.md"), "rb") as f:
            user = f.read()
        all_ok = True
        for entry, workdir in zip(self.models, self.make_workdirs(len(self.models))):
            meta = self.attempt(entry, system, user, True, sealed_dir, entry["name"], workdir)
            with open(os.path.join(sealed_dir, f"{entry['name']}.answer.md"), encoding="utf-8") as f:
                answer = f.read()
            canaries = all(c in answer for c in SMOKE_CANARIES)
            all_ok &= meta["valid"] and canaries
            print(f"{entry['name']}: valid={meta['valid']} canaries={canaries} per_turn_effort_active={meta['per_turn_effort_active']} "
                  f"maxOutputTokens={meta['max_output_tokens']} exit={meta['exit']} retries={meta['api_retries']}")
            for cat, detail in meta["problems"]:
                print(f"  {cat}: {detail}")
        with open(os.path.join(self.case, "prompts", "cap_probe_user.md"), "rb") as f:
            probe = f.read()
        capped_env = dict(self.env, CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(CAP_PROBE_TOKENS))
        for entry, workdir in zip(self.models, self.make_workdirs(len(self.models))):
            label = f"{entry['name']}-cap{CAP_PROBE_TOKENS}"
            meta = self.attempt(entry, system, probe, True, sealed_dir, label, workdir, env=capped_env)
            with open(os.path.join(sealed_dir, f"{label}.answer.md"), encoding="utf-8") as f:
                answer = f.read()
            capped = (meta["num_turns"] or 0) > 1 or CAP_HIT in answer
            all_ok &= capped
            print(f"{entry['name']}: cap_probe capped={capped} turns={meta['num_turns']} is_error={meta['is_error']} exit={meta['exit']}")
        print(f"SMOKE {'OK' if all_ok else 'FAIL'} -> {sealed_dir}")
        return 0 if all_ok else 1

    def probe(self):
        """Budget probe (impl_plan Task 6; author decision 2026-10-28): the three fixed prompts to every model, once
        each; only the usage fields are kept (the answer text is removed)."""
        probe_dir = os.path.join(self.sandbox_root, "smoke-case02-budget-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.makedirs(probe_dir)
        with open(os.path.join(self.case, "prompts", "system.md"), "rb") as f:
            system = f.read()
        usage, ok = {}, True
        for entry, workdir in zip(self.models, self.make_workdirs(len(self.models))):
            usage[entry["name"]] = {}
            for name in PROBES:
                with open(os.path.join(self.case, "prompts", f"budget_probe_{name}.md"), "rb") as f:
                    user = f.read()
                label = f"{entry['name']}-probe-{name}"
                meta = self.attempt(entry, system, user, True, probe_dir, label, workdir)
                u = meta.get("usage") or {}
                mu = meta.get("model_usage") or {}
                rec = {"prompt_bytes": len(user), "system_bytes": len(system), "exit": meta["exit"],
                       "input_tokens": u.get("input_tokens"), "cache_creation_input_tokens": u.get("cache_creation_input_tokens"),
                       "cache_read_input_tokens": u.get("cache_read_input_tokens"), "output_tokens": u.get("output_tokens"),
                       "model_usage_inputTokens": mu.get("inputTokens"), "model_usage_cacheCreation": mu.get("cacheCreationInputTokens"),
                       "model_usage_cacheRead": mu.get("cacheReadInputTokens")}
                usage[entry["name"]][name] = rec
                ok &= rec["input_tokens"] is not None
                try:
                    os.remove(os.path.join(probe_dir, f"{label}.answer.md"))
                except OSError:
                    pass
                print(f"{entry['name']} {name}: bytes={len(user)} input_tokens={rec['input_tokens']} cache_create={rec['cache_creation_input_tokens']} "
                      f"cache_read={rec['cache_read_input_tokens']} exit={meta['exit']}")
        with open(os.path.join(probe_dir, "usage.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(usage, f, ensure_ascii=False, indent=1)
        print(f"PROBE {'OK' if ok else 'INCOMPLETE'} -> {probe_dir}")
        return 0 if ok else 1


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--round", type=int, choices=(1, 2))
    g.add_argument("--smoke", action="store_true")
    g.add_argument("--probe", action="store_true")
    g.add_argument("--init-mapping", action="store_true")
    h = ap.add_mutually_exclusive_group()
    h.add_argument("--rerun", choices=CODES)
    h.add_argument("--resume", action="store_true")
    ap.add_argument("--repo-root")
    ap.add_argument("--case-dir")
    ap.add_argument("--sandbox-root", default=r"D:\study\diag_sandbox")
    ap.add_argument("--claude-cmd", help="tests only: JSON list replacing the pinned claude executable")
    ap.add_argument("--no-tags", action="store_true", help="tests only: skip the pre-registration tag check")
    args = ap.parse_args(argv)
    if (args.rerun or args.resume) and not args.round:
        ap.error("--rerun and --resume need --round")
    repo, case = args.repo_root or c2paths.REPO, args.case_dir or c2paths.CASE
    claude_cmd = json.loads(args.claude_cmd) if args.claude_cmd else [CLI_PATH]
    mode = "round" if args.round else "smoke"
    if args.no_tags and any(git(repo, "rev-parse", "-q", "--verify", f"refs/tags/{t}").returncode == 0 for t in TAGS.values()):
        print("ROUND FAIL: --no-tags is for tests only and is refused once a pre-registration tag exists")
        return 1
    if not args.probe:                       # the budget probe is a calibration before tier 1: no registration check
        problems = prereg_problems(repo, os.path.join(case, "rules", "preregistered.txt"), mode, not args.no_tags)
        if problems:
            for p in problems:
                print(f"PREREG {p}")
            print("ROUND FAIL: pre-registered files are not all committed and unchanged")
            return 1
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    runner = RoundRunner(repo, case, args.sandbox_root, claude_cmd)
    if args.init_mapping:
        print(f"MAPPING OK: commitment {runner.init_mapping()} -> outputs/mapping.sha256 (commit it before round 1)")
        return 0
    problems = runner.preflight()
    if problems:
        for p in problems:
            print(f"PREFLIGHT {p}")
        print("ROUND FAIL: preflight failed; no model was called and no attempt was used")
        return 1
    os.makedirs(runner.sealed, exist_ok=True)
    what = "probe" if args.probe else "smoke" if args.smoke else f"round {args.round}" + (f" rerun {args.rerun}" if args.rerun else "") + (
        " resume" if args.resume else "")
    what += " no-tags" if args.no_tags else ""
    with open(os.path.join(runner.sealed, "heads.log"), "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} HEAD={head} {what}\n")
    if args.probe:
        return runner.probe()
    if args.smoke:
        return runner.smoke()
    if args.rerun:
        lines = runner.rerun(args.round, args.rerun)
    elif args.resume:
        lines = runner.resume(args.round)
    else:
        lines = runner.run_round(args.round)
    for line in lines:
        print(line)
    print(f"ROUND {args.round} DONE (HEAD {head[:7]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
