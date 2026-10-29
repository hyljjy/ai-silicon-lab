"""Shared paths for the CASE-02 scripts (protocol v0.3 section 8; copied and adapted from
tasks/CASE-01/diag/scripts/diagpaths.py, see rules/copied_from.tsv). Works both installed (tasks/CASE-02/scripts)
and from the scratch implementation directory (tasks/CASE-02/runs/impl/<task>): CASE is the nearest ancestor that
holds protocol.md and appendix_A.md."""
import datetime
import hashlib
import os
import secrets

HERE = os.path.dirname(os.path.abspath(__file__))


def find_case(start=HERE):
    d = start
    while True:
        if os.path.isfile(os.path.join(d, "protocol.md")) and os.path.isfile(os.path.join(d, "appendix_A.md")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("CASE02 FAIL: tasks/CASE-02 not found above " + start)
        d = parent


CASE = find_case()
REPO = os.path.dirname(os.path.dirname(CASE))
RULES = os.path.join(CASE, "rules")
SCRIPTS = os.path.join(CASE, "scripts")
QUERIES = os.path.join(CASE, "queries")
PACKAGE = os.path.join(CASE, "package")
PACKAGE_SRC = os.path.join(CASE, "package_src")
PROMPTS = os.path.join(CASE, "prompts")
OUTPUTS = os.path.join(CASE, "outputs")
ROUND2 = os.path.join(CASE, "round2")
RUNS = os.path.join(CASE, "runs")
PREVALIDATION = os.path.join(CASE, "prevalidation")
CASE01 = os.path.join(REPO, "tasks", "CASE-01")
CASE01_DIAG = os.path.join(CASE01, "diag")
CASE01_SCRIPTS = os.path.join(CASE01, "scripts")
F1_RUN_NAME = "20261009-092827-base-T27.91"
F1_ARCHIVE = os.path.join(CASE01, "evidence", "F1", "archive", F1_RUN_NAME)


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
            raise SystemExit(f"CASE02 FAIL: {path} exists with different content; pre-registered files are not rewritten")
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return True


def new_run_dir(kind, ident, runs=RUNS):
    """A fresh, never-reused run directory runs/<ts>-c2-<kind>-<ident>-<4 random hex>/."""
    while True:
        name = f"{datetime.datetime.now():%Y%m%d-%H%M%S}-c2-{kind}-{ident}-{secrets.token_hex(2)}"
        path = os.path.join(runs, name)
        if not os.path.exists(path):
            os.makedirs(path)
            return path
