"""Build the stage B materials package revise/package/ (implementation plan Task 9; protocol v0.4 section 5.1).

  python -B revise/scripts/build_package.py [--check]

Package files, in this order (ORDER, also the order in which build_prompt.py inserts them):
  constraints.md       copied verbatim from revise/package_src/constraints.md
  contract_excerpt.md  contract sections 1, 2 and 3.1 verbatim, read with `git show <commit>:./spec.md` from the
                       commit recorded in revise/rules/contract_source.txt ("commit <full hash>" and
                       "spec_sha256 <sha256 of that spec.md>"); the spec bytes must have the recorded sha256
  context.md path_report.rpt case01_sdc.tcl values.txt slack_summary.tsv dot4sat.v
                       the six stage A package files, copied verbatim from diag/package/ after checking each against
                       diag/package/SHA256SUMS
plus SHA256SUMS (the package files in ORDER) and SOURCES.tsv (source and source sha256 of every package file).
An existing package file must already hold exactly the built bytes (never rewritten): a difference is refused.
--check only compares and exits 1 on any difference. git runs through prereg.git (60 s timeout).
Python standard library only; Windows and WSL."""
import os
import re
import sys

import prereg
import revpaths as rp

DIAG_PACKAGE = os.path.join(rp.CASE, "diag", "package")
PACKAGE_SRC = os.path.join(rp.REVISE, "package_src")
CONTRACT_SOURCE = os.path.join(rp.RULES, "contract_source.txt")
STAGE_A = ("context.md", "path_report.rpt", "case01_sdc.tcl", "values.txt", "slack_summary.tsv", "dot4sat.v")
ORDER = ("constraints.md", "contract_excerpt.md") + STAGE_A
LISTINGS = ("SHA256SUMS", "SOURCES.tsv")
_SUM = re.compile(r"^([0-9a-f]{64})  (\S+)$")


class PackageError(Exception):
    pass


def contract_source(path=None):
    """(commit, spec_sha256) from contract_source.txt: exactly the two lines 'commit <40 hex>' and
    'spec_sha256 <64 hex>'."""
    path = path or CONTRACT_SOURCE
    try:
        lines = [ln for ln in rp.read_bytes(path).decode("utf-8").split("\n") if ln.strip()]
    except (OSError, UnicodeDecodeError) as e:
        raise PackageError(f"PACKAGE FAIL: cannot read {path} ({e.__class__.__name__})") from None
    kv = {}
    for ln in lines:
        parts = ln.split()
        if len(parts) != 2 or parts[0] in kv:
            raise PackageError(f"PACKAGE FAIL: {path}: malformed line {ln!r}")
        kv[parts[0]] = parts[1]
    if (set(kv) != {"commit", "spec_sha256"} or not re.fullmatch(r"[0-9a-f]{40}", kv["commit"])
            or not re.fullmatch(r"[0-9a-f]{64}", kv["spec_sha256"])):
        raise PackageError(f"PACKAGE FAIL: {path} must hold 'commit <40 hex>' and 'spec_sha256 <64 hex>'")
    return kv["commit"], kv["spec_sha256"]


def spec_at(commit, case=None):
    """Bytes of spec.md in `commit`, read with git from the directory `case` (default tasks/CASE-01)."""
    rc, out = prereg.git(["show", f"{commit}:./spec.md"], case or rp.CASE)
    if rc != 0:
        raise PackageError(f"PACKAGE FAIL: git show {commit}:./spec.md failed")
    return out


def _section(lines, start_prefix, stop_prefixes):
    starts = [i for i, ln in enumerate(lines) if ln.startswith(start_prefix)]
    if len(starts) != 1:
        raise PackageError(f"PACKAGE FAIL: spec.md must have exactly one heading starting with {start_prefix!r}")
    s = starts[0]
    e = next((i for i in range(s + 1, len(lines)) if lines[i].startswith(stop_prefixes)), None)
    if e is None:
        raise PackageError(f"PACKAGE FAIL: spec.md: no heading after {start_prefix!r}")
    return "".join(lines[s:e]).rstrip("\n") + "\n"


def contract_excerpt(spec_text):
    """Contract sections 1 and 2 (from '## 1. ' up to '## 3. ') and section 3.1 (from '### 3.1 ' up to the next
    heading of level 2 or 3), verbatim, separated by one blank line."""
    lines = spec_text.splitlines(keepends=True)
    one_two = _section(lines, "## 1. ", ("## 3. ",))
    if "\n## 2. " not in "\n" + one_two:
        raise PackageError("PACKAGE FAIL: spec.md: section 2 is not between sections 1 and 3")
    three_one = _section(lines, "### 3.1 ", ("### ", "## "))
    return one_two + "\n" + three_one


def _stage_a_files(diag_package):
    sums = {}
    try:
        text = rp.read_bytes(os.path.join(diag_package, "SHA256SUMS")).decode("ascii")
    except (OSError, UnicodeDecodeError) as e:
        raise PackageError(f"PACKAGE FAIL: cannot read diag/package/SHA256SUMS ({e.__class__.__name__})") from None
    for ln in text.splitlines():
        m = _SUM.match(ln)
        if not m or m.group(2) in sums:
            raise PackageError(f"PACKAGE FAIL: diag/package/SHA256SUMS: malformed line {ln!r}")
        sums[m.group(2)] = m.group(1)
    if set(sums) != set(STAGE_A):
        raise PackageError("PACKAGE FAIL: diag/package/SHA256SUMS does not list exactly the six stage A files")
    files = {}
    for name in STAGE_A:
        try:
            data = rp.read_bytes(os.path.join(diag_package, name))
        except OSError as e:
            raise PackageError(f"PACKAGE FAIL: cannot read diag/package/{name} ({e.__class__.__name__})") from None
        if rp.sha256_bytes(data) != sums[name]:
            raise PackageError(f"PACKAGE FAIL: diag/package/{name} differs from diag/package/SHA256SUMS")
        files[name] = data
    return files


def build(diag_package=None, package_src=None, source=None, case=None):
    """({package file: bytes}, [(package file, source description, source sha256)]) in ORDER."""
    diag_package = diag_package or DIAG_PACKAGE
    package_src = package_src or PACKAGE_SRC
    commit, spec_sha = contract_source(source)
    spec = spec_at(commit, case)
    if rp.sha256_bytes(spec) != spec_sha:
        raise PackageError(f"PACKAGE FAIL: spec.md at {commit} does not have the recorded sha256 {spec_sha}")
    try:
        constraints = rp.read_bytes(os.path.join(package_src, "constraints.md"))
    except OSError as e:
        raise PackageError(f"PACKAGE FAIL: cannot read package_src/constraints.md ({e.__class__.__name__})") from None
    stage_a = _stage_a_files(diag_package)
    files = {"constraints.md": constraints,
             "contract_excerpt.md": contract_excerpt(spec.decode("utf-8")).encode("utf-8")}
    files.update(stage_a)
    sources = [("constraints.md", "tasks/CASE-01/revise/package_src/constraints.md", rp.sha256_bytes(constraints)),
               ("contract_excerpt.md", f"tasks/CASE-01/spec.md at commit {commit} (sections 1, 2, 3.1)", spec_sha)]
    sources += [(n, f"tasks/CASE-01/diag/package/{n}", rp.sha256_bytes(stage_a[n])) for n in STAGE_A]
    return files, sources


def listing(files, sources):
    """(SHA256SUMS bytes, SOURCES.tsv bytes)."""
    sums = "".join(f"{rp.sha256_bytes(files[n])}  {n}\n" for n in ORDER).encode("ascii")
    src = ("# package file\tsource\tsource sha256\n" +
           "".join(f"{n}\t{s}\t{h}\n" for n, s, h in sources)).encode("utf-8")
    return sums, src


def everything(**kw):
    files, sources = build(**kw)
    sums, src = listing(files, sources)
    return dict(files, **{"SHA256SUMS": sums, "SOURCES.tsv": src})


def main(argv=None, package=None, **kw):
    argv = list(sys.argv[1:] if argv is None else argv)
    package = package or rp.PACKAGE
    if any(a != "--check" for a in argv):
        print("usage: build_package.py [--check]", file=sys.stderr)
        return 2
    try:
        allf = everything(**kw)
    except PackageError as e:
        print(str(e), flush=True)
        return 1
    if "--check" in argv:
        bad = [n for n, data in allf.items()
               if not os.path.isfile(os.path.join(package, n)) or rp.read_bytes(os.path.join(package, n)) != data]
        extra = sorted(set(os.listdir(package)) - set(allf)) if os.path.isdir(package) else []
        bad += extra
        print(f"PACKAGE {'DIFFERS: ' + ', '.join(bad) if bad else 'OK'}", flush=True)
        return 1 if bad else 0
    differ = [n for n, data in allf.items()
              if os.path.exists(os.path.join(package, n)) and rp.read_bytes(os.path.join(package, n)) != data]
    if differ:
        print(f"PACKAGE FAIL: existing file(s) differ and are not rewritten: {', '.join(differ)}", flush=True)
        return 1
    for n, data in allf.items():
        rp.write_new_or_same(os.path.join(package, n), data)
    print(f"PACKAGE OK: {len(ORDER)} files -> {os.path.relpath(package, rp.CASE)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
