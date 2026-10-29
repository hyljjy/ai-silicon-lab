"""R1/R2 assignment: commitment, sealing and resolution (protocol v0.3 sections 6.2, 8, 9; rules/layout.md).

Formal runs: contexts.commit() draws the assignment {"R1": version, "R2": version} (correct / missing), writes it
with a salt to the sealed directory (outside git) and its sha256 to outputs/assign.sha256 (committed at tier 2).
contexts.resolve(ctx) is the only way the executor learns which version a context is; it checks that the commitment
file is tracked and unchanged (checker) and that the sealed file still hashes to it.
Self-tests use a fixed, unsealed assignment file under runs/ so that nothing before tier 1 touches the sealed dir."""
import hashlib
import json
import os
import secrets
import subprocess

import c2paths

VERSIONS = ("correct", "missing")
CTXS = ("R1", "R2")
SEALED_DIR_WIN = r"D:\study\diag_sandbox\sealed-case02"
SEALED_DIR_WSL = "/mnt/d/study/diag_sandbox/sealed-case02"
SELFTEST_ASSIGN = {"R1": "correct", "R2": "missing"}


class AssignError(RuntimeError):
    pass


def sealed_dir():
    return os.environ.get("CASE02_SEALED") or (SEALED_DIR_WIN if os.name == "nt" else SEALED_DIR_WSL)


def selftest_assign_path():
    return os.path.join(c2paths.RUNS, "selftest_assign.json")


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def tracked_and_unchanged(path, repo=c2paths.REPO):
    """Problems if `path` is not tracked by git or differs from HEAD (the commitment must be committed before any
    formal resolution)."""
    rel = os.path.relpath(path, repo).replace(os.sep, "/")
    problems = []
    try:
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=repo, capture_output=True,
                                 text=True).returncode == 0
    except OSError as e:
        return [f"git not available: {e}"]
    if not tracked:
        return [f"{rel} is not tracked by git"]
    head = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=repo, capture_output=True).stdout
    with open(path, "rb") as f:
        if f.read() != head:
            problems.append(f"{rel} differs from HEAD")
    return problems


def commit(selftest, sealed_dir=None, out_dir=None, selftest_path=None):
    """Draw and seal the assignment (formal) or write the fixed self-test assignment. Returns the assignment."""
    if selftest:
        path = selftest_path or selftest_assign_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(dict(SELFTEST_ASSIGN), f, ensure_ascii=False, indent=1)
        return dict(SELFTEST_ASSIGN)
    sdir = sealed_dir or globals()["sealed_dir"]()
    odir = out_dir or c2paths.OUTPUTS
    sealed_path = os.path.join(sdir, "assign.json")
    commit_path = os.path.join(odir, "assign.sha256")
    if os.path.exists(sealed_path) or os.path.exists(commit_path):
        raise AssignError("assignment already committed; it is never redrawn")
    r1 = secrets.choice(VERSIONS)
    assign = {"R1": r1, "R2": "missing" if r1 == "correct" else "correct"}
    data = json.dumps({"R1": assign["R1"], "R2": assign["R2"], "salt": secrets.token_hex(16)},
                      ensure_ascii=False, indent=1).encode("utf-8") + b"\n"
    os.makedirs(sdir, exist_ok=True)
    with open(sealed_path, "wb") as f:
        f.write(data)
    os.makedirs(odir, exist_ok=True)
    with open(commit_path, "w", newline="\n") as f:
        f.write(f"{hashlib.sha256(data).hexdigest()}  assign.json\n")
    return assign


def _load_sealed(sdir, odir, checker):
    sealed_path = os.path.join(sdir, "assign.json")
    commit_path = os.path.join(odir, "assign.sha256")
    if not os.path.exists(commit_path):
        raise AssignError("outputs/assign.sha256 missing: the assignment was never committed")
    problems = checker(commit_path)
    if problems:
        raise AssignError("assignment commitment not committed in git: " + "; ".join(problems))
    with open(commit_path) as f:
        want = f.read().split()[0]
    if not os.path.exists(sealed_path):
        raise AssignError("sealed assign.json missing")
    if _sha(sealed_path) != want:
        raise AssignError("sealed assign.json does not hash to the committed value")
    with open(sealed_path, encoding="utf-8") as f:
        d = json.load(f)
    return {"R1": d["R1"], "R2": d["R2"]}


def resolve(ctx, selftest, sealed_dir=None, out_dir=None, checker=tracked_and_unchanged, selftest_path=None):
    """The version (correct / missing) behind a context label. Formal mode verifies the commitment first."""
    if ctx not in CTXS:
        raise AssignError(f"unknown context {ctx!r}; one of {CTXS}")
    if selftest:
        path = selftest_path or selftest_assign_path()
        if not os.path.exists(path):
            raise AssignError(f"self-test assignment {path} missing; run contexts.commit(selftest=True)")
        with open(path, encoding="utf-8") as f:
            assign = json.load(f)
    else:
        assign = _load_sealed(sealed_dir or globals()["sealed_dir"](), out_dir or c2paths.OUTPUTS, checker)
    version = assign[ctx]
    if version not in VERSIONS:
        raise AssignError(f"assignment names unknown version {version!r}")
    return version


def label_of(version, assign):
    for ctx, v in assign.items():
        if v == version:
            return ctx
    raise AssignError(f"{version!r} not in the assignment")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "commit":
        st = "--selftest" in sys.argv
        a = commit(selftest=st)
        print("committed" + (" (selftest)" if st else "") + ": R1, R2 drawn" + (f" {a}" if st else ""))
    else:
        print("usage: contexts.py commit [--selftest]")
