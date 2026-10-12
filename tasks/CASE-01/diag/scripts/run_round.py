"""Run one round of model diagnoses through the thin Claude Code shell (protocol v0.5 sections 5 and 6).

Run from Git Bash in the repository root (Windows Python: claude.exe is a Windows program). A round can take up to
3 x 30 minutes, so the operator always starts it in the background with its output in a log file:
  python -B tasks/CASE-01/diag/scripts/run_round.py --smoke          # protocol step 4 (not blinded)
  python -B tasks/CASE-01/diag/scripts/run_round.py --init-mapping   # code mapping + commitment, before round 1
  python -B tasks/CASE-01/diag/scripts/run_round.py --round 1        # all three models, one call
  python -B tasks/CASE-01/diag/scripts/run_round.py --round 1 --resume      # after an interruption
  python -B tasks/CASE-01/diag/scripts/run_round.py --round 1 --rerun B
  python -B tasks/CASE-01/diag/scripts/run_round.py --round 2

What it guarantees:
  * refuses to run unless every path in diag/rules/preregistered.txt is tracked, equal to HEAD and equal to the
    pre-registration tag of its tier (diag-prereg; diag-prereg-round for lines starting with "round ");
  * preflight before any model call, which costs no attempt: the pinned CLI file has the pre-registered sha256
    (rules/cli.sha256), reports version 2.1.296, every settings file has the sha256 in models/originals.sha256, and
    `auth status` says logged in;
  * every run: inherited ANTHROPIC_*/CLAUDE* variables removed, CLAUDE_CODE_MAX_OUTPUT_TOKENS=32000 and
    DISABLE_AUTOUPDATER=1 set, tools off, own system prompt, prompt bytes on stdin, fresh empty working directory
    (all directories of a round are created together and handed out in random order);
  * everything that identifies a model (command line, stream-json, times, working directories, void details, the
    code mapping with a 256-bit random salt) goes to the sealed directory outside the repository; the repository
    only gets answers named by code, a status file with generic void categories, and the sha256 commitment of the
    mapping file, written by --init-mapping and committed before round 1;
  * every attempt is recorded in the sealed attempts file before the model is called and again when it ends, so an
    interrupted round is finished with --resume: the interrupted attempt counts as a void attempt (运行中断), models
    that never started are run, nothing sealed has to be opened by hand;
  * void is decided by void_check.py from machine fields before anyone reads an answer; at most one rerun per code,
    and only after a void attempt;
  * the account e-mail, Windows user-directory paths and working-directory names in an answer are replaced by
    "<已隐去>" (count sealed); round 2 embeds this redacted answer.
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import void_check as vc  # noqa: E402
from diagpaths import write_new_or_same  # noqa: E402
from privacy_check import USER_DIR, account_email  # noqa: E402

CODES = ("A", "B", "C")
TIMEOUT_S = 1800
HIDDEN = "<已隐去>"
SMOKE_CANARIES = ("青松-0427", "白鹭-1010")
CLI_PATH = r"D:\study\diag_sandbox\bin\claude-2.1.296.exe"
CLI_VERSION = "2.1.296"
RUN_DIR = re.compile(r"run-[0-9a-f]{8}")
TAGS = {"smoke": "diag-prereg", "round": "diag-prereg-round"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def clean_env(base):
    env = {k: v for k, v in base.items() if not k.upper().startswith(("ANTHROPIC_", "CLAUDE"))}
    env.update({"CLAUDE_CODE_MAX_OUTPUT_TOKENS": "32000", "DISABLE_AUTOUPDATER": "1"})
    return env


def redact(text, email):
    count = (len(re.findall(re.escape(email), text, re.I)) + len(USER_DIR.findall(text))
             + len(RUN_DIR.findall(text)))
    text = re.sub(re.escape(email), HIDDEN, text, flags=re.I)
    return RUN_DIR.sub(HIDDEN, USER_DIR.sub(HIDDEN, text)), count


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)


def prereg_paths(list_path, mode):
    """{tier: [paths]} for mode 'smoke' (smoke tier only) or 'round' (both tiers). Lines starting with 'round ' are
    the round tier: produced in protocol step 5 (base checks, mapping commitment), after the smoke retest."""
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
    """A path (file or directory) must be tracked, equal to HEAD, have no untracked files under it, and, when a tag
    is given, be unchanged between that tag and HEAD."""
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


class RoundRunner:
    def __init__(self, repo, diag, sandbox_root, claude_cmd, base_env=None):
        self.repo, self.diag, self.sandbox_root = repo, diag, sandbox_root
        self.sealed = os.path.join(sandbox_root, "sealed")
        self.claude_cmd = claude_cmd
        self.env = clean_env(dict(os.environ if base_env is None else base_env))
        self.email = account_email()
        with open(os.path.join(diag, "rules", "run_order.json"), encoding="utf-8") as f:
            self.models = json.load(f)["models"]
        with open(os.path.join(diag, "rules", "expected.json"), encoding="utf-8") as f:
            self.expect = json.load(f)

    # ---- preflight (no attempt is used) ------------------------------------------------------------------------
    def preflight(self):
        problems = []
        cli_file = self.claude_cmd[-1]
        with open(os.path.join(self.diag, "rules", "cli.sha256"), encoding="utf-8") as f:
            want = f.read().split()[0]
        with open(cli_file, "rb") as f:
            if sha256(f.read()) != want:
                problems.append("CLI file sha256 differs from rules/cli.sha256")
        run = lambda *a: subprocess.run(self.claude_cmd + list(a), env=self.env, capture_output=True, timeout=120)
        version = run("--version").stdout.decode("utf-8", "replace").split()
        if not version or version[0] != CLI_VERSION:
            problems.append(f"CLI version is not {CLI_VERSION}")
        with open(os.path.join(self.diag, "models", "originals.sha256"), encoding="utf-8") as f:
            originals = {line.split()[1].replace("\\", "/").rsplit("/", 1)[-1]: line.split()[0]
                         for line in f if line.strip()}
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
        """n fresh empty working directories, created together and returned in random order."""
        dirs = []
        while len(dirs) < n:
            d = os.path.join(self.sandbox_root, "run-" + secrets.token_hex(4))
            os.makedirs(d)
            dirs.append(d)
        for i in range(len(dirs) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            dirs[i], dirs[j] = dirs[j], dirs[i]
        return dirs

    def attempt(self, entry, system_bytes, user_bytes, prompt_ok, sealed_dir, label, workdir):
        argv = self.claude_cmd + ["-p", "--model", entry["model"], "--tools", "", "--system-prompt",
                                  system_bytes.decode("utf-8"), "--settings", os.path.expandvars(entry["settings"]),
                                  "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
                                  "--output-format", "stream-json", "--verbose"]
        out_path, err_path = (os.path.join(sealed_dir, f"{label}.{x}") for x in ("jsonl", "err"))
        start = datetime.datetime.now().isoformat(timespec="seconds")
        with open(out_path, "wb") as out, open(err_path, "wb") as err:
            proc = subprocess.Popen(argv, cwd=workdir, env=self.env, stdin=subprocess.PIPE, stdout=out, stderr=err)
            try:
                proc.communicate(input=user_bytes, timeout=TIMEOUT_S)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                else:
                    proc.kill()
                proc.wait()
                exit_code = "timeout"
        end = datetime.datetime.now().isoformat(timespec="seconds")
        with open(out_path, encoding="utf-8", errors="replace") as f:
            events = vc.parse_stream(f.read())
        init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
        mem = (init.get("memory_paths") or {}).get("auto")
        memory_clean = None if not mem else (not os.path.isdir(mem) or not os.listdir(mem))
        problems = vc.check_run(events, self.expect[entry["name"]], exit_code, prompt_ok, memory_clean)
        answer, hidden = redact(vc.answer_text(events), self.email)
        result = next((e for e in events if e.get("type") == "result"), {})
        usage = (result.get("modelUsage") or {}).get(self.expect[entry["name"]]["init_model"], {})
        meta = {"label": label, "model": entry["name"], "start": start, "end": end, "exit": exit_code,
                "workdir": workdir,
                "argv": argv[:len(self.claude_cmd)] + ["-p", "--model", entry["model"], "--tools", "", "--system-prompt",
                        f"<system prompt sha256={sha256(system_bytes)}>", "--settings", entry["settings"],
                        "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
                        "--output-format", "stream-json", "--verbose"],
                "system_sha256": sha256(system_bytes), "user_sha256": sha256(user_bytes), "prompt_ok": prompt_ok,
                "valid": not problems, "problems": problems, "categories": vc.categories(problems),
                "per_turn_effort_active": init.get("per_turn_effort_active"),
                "max_output_tokens": usage.get("maxOutputTokens"), "hidden_in_answer": hidden,
                "api_retries": sum(e.get("subtype") == "api_retry" for e in events)}
        with open(os.path.join(sealed_dir, f"{label}.meta.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        with open(os.path.join(sealed_dir, f"{label}.answer.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(answer)
        return meta

    # ---- sealed bookkeeping ------------------------------------------------------------------------------------
    def mapping_path(self):
        return os.path.join(self.sealed, "mapping.json")

    def commitment_path(self):
        return os.path.join(self.diag, "outputs", "mapping.sha256")

    def init_mapping(self):
        if os.path.exists(self.mapping_path()):
            raise SystemExit("ROUND FAIL: a code mapping already exists")
        names = [m["name"] for m in self.models]
        for i in range(len(names) - 1, 0, -1):                     # Fisher-Yates with the system random source
            j = secrets.randbelow(i + 1)
            names[i], names[j] = names[j], names[i]
        data = (json.dumps({"salt": secrets.token_hex(32), "codes": dict(zip(CODES, names))}, indent=1) + "\n")
        os.makedirs(self.sealed, exist_ok=True)
        with open(self.mapping_path(), "x", encoding="utf-8", newline="\n") as f:
            f.write(data)
        commitment = sha256(data.encode("utf-8"))
        write_new_or_same(self.commitment_path(), f"{commitment}  sealed/mapping.json\n".encode())
        return commitment

    def load_mapping(self):
        """The sealed mapping {code: model name}, after checking it against the committed commitment."""
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
        out = os.path.join(self.diag, "outputs", f"round{rnd}")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "status.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        return lines[2:]

    def finish(self, rnd, attempts):
        """Copy the redacted answer of every code whose last attempt is valid into the repository, then the status."""
        for code in CODES:
            mine = [a for a in attempts if a["code"] == code]
            if mine and mine[-1]["valid"]:
                with open(os.path.join(self.sealed, f"round{rnd}", f"{mine[-1]['label']}.answer.md"),
                          encoding="utf-8") as f:
                    answer = f.read()
                write_new_or_same(os.path.join(self.diag, "outputs", f"round{rnd}", f"{code}.md"),
                                  (answer.rstrip("\n") + "\n").encode("utf-8"))
        return self.write_status(rnd, attempts)

    # ---- rounds --------------------------------------------------------------------------------------------------
    def prompts(self, rnd, code):
        """(system bytes, user bytes, prompt_ok) for one model in one round."""
        with open(os.path.join(self.diag, "prompts", "system.md"), "rb") as f:
            system = f.read()
        if rnd == 1:
            path = os.path.join(self.diag, "prompts", "round1_user.md")
            expected = self.round1_bytes()
        else:
            path = os.path.join(self.diag, "prompts", "round2", f"{code}.md")
            expected = self.round2_bytes(code)
        with open(path, "rb") as f:
            user = f.read()
        return system, user, user == expected

    def round1_bytes(self):
        import build_prompt
        return build_prompt.round1_bytes()

    def round2_bytes(self, code):
        import build_prompt
        return build_prompt.round2_bytes(code)

    def runnable(self, rnd):
        if rnd == 1:
            return set(CODES)
        runnable = {c for c in CODES if os.path.exists(os.path.join(self.diag, "outputs", "round1", f"{c}.md"))}
        rel = os.path.relpath(self.diag, self.repo).replace(os.sep, "/")
        needed = [f"{rel}/{d}" for d in ("round2", "prompts/round2", "outputs/round1")]
        needed += [f"{rel}/{d}" for c in sorted(runnable)
                   for d in (f"prompts/round2/{c}.md", f"round2/{c}_results.md", f"outputs/round1/{c}.md")]
        needed.append(f"{rel}/round2/translation.tsv")
        if os.path.isdir(os.path.join(self.diag, "queries", "round2")):
            needed += [f"{rel}/queries/round2", f"{rel}/queries/round2/SHA256SUMS"]
        problems = tracked_problems(self.repo, needed)
        if problems:
            raise SystemExit("ROUND FAIL: round-2 inputs not committed: " + "; ".join(problems))
        return runnable

    def run_attempts(self, rnd, attempts, todo):
        """todo: [(entry, code, attempt number)] in run order. Each attempt is recorded before and after the call."""
        sealed_dir = os.path.join(self.sealed, f"round{rnd}")
        os.makedirs(sealed_dir, exist_ok=True)
        for (entry, code, n), workdir in zip(todo, self.make_workdirs(len(todo))):
            system, user, ok = self.prompts(rnd, code)
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
        self.run_attempts(rnd, attempts, [(e, codes[e["name"]], 1) for e in self.models   # fixed, pre-registered
                                          if codes[e["name"]] in runnable])               # order
        return self.finish(rnd, attempts)

    def resume(self, rnd):
        attempts = self.load_attempts(rnd)
        if not attempts:
            raise SystemExit(f"ROUND FAIL: round {rnd} has not started; nothing to resume")
        codes = {v: k for k, v in self.load_mapping().items()}
        for a in attempts:
            if a["state"] == "started":                                 # interrupted: one void attempt
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
        sealed_dir = os.path.join(self.sandbox_root, "smoke-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.makedirs(sealed_dir)
        with open(os.path.join(self.diag, "prompts", "smoke_system.md"), "rb") as f:
            system = f.read()
        with open(os.path.join(self.diag, "prompts", "smoke_user.md"), "rb") as f:
            user = f.read()
        all_ok = True
        for entry, workdir in zip(self.models, self.make_workdirs(len(self.models))):
            meta = self.attempt(entry, system, user, True, sealed_dir, entry["name"], workdir)
            with open(os.path.join(sealed_dir, f"{entry['name']}.answer.md"), encoding="utf-8") as f:
                answer = f.read()
            canaries = all(c in answer for c in SMOKE_CANARIES)
            all_ok &= meta["valid"] and canaries
            print(f"{entry['name']}: valid={meta['valid']} canaries={canaries} "
                  f"per_turn_effort_active={meta['per_turn_effort_active']} "
                  f"maxOutputTokens={meta['max_output_tokens']} exit={meta['exit']} retries={meta['api_retries']}")
            for cat, detail in meta["problems"]:
                print(f"  {cat}: {detail}")
        print(f"SMOKE {'OK' if all_ok else 'FAIL'} -> {sealed_dir}")
        return 0 if all_ok else 1


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--round", type=int, choices=(1, 2))
    g.add_argument("--smoke", action="store_true")
    g.add_argument("--init-mapping", action="store_true")
    h = ap.add_mutually_exclusive_group()
    h.add_argument("--rerun", choices=CODES)
    h.add_argument("--resume", action="store_true")
    ap.add_argument("--repo-root")
    ap.add_argument("--diag-dir")
    ap.add_argument("--sandbox-root", default=r"D:\study\diag_sandbox")
    ap.add_argument("--claude-cmd", help="tests only: JSON list replacing the pinned claude executable")
    ap.add_argument("--no-tags", action="store_true", help="tests only: skip the pre-registration tag check")
    args = ap.parse_args(argv)
    if (args.rerun or args.resume) and not args.round:
        ap.error("--rerun and --resume need --round")
    from diagpaths import DIAG, REPO
    repo, diag = args.repo_root or REPO, args.diag_dir or DIAG
    claude_cmd = json.loads(args.claude_cmd) if args.claude_cmd else [CLI_PATH]
    mode = "round" if args.round else "smoke"
    if args.no_tags and any(git(repo, "rev-parse", "-q", "--verify", f"refs/tags/{t}").returncode == 0
                            for t in TAGS.values()):
        print("ROUND FAIL: --no-tags is for tests only and is refused once a pre-registration tag exists")
        return 1
    problems = prereg_problems(repo, os.path.join(diag, "rules", "preregistered.txt"), mode, not args.no_tags)
    if problems:
        for p in problems:
            print(f"PREREG {p}")
        print("ROUND FAIL: pre-registered files are not all committed and unchanged")
        return 1
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    runner = RoundRunner(repo, diag, args.sandbox_root, claude_cmd)
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
    what = "smoke" if args.smoke else f"round {args.round}" + (f" rerun {args.rerun}" if args.rerun else "") + (
        " resume" if args.resume else "")
    what += " no-tags" if args.no_tags else ""
    with open(os.path.join(runner.sealed, "heads.log"), "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} HEAD={head} {what}\n")
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
