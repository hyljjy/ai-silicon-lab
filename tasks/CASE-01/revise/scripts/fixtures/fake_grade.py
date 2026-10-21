"""Stand-in for scripts/grade.py in test_run_grade (CASE-01 stage B, Task 5). Never used for a real evaluation.

  fake_grade.py --mode <mode> --impl config/impl.<code>.cfg

Self-limited (Global Constraints): every process exits on its own after at most 10 s, and the whole output is capped at
64 KB, whatever the wrapper under test does. Run from the (temporary) case directory: like grade.py it creates
runs/<run_id>/ there, prints RUN_ID=<run_id> as its first line and a final 'GRADE OK:'/'GRADE FAIL:' line.

Modes:
  <sample>     replay fixtures/runs/<sample>/: meta.json gives run_dir, exit code and final line ({run_id} is
               substituted; null = no final line); run/ is copied into the run directory; inputs.sha256 is written
               when a run directory exists; "sta_files": true also writes small sta/ files (sta_analysis pass).
  hang         RUN_ID, then a tool child in a NEW SESSION (start_new_session=True, like grade.py:283-284), then wait.
               SIGTERM: kill the child's process group, write steps.json with the running step marked interrupted,
               print 'GRADE FAIL: interrupted: SystemExit' and exit 143 (grade.py:687-709).
  hang_leak    like hang, but on SIGTERM it exits 143 WITHOUT killing its new-session child (the wrapper must find
               and kill that child itself).
  remove_gl    deletes $SKY130_HD/verilog/sky130_fd_sc_hd.v (the gate-level model) during the run, then fails outside
               the steps like grade.py does when the model cannot be read (grade.py:624-629).
Every child pid is printed as 'child <pid>' and appended to runs/<run_id>/children.txt.
"""
import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

MAX_SECONDS = 10
MAX_OUTPUT = 64 * 1024
HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "runs")
STD = ["tt_025C_1v80", "tt_100C_1v80", "ss_100C_1v60", "ss_n40C_1v60", "ff_n40C_1v95", "ff_100C_1v95"]
SLEEPER = ("import time\nt = time.monotonic()\nwhile time.monotonic() - t < %d:\n    time.sleep(0.05)\n"
           % MAX_SECONDS)

_written = 0
_children = []


def out(line):
    """Print one line, never more than MAX_OUTPUT bytes in total (then exit at once)."""
    global _written
    data = (line + "\n").encode("utf-8")
    if _written + len(data) > MAX_OUTPUT:
        os._exit(4)
    _written += len(data)
    try:
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    except (BrokenPipeError, OSError):
        pass


def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1)


def impl_name(cfg):
    with open(cfg, encoding="utf-8") as f:
        for line in f:
            key, _, value = line.partition("=")
            if key.strip() == "name":
                return value.strip()
    return "x"


def new_run(name):
    run_id = f"{datetime.datetime.now():%Y%m%d-%H%M%S}-{name}-T27.91-{os.getpid()}"
    root = os.path.join(os.getcwd(), "runs", run_id)
    os.makedirs(root)
    with open(os.path.join(root, "inputs.sha256"), "w", encoding="utf-8", newline="\n") as f:
        f.write("0" * 64 + "  config/impl.%s.cfg\n" % name)
    out(f"RUN_ID={run_id}")
    return run_id, root


def spawn_child(root):
    p = subprocess.Popen([sys.executable, "-B", "-c", SLEEPER], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    _children.append(p)
    with open(os.path.join(root, "children.txt"), "a", encoding="ascii") as f:
        f.write(f"{p.pid}\n")
    out(f"child {p.pid}")
    return p


def sample_steps(upto):
    with open(os.path.join(SAMPLES, "success", "run", "steps.json"), encoding="utf-8") as f:
        steps = json.load(f)
    names = [s["step"] for s in steps]
    return steps[:names.index(upto) + 1]


def replay(sample, name):
    with open(os.path.join(SAMPLES, sample, "meta.json"), encoding="utf-8") as f:
        meta = json.load(f)
    run_id = None
    if meta["run_dir"]:
        run_id, root = new_run(name)
        out("frozen inputs copied")
        src = os.path.join(SAMPLES, sample, "run")
        for base, _, files in os.walk(src):
            for fn in files:
                rel = os.path.relpath(os.path.join(base, fn), src)
                dst = os.path.join(root, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(os.path.join(base, fn), dst)
        if meta.get("sta_files"):
            sta = os.path.join(root, "sta")
            os.makedirs(sta, exist_ok=True)
            names = ["sta_results.tsv", "sta_check.json"] + [f"cat_{c}_in2reg_max.rpt" for c in STD] + \
                [f"path_{k}_{c}.rpt" for k in ("max", "min") for c in STD]
            for n in names:
                with open(os.path.join(sta, n), "w", encoding="utf-8", newline="\n") as f:
                    f.write('{"fake": true}\n' if n.endswith(".json") else f"fake {n}\n")
    else:
        out("checking the implementation config")
    if meta["final"] is not None:
        out(meta["final"].replace("{run_id}", run_id or ""))
    sys.stdout.flush()
    os._exit(meta["exit"])


def hang(name, leak):
    run_id, root = new_run(name)
    steps = sample_steps("rtl_compile")
    child = spawn_child(root)

    def on_term(signum, frame):
        if not leak:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except OSError:
                pass
            child.wait()
        rec = dict(steps[-1], step="rtl_sim", returncode=-9, logs=["rtl_sim/sim.log"], log_problems=[],
                   interrupted="SystemExit")
        wjson(os.path.join(root, "steps.json"), steps + [rec])
        wjson(os.path.join(root, "verdict.json"), {"functional_pass": False, "analysis_valid": False,
                                                   "run_id": run_id, "error": "interrupted: SystemExit"})
        out("GRADE FAIL: interrupted: SystemExit")
        os._exit(143)

    signal.signal(signal.SIGTERM, on_term)
    out("running rtl_sim")
    while True:
        time.sleep(0.05)


def remove_gl(name):
    run_id, root = new_run(name)
    hd = os.environ.get("SKY130_HD", "")
    model = os.path.join(hd, "verilog", "sky130_fd_sc_hd.v")
    try:
        os.remove(model)
    except OSError:
        pass
    wjson(os.path.join(root, "steps.json"), sample_steps("synth"))
    wjson(os.path.join(root, "verdict.json"), {"functional_pass": False, "analysis_valid": False, "run_id": run_id,
                                               "error": f"FileNotFoundError: no such file: {model}"})
    out(f"GRADE FAIL: FileNotFoundError: [Errno 2] No such file or directory: '{model}'")
    os._exit(1)


def main():
    threading.Timer(MAX_SECONDS, lambda: os._exit(3)).start()
    args = sys.argv[1:]
    mode = args[args.index("--mode") + 1]
    cfg = args[args.index("--impl") + 1]
    name = impl_name(cfg)
    if mode in ("hang", "hang_leak"):
        hang(name, leak=(mode == "hang_leak"))
    elif mode == "remove_gl":
        remove_gl(name)
    else:
        replay(mode, name)


if __name__ == "__main__":
    main()
