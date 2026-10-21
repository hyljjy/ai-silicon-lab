"""Process-tree fixture for test_limits. Self-limited: every process exits on its own after at most 10 s and the whole
tree prints a few lines only (far below 64 KB), whatever the wrapper under test does.

  tree.py --pidfile F [--new-session | --no-children | --ignore-term | --orphan | --root-exits] [--marker M]

Every process appends "<role> <pid>\\n" to the pid file as soon as it starts. The root prints "ready <pid>" on stdout.
  (default)       root -> child -> grandchild, all in the same session, all sleep
  --new-session   the child starts the grandchild in a new session / process group
  --no-children   the root alone
  --ignore-term   the root alone, ignoring SIGTERM (POSIX)
  --orphan        the child starts the grandchild in a new session and exits at once; root and grandchild sleep
  --root-exits    the root starts a grandchild in a new session, waits until it is registered in the pid file, exits 0
"""
import os
import signal
import subprocess
import sys
import time

MAX_SECONDS = 10
START = time.monotonic()


def note(pidfile, role):
    with open(pidfile, "a", encoding="ascii") as f:
        f.write(f"{role} {os.getpid()}\n")


def sleep_out():
    while time.monotonic() - START < MAX_SECONDS:
        time.sleep(0.05)
    sys.exit(3)


def spawn(args, new_session):
    kw = {"stdin": subprocess.DEVNULL}
    if new_session:
        if os.name == "nt":
            kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kw["start_new_session"] = True
    return subprocess.Popen([sys.executable, "-B", os.path.abspath(__file__)] + args, **kw)


def wait_for_line(pidfile, role):
    while time.monotonic() - START < MAX_SECONDS:
        with open(pidfile, encoding="ascii") as f:
            if any(line.startswith(role + " ") for line in f):
                return
        time.sleep(0.02)
    sys.exit(4)


def main(argv):
    pidfile = argv[argv.index("--pidfile") + 1]
    role = argv[argv.index("--role") + 1] if "--role" in argv else "root"
    if "--marker" in argv:
        with open(argv[argv.index("--marker") + 1], "w", encoding="ascii") as f:
            f.write("started\n")
    note(pidfile, role)
    mode = next((m for m in ("--new-session", "--no-children", "--ignore-term", "--orphan", "--root-exits")
                 if m in argv), "--default")
    base = ["--pidfile", pidfile, mode]
    if role == "root":
        sys.stdout.write(f"ready {os.getpid()}\n")
        sys.stdout.flush()
        if mode == "--ignore-term":
            if hasattr(signal, "SIGTERM") and os.name != "nt":
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
            sleep_out()
        if mode == "--no-children":
            sleep_out()
        if mode == "--root-exits":
            spawn(base + ["--role", "grandchild"], new_session=True)
            wait_for_line(pidfile, "grandchild")
            sys.exit(0)
        spawn(base + ["--role", "child"], new_session=False)
        sleep_out()
    if role == "child":
        spawn(base + ["--role", "grandchild"], new_session=mode in ("--new-session", "--orphan"))
        if mode == "--orphan":
            wait_for_line(pidfile, "grandchild")
            sys.exit(0)
        sleep_out()
    sleep_out()


if __name__ == "__main__":
    main(sys.argv[1:])
