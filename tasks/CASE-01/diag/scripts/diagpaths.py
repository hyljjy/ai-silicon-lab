"""Shared paths for the CASE-01 diag scripts (protocol v0.5). Works both installed (tasks/CASE-01/diag/scripts) and
from the plan prototype (tasks/CASE-01/diag/plan/proto/scripts): DIAG is always the parent of this scripts/ directory."""
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DIAG = os.path.dirname(HERE)
RULES = os.path.join(DIAG, "rules")
PROMPTS = os.path.join(DIAG, "prompts")
PACKAGE = os.path.join(DIAG, "package")
PACKAGE_SRC = os.path.join(DIAG, "package_src")
OUTPUTS = os.path.join(DIAG, "outputs")


def find_case(start=HERE):
    """The CASE-01 directory: the nearest ancestor holding config/f1.cfg and scripts/grade.py."""
    d = start
    while True:
        if os.path.isfile(os.path.join(d, "config", "f1.cfg")) and os.path.isfile(os.path.join(d, "scripts", "grade.py")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("DIAG FAIL: tasks/CASE-01 not found above " + start)
        d = parent


CASE = find_case()
REPO = os.path.dirname(os.path.dirname(CASE))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_new_or_same(path, data):
    """Write bytes; an existing file must already hold exactly these bytes (pre-registered files never change)."""
    if os.path.exists(path):
        if read_bytes(path) != data:
            raise SystemExit(f"DIAG FAIL: {path} exists with different content; pre-registered files are not rewritten")
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return True
