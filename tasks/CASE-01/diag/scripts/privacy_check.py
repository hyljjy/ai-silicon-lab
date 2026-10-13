"""Privacy check before committing diag files or the article (protocol v0.5 section 10).

  python3 -B diag/scripts/privacy_check.py <file or directory>...          # files as they are on disk
  python3 -B diag/scripts/privacy_check.py --staged [--message <text>]     # what the next commit would contain

Fails (exit 1) when a file contains the account e-mail (read at run time from `git config user.email`, so it is never
written into the repository) or an absolute Windows user-directory path in any spelling: a drive letter, then "Users",
then a name, separated by backslashes, forward slashes or JSON-escaped double backslashes; also the Git Bash and WSL
mount forms (/<drive>/Users/<name>, /mnt/<drive>/Users/<name>). WSL paths under /home/eda are allowed: they are already
public in evidence/F1. --staged scans the staged blob of every staged file (`git show :<path>`), not the working tree,
and --message also scans the commit message. UTF-16 text (with a byte-order mark) is decoded; any other content with
a NUL byte cannot be checked and is a failure. Hits are reported as file:line and kind only, never the matched text.
"""
import argparse
import os
import re
import subprocess
import sys

SEP = r"(?:\\\\|\\|/)+"
USER_DIR = re.compile(r"(?i)(?:\b[a-z]:" + SEP + "users" + SEP + r"[^\\/\s\"'`<>|]+"
                      r"|(?:/mnt)?/[a-z]/users/[^/\s\"'`<>|]+)")


def account_email():
    email = os.environ.get("CASE01_PRIVACY_EMAIL")          # tests only
    if email is None:
        email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True).stdout.strip()
    if not email:
        raise SystemExit("PRIVACY FAIL: git config user.email is empty; cannot check for the account e-mail")
    return email


def files_under(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
                for n in sorted(names):
                    yield os.path.join(root, n)
        else:
            yield p


def scan_bytes(data, email):
    """Return [(line_no, kind)] for one file's bytes."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = data.decode("utf-16", errors="replace")
    elif b"\0" in data:
        return [(0, "含 NUL 字节，无法检查")]
    else:
        text = data.decode("utf-8", errors="replace")
    hits = []
    low_email = email.lower()
    for n, line in enumerate(text.splitlines(), 1):
        if low_email in line.lower():
            hits.append((n, "账号邮箱"))
        if USER_DIR.search(line):
            hits.append((n, "用户目录路径"))
    return hits


def read_file(path):
    with open(path, "rb") as f:
        return f.read()


def scan(path, email):
    return scan_bytes(read_file(path), email)


def staged_files():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
                         capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def staged_blob(path):
    return subprocess.run(["git", "show", f":{path}"], capture_output=True, check=True).stdout


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--message")
    args = ap.parse_args(argv)
    if bool(args.paths) == args.staged or (args.message is not None and not args.staged):
        ap.error("give paths, or --staged [--message <text>]")
    email = account_email()
    if args.staged:
        targets = [(p, (lambda p=p: staged_blob(p))) for p in staged_files()]
        if not targets:
            print("PRIVACY FAIL: nothing staged")
            return 1
        if args.message is not None:
            targets.append(("<commit message>", lambda: args.message.encode("utf-8")))
    else:
        targets = [(p, (lambda p=p: read_file(p))) for p in files_under(args.paths)]
    total = 0
    for name, read in targets:
        for n, kind in scan_bytes(read(), email):
            print(f"PRIVACY HIT {name}:{n} {kind}")
            total += 1
    print(f"PRIVACY {'FAIL' if total else 'OK'}: {total} hit(s) in {len(targets)} item(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
