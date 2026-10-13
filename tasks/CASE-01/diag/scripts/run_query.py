"""Run one diag query on the frozen F1 analysis context (protocol v0.5 sections 7.1 and 8).

Run inside WSL (login shell) from tasks/CASE-01:
  python3 -B diag/scripts/run_query.py --id <query id> --query <file.tcl> [--mode auto|query|whatif] [--strict-log]

Each call is one fresh OpenSTA process in a new directory runs/<ts>-diag-<id>/ (never overwritten):
  1. the executor checks itself against rules/executor.sha256 and refuses to run if anything differs, or if that
     manifest is not committed, equal to HEAD and (once the tag diag-prereg exists) unchanged since that tag
     (--uncommitted-ok: prototype checks and self-tests only); result.json records HEAD;
  2. env/snapshot.sh check;
  3. diag_query.tcl sources F1's frozen sta_run.tcl (rebuilding the exact F1 context and its records), then runs the
     query in a safe Tcl interpreter (allow-listed commands only, no redirection, time and command-count limits);
  4. the environment check decides env_ok: snapshot, frozen inputs and netlist hashes, every record file equal to
     F1's byte for byte, the environment part of the log clean under logcheck, and the query section reached;
  5. the query itself ends as query_status completed | crashed:<rc> | timed_out | output_limit (more than 50 MB of
     log); a crash, timeout or output stop is the query's result (code 工具异常退出), not an environment failure;
  6. --strict-log (base checks and the operator's own rechecks): the query output must also pass logcheck.
The query output is kept in full and also returned truncated (200 lines: first 100 + last 100) with result codes.
Exit status: 0 when env_ok is true (and, with --strict-log, the query log is clean); 1 otherwise.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from diagpaths import CASE, DIAG, REPO, RULES  # noqa: E402
sys.path.insert(0, os.path.join(CASE, "scripts"))
import logcheck  # noqa: E402

F1_RUN = os.path.join(CASE, "runs", "20261009-092827-base-T27.91")
NETLIST_SHA = "1fa89c975162f4f1f9a2f349bed73b4dae5f53ab921883be842cb0a37763a8d1"
EXPANDED_SDC_SHA = "c4e85ff0401eb803"           # prefix of F1 sta/expanded.sdc
GIVEN_REPORT_SHA = "043e50bf6638284a"           # prefix of the report given to the models
GIVEN_REPORT = "cat_ss_n40C_1v60_in2reg_max.rpt"
NOT_RECORDS = {"sta.log", "check.log", "sta_check.json"}   # written by grade.py/check_sta.py, not by sta_run.tcl
FROZEN_FROM_F1 = ("scripts/sta_run.tcl", "sdc/case01_sdc.tcl")
T_NS = "27.91"
TIMEOUT_S = 600
QUERY_SECONDS = 300
MAX_LINES = 200
MAX_LOG_BYTES = 50 * 1024 * 1024        # a query that prints more is stopped (status output_limit)
PREREG_TAG = "diag-prereg"                 # pre-registration tag of the executor manifest (protocol section 3)
EXECUTOR = ("scripts/run_query.py", "scripts/diag_query.tcl", "scripts/diagpaths.py", "rules/allow_query.txt",
            "rules/allow_whatif.txt", "rules/setup_commands.txt", "@case/scripts/logcheck.py")

CODE_DONE = "已执行"
CODE_SYNTAX = "语法错误"
CODE_NO_OBJECT = "对象不存在"
CODE_WHATIF = "改变冻结模型的查询（已在单独运行中执行）"
CODE_SETUP = "环境已由冻结环境提供，未执行"
CODE_CRASH = "工具异常退出"
LIMIT_ERRORS = re.compile(r"time limit exceeded|command count limit exceeded", re.I)
NOT_FOUND = re.compile(r"not found|does not exist|cannot find", re.I)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def words(path):
    with open(path, encoding="utf-8") as f:
        return [w.strip() for w in f if w.strip() and not w.strip().startswith("#")]


def executor_path(rel, diag=DIAG, case=CASE):
    return os.path.join(case, rel[len("@case/"):]) if rel.startswith("@case/") else os.path.join(diag, rel)


def executor_hashes(diag=DIAG, case=CASE):
    return {rel: sha256(executor_path(rel, diag, case)) for rel in EXECUTOR}


def manifest_committed(manifest, repo=REPO, tag=PREREG_TAG):
    """The manifest is tracked by git, equal to HEAD and, once the pre-registration tag exists, unchanged since it
    (so the executor it pins is the pre-registered one)."""
    git = lambda *a: subprocess.run(["git", "-C", repo] + list(a), capture_output=True).returncode == 0
    if not (git("ls-files", "--error-unmatch", "--", manifest) and git("diff", "--quiet", "HEAD", "--", manifest)):
        return False
    return not git("rev-parse", "-q", "--verify", f"refs/tags/{tag}") or git("diff", "--quiet", tag, "HEAD", "--",
                                                                             manifest)


def git_head(repo=REPO):
    p = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def executor_problems(manifest, diag=DIAG, case=CASE):
    """Protocol section 3 step 3 / 7.1 e: the executor must be the pre-registered one."""
    if not os.path.exists(manifest):
        return [f"executor manifest {os.path.relpath(manifest, case)} missing"]
    want = {}
    with open(manifest) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                digest, rel = line.split(None, 1)
                want[rel.strip()] = digest
    got = executor_hashes(diag, case)
    return [f"executor file {rel} differs from {os.path.basename(manifest)}" for rel in EXECUTOR
            if want.get(rel) != got[rel]] + [f"manifest lists unknown file {rel}" for rel in want if rel not in got]


def strip_comments(text):
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def choose_mode(query_text, whatif_words, t_ns=T_NS):
    """'whatif' when the query calls a model-changing command (protocol 8 h), else 'query'. Comment lines are
    ignored. create_clock with a literal -period equal to T is a setup command (8 b) and does not count."""
    text = strip_comments(query_text)
    for w in whatif_words:
        pattern = r"(?<![\w:])" + re.escape(w) + r"(?![\w])"
        if w == "create_clock":
            for m in re.finditer(pattern + r"([^\n;\]]*)", text):
                period = re.search(r"-period\s+([0-9.eE+-]+)(?![\w$\[])", m.group(1))
                try:
                    same = period is not None and float(period.group(1)) == float(t_ns)
                except ValueError:
                    same = False
                if not same:
                    return "whatif"
        elif re.search(pattern, text):
            return "whatif"
    return "query"


def truncate(lines, limit=MAX_LINES):
    """Protocol 8 g: more than `limit` lines -> first limit/2 + marker + last limit/2."""
    if len(lines) <= limit:
        return lines, False
    half = limit // 2
    marker = f"... [已截断：共 {len(lines)} 行，保留开头 {half} 行和结尾 {half} 行] ..."
    return lines[:half] + [marker] + lines[-half:], True


def split_log(text, nonce):
    """Return (env_part, query_lines, mode, rc) of a diag_query.tcl log; rc None when the END marker is missing.
    Only markers carrying this run's nonce count."""
    begin_re = re.compile(r"^=== CASE01-" + re.escape(nonce) + r" QUERY BEGIN \((query|whatif)\) ===$")
    end_re = re.compile(r"^=== CASE01-" + re.escape(nonce) + r" QUERY END rc=(\d+) ===$")
    lines = text.splitlines()
    begin = next((i for i, l in enumerate(lines) if begin_re.match(l)), None)
    if begin is None:
        return text, [], None, None
    end = next((i for i in range(len(lines) - 1, begin, -1) if end_re.match(lines[i])), None)
    mode = begin_re.match(lines[begin]).group(1)
    if end is None:
        return "\n".join(lines[:begin]), lines[begin + 1:], mode, None
    return "\n".join(lines[:begin]), lines[begin + 1:end], mode, int(end_re.match(lines[end]).group(1))


def normalize(lines, nonce):
    """The returned output shows plain CASE01- markers (the nonce is only for parsing)."""
    tag = f"CASE01-{nonce}-"
    return [l.replace(tag, "CASE01-") for l in lines]


def classify(mode, query_lines, rc, status, nonce):
    """Fixed result codes (protocol 8 f); several can apply to one query."""
    tag = f"CASE01-{nonce}-"
    codes = []
    if mode == "whatif":
        codes.append(CODE_WHATIF)
    if any(l.startswith(tag + "CODE: SETUP_SKIPPED") for l in query_lines):
        codes.append(CODE_SETUP)
    errors = [l for l in query_lines if l.startswith(tag + "ERROR:")]
    if status != "completed" or any(LIMIT_ERRORS.search(e) for e in errors):
        codes.append(CODE_CRASH)
    plain = [e for e in errors if not LIMIT_ERRORS.search(e)]
    if any(NOT_FOUND.search(e) for e in plain) or re.search(r"^Warning( \d+)?: .*not found", "\n".join(query_lines),
                                                             re.M):
        codes.append(CODE_NO_OBJECT)
    if any(not NOT_FOUND.search(e) for e in plain):
        codes.append(CODE_SYNTAX)
    return codes or [CODE_DONE]


def compare_records(env_dir, f1_sta_dir):
    """Problems if any record file sta_run.tcl wrote differs from F1's (protocol 7.1 d)."""
    problems = []
    f1_files = sorted(n for n in os.listdir(f1_sta_dir) if n not in NOT_RECORDS)
    got = sorted(os.listdir(env_dir)) if os.path.isdir(env_dir) else []
    if got != f1_files:
        problems.append(f"record file set differs: missing {sorted(set(f1_files) - set(got))}, "
                        f"extra {sorted(set(got) - set(f1_files))}")
    for name in f1_files:
        p = os.path.join(env_dir, name)
        if os.path.exists(p) and sha256(p) != sha256(os.path.join(f1_sta_dir, name)):
            problems.append(f"{name} differs from F1")
    for name, prefix in (("expanded.sdc", EXPANDED_SDC_SHA), (GIVEN_REPORT, GIVEN_REPORT_SHA)):
        p = os.path.join(env_dir, name)
        if not os.path.exists(p) or not sha256(p).startswith(prefix):
            problems.append(f"{name} sha256 is not {prefix}…")
    return problems


def check_frozen_inputs(case_dir, f1_sha_path):
    problems = []
    want = {}
    with open(f1_sha_path) as f:
        for line in f:
            digest, rel = line.split(None, 1)
            want[rel.strip()] = digest
    for rel in FROZEN_FROM_F1:
        if sha256(os.path.join(case_dir, rel)) != want.get(rel):
            problems.append(f"{rel} in {case_dir} does not match config/f1.sha256")
    return problems


def kill_tree(proc):
    """Kill proc and every process it started, on Windows as well as POSIX. Incident 2026-10-12: os.killpg does not
    exist on Windows; the AttributeError skipped the kill and an orphaned `yes` filled the system disk."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        else:
            os.killpg(proc.pid, signal.SIGKILL)      # start_new_session=True: the group id is the child's pid
    except (OSError, subprocess.SubprocessError):
        pass
    if proc.poll() is None:
        try:
            proc.kill()
        except OSError:
            pass


def reap(proc, cause):
    """Wait for a killed process; one that survives is an error, never a silent orphan."""
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"pid {proc.pid} survived the kill; stop it by hand") from cause


def run_limited(argv, log_path, env, cwd, timeout=TIMEOUT_S, max_bytes=MAX_LOG_BYTES):
    """Wall-clock and log-size limits with a kill of the whole process tree (same pattern as grade.py).
    Returns (rc, stop): stop is None, "timed_out" or "output_limit" (rc is None when stopped)."""
    with open(log_path, "w") as f:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=f,
                                stderr=subprocess.STDOUT, start_new_session=True)
        deadline, stop = time.monotonic() + timeout, None
        try:
            while True:
                try:
                    return proc.wait(timeout=1), None
                except subprocess.TimeoutExpired:
                    if time.monotonic() >= deadline:
                        stop = "timed_out"
                    elif max_bytes and os.path.getsize(log_path) > max_bytes:
                        stop = "output_limit"
                    if stop:
                        raise
        except BaseException as e:
            kill_tree(proc)
            reap(proc, e)
            if isinstance(e, subprocess.TimeoutExpired):
                return None, stop
            raise


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--id")
    ap.add_argument("--query")
    ap.add_argument("--mode", choices=("auto", "query", "whatif"), default="auto")
    ap.add_argument("--strict-log", action="store_true", help="the query output must also pass logcheck")
    ap.add_argument("--timeout", type=int, default=TIMEOUT_S, help="wall-clock limit of the whole STA process (s)")
    ap.add_argument("--query-seconds", type=int, default=QUERY_SECONDS, help="time limit of the safe interpreter")
    ap.add_argument("--selftest-case-dir", help="self-test only: a modified copy of the F1 inputs")
    ap.add_argument("--selftest-cload", help="self-test only: a different C_load")
    ap.add_argument("--uncommitted-ok", action="store_true",
                    help="prototype checks and self-tests only: allow an executor manifest not committed in git "
                         "(recorded as executor_committed false; collect_runs refuses such runs)")
    ap.add_argument("--write-manifest", action="store_true",
                    help="write rules/executor.sha256 for the current executor files (pre-registration only)")
    args = ap.parse_args(argv)
    if args.write_manifest:
        from diagpaths import write_new_or_same
        text = "# sha256 of the diag query executor (protocol v0.5 sections 3 and 7.1 e)\n" + "".join(
            f"{h}  {rel}\n" for rel, h in executor_hashes().items())
        write_new_or_same(os.path.join(RULES, "executor.sha256"), text.encode())
        print("MANIFEST OK: rules/executor.sha256")
        return 0
    if not args.id or not args.query:
        ap.error("--id and --query are required")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.id):
        print(f"DIAG FAIL: bad id {args.id!r}")
        return 1
    bad = executor_problems(os.path.join(RULES, "executor.sha256"))
    if bad:
        for p in bad:
            print(f"  {p}")
        print("DIAG FAIL: the executor is not the pre-registered one; nothing was run")
        return 1
    committed = manifest_committed(os.path.join(RULES, "executor.sha256"))
    if not committed and not args.uncommitted_ok:
        print("DIAG FAIL: rules/executor.sha256 is not committed, or changed since HEAD or the tag diag-prereg; "
              "nothing was run")
        return 1
    with open(args.query, encoding="utf-8") as f:
        query_text = f.read()
    mode = choose_mode(query_text, words(os.path.join(RULES, "allow_whatif.txt"))) if args.mode == "auto" else args.mode

    root = os.path.join(CASE, "runs", f"{datetime.datetime.now():%Y%m%d-%H%M%S}-diag-{args.id}")
    os.makedirs(root)                                       # never overwrite
    env_dir = os.path.join(root, "env")
    os.makedirs(env_dir)
    shutil.copyfile(args.query, os.path.join(root, "query.tcl"))
    case_dir = args.selftest_case_dir or os.path.join(F1_RUN, "inputs")
    netlist = os.path.join(F1_RUN, "synth", "netlist.v")
    nonce = secrets.token_hex(8)
    result = {"id": args.id, "mode": mode, "strict_log": args.strict_log, "query_sha256": sha256(args.query),
              "selftest": bool(args.selftest_case_dir or args.selftest_cload), "netlist_sha256": sha256(netlist),
              "f1_cfg_sha256": sha256(os.path.join(CASE, "config", "f1.cfg")), "executor": executor_hashes(),
              "executor_committed": committed, "head": git_head()}
    problems = []

    rc, _ = run_limited(["bash", os.path.join(REPO, "env", "snapshot.sh"), "check"],
                        os.path.join(root, "snapshot.log"), os.environ, CASE)
    result["snapshot_rc"] = rc
    if rc != 0:
        problems.append("env/snapshot.sh check failed")
    if result["netlist_sha256"] != NETLIST_SHA:
        problems.append("netlist sha256 differs from F1")
    problems += check_frozen_inputs(case_dir, os.path.join(CASE, "config", "f1.sha256"))

    env = dict(os.environ, TOP="dot4sat", NETLIST=netlist, T_NS=T_NS, CLOAD_PF=args.selftest_cload or "0.0024",
               SCENESET="std", OUTDIR=env_dir, CASE_DIR=case_dir, QUERY_FILE=os.path.join(root, "query.tcl"),
               QUERY_MODE=mode, RULES_DIR=RULES, CASE01_NONCE=nonce, CASE01_QUERY_SECONDS=str(args.query_seconds))
    sta_rc, stop = run_limited(["sta", "-no_init", "-no_splash", "-exit", os.path.join(HERE, "diag_query.tcl")],
                                    os.path.join(root, "sta.log"), env, root, args.timeout)
    with open(os.path.join(root, "sta.log"), errors="replace") as f:
        env_part, query_lines, logged_mode, qrc = split_log(f.read(), nonce)
    with open(os.path.join(root, "env_part.log"), "w") as f:
        f.write(env_part)
    if logged_mode != mode:
        problems.append("query section never reached (the environment build failed)")
    rules = logcheck.load_rules(os.path.join(CASE, "config", "warn_whitelist.txt"))
    problems += logcheck.scan("sta", os.path.join(root, "env_part.log"), rules)[0]
    problems += compare_records(env_dir, os.path.join(F1_RUN, "sta"))
    status = stop or ("completed" if sta_rc == 0 and qrc is not None else f"crashed:{sta_rc}")

    shown = normalize(query_lines, nonce)
    with open(os.path.join(root, "query_full.txt"), "w") as f:
        f.write("\n".join(shown) + "\n")
    returned, truncated = truncate(shown)
    if status != "completed":
        ended = f"被信号 {-sta_rc} 终止" if sta_rc is not None and sta_rc < 0 else f"以退出码 {sta_rc} 结束"
        why = {"timed_out": "超过时限被终止", "output_limit": "输出超过上限被终止"}.get(stop, ended)
        returned.append(f"[工具进程{why}，以上为结束前的输出]")
    with open(os.path.join(root, "query_return.txt"), "w") as f:
        f.write("\n".join(returned) + "\n")
    query_log_problems = logcheck.scan("sta", os.path.join(root, "query_full.txt"), rules)[0]
    result.update({"env_ok": not problems, "env_problems": problems, "sta_rc": sta_rc, "timed_out": stop == "timed_out",
                   "query_status": status, "query_rc": qrc, "codes": classify(mode, query_lines, qrc, status, nonce),
                   "query_log_ok": not query_log_problems, "query_log_problems": query_log_problems[:20],
                   "lines": len(query_lines), "truncated": truncated, "run_dir": os.path.relpath(root, CASE)})
    with open(os.path.join(root, "result.json"), "w", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    ok = result["env_ok"] and (result["query_log_ok"] or not args.strict_log)
    status_word = "OK" if ok else ("ENV FAIL" if not result["env_ok"] else "LOG FAIL")
    print(f"DIAG {status_word}: {args.id} mode={mode} status={status} codes={','.join(result['codes'])} "
          f"-> {result['run_dir']}")
    for p in (problems + (query_log_problems if args.strict_log else []))[:10]:
        print(f"  {p}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
