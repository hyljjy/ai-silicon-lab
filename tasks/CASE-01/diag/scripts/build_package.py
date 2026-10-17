"""Build the materials package given to every model (protocol v0.5 section 5.2).

  python3 -B diag/scripts/build_package.py [--check]

Writes diag/package/{context.md, path_report.rpt, case01_sdc.tcl, values.txt, slack_summary.tsv, dot4sat.v},
SHA256SUMS (package files) and SOURCES.tsv (source path and sha256 of every input). Everything comes from committed,
frozen files whose sha256 is pinned in PINNED (the SDC also against config/f1.sha256), so the build is deterministic.
An existing package must be byte-identical (it is never rewritten); --check only compares and exits 1 on any
difference.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagpaths import CASE, PACKAGE, PACKAGE_SRC, read_bytes, sha256_bytes, write_new_or_same  # noqa: E402

REPORT = "evidence/F1/f1_run_cat_ss_n40C_1v60_in2reg_max.rpt"
RTL = "rtl/dot4sat.v"
SDC = "sdc/case01_sdc.tcl"
RESULTS = "evidence/F1/sta_results.tsv"      # same bytes as runs/20261009-092827-base-T27.91/sta/sta_results.tsv
F1_CFG = "config/f1.cfg"
SPEC = "spec.md"
PINNED = {                                   # every source is checked before anything is built
    REPORT: "043e50bf6638284a043aec4cdf9a23ea999878a369ac58cfef7b613420f38d88",
    RTL: "422ba000b48903558d797510cd4d0189b3fac9f83ba4ce4a1b22eb497194c802",
    SDC: "b8d1aab60d137dc39dc7cb55b2ec314b952538dfee8f5be627a140dcca09300c",
    RESULTS: "14f4def3616882bd2149d38e3b7e1ebac2145438fffbe08b578f1b857aabd7ca",
    F1_CFG: "652c1f1f25be0e0996b841ba371fef5bb667d1609eb92c8e4691c9df4a63bf89",
    SPEC: "7ab53c49982cc7a76017060931f8b3a6a5a3b760a767b024fbccabe696b414a1",
}
ORDER = ("context.md", "path_report.rpt", "case01_sdc.tcl", "values.txt", "slack_summary.tsv", "dot4sat.v")
SPEC_COMMIT = "aff0e2698bf951b7af6f96e6ea3cf42474c0c69a"   # the commit whose spec.md has the PINNED hash (v1.2)


def text(rel):
    return read_bytes(os.path.join(CASE, rel)).decode("utf-8")


def spec_bytes():
    """spec.md as pinned. The contract keeps its revision record in spec.md itself, so a later revision (v1.3,
    PRJ-004: only the status line and the version record) changes the live file; the package is still built from
    the pinned version, read from git, and its hash is checked like every other source."""
    live = read_bytes(os.path.join(CASE, SPEC))
    if sha256_bytes(live) == PINNED[SPEC]:
        return live
    return subprocess.run(["git", "-C", CASE, "show", f"{SPEC_COMMIT}:./{SPEC}"], capture_output=True,
                          check=True).stdout


def spec_section_1(spec):
    """Spec section 1 verbatim: from the '## 1. ' heading up to (not including) the '## 2. ' heading."""
    lines = spec.splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines) if l.startswith("## 1. "))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## 2. "))
    return "".join(lines[start:end]).rstrip("\n") + "\n"


def values(cfg):
    kv = {}
    for raw in cfg.splitlines():
        line = raw.split("#", 1)[0].strip()
        if "=" in line:
            k, v = (s.strip() for s in line.split("=", 1))
            kv[k] = v
    return f"T_ns = {kv['T_ns']}\nC_load_pF = {kv['C_load_pF']}\n"


def slack_summary(results, notes):
    rows = [l for l in results.splitlines() if l.split("\t", 1)[0] in ("WS", "CAT", "TOPO")]
    return notes.rstrip("\n") + "\n" + "\n".join(rows) + "\n"


def build():
    """Return ({package file: bytes}, [(package file, source description, source sha256)])."""
    for rel, want in PINNED.items():
        data = spec_bytes() if rel == SPEC else read_bytes(os.path.join(CASE, rel))
        if sha256_bytes(data) != want:
            raise SystemExit(f"DIAG FAIL: {rel} is not the frozen source ({want[:16]}…)")
    spec = spec_bytes()
    frozen = dict(reversed(l.split()) for l in text("config/f1.sha256").splitlines() if l.strip())
    if frozen.get(SDC) != PINNED[SDC]:
        raise SystemExit(f"DIAG FAIL: {SDC} hash differs from config/f1.sha256")
    report, rtl = read_bytes(os.path.join(CASE, REPORT)), read_bytes(os.path.join(CASE, RTL))
    extra = read_bytes(os.path.join(PACKAGE_SRC, "context_extra.md")).decode("utf-8")
    notes = read_bytes(os.path.join(PACKAGE_SRC, "slack_notes.txt")).decode("utf-8")
    files = {
        "context.md": (spec_section_1(spec.decode("utf-8")) + extra).encode("utf-8"),
        "path_report.rpt": report,
        "case01_sdc.tcl": read_bytes(os.path.join(CASE, SDC)),
        "values.txt": values(text(F1_CFG)).encode("utf-8"),
        "slack_summary.tsv": slack_summary(text(RESULTS), notes).encode("utf-8"),
        "dot4sat.v": rtl,
    }
    sources = [("context.md", SPEC + " (section 1)", sha256_bytes(spec)),
               ("context.md", "diag/package_src/context_extra.md", sha256_bytes(extra.encode("utf-8"))),
               ("path_report.rpt", REPORT, sha256_bytes(report)),
               ("case01_sdc.tcl", SDC, sha256_bytes(files["case01_sdc.tcl"])),
               ("values.txt", F1_CFG + " (T_ns, C_load_pF)", sha256_bytes(read_bytes(os.path.join(CASE, F1_CFG)))),
               ("slack_summary.tsv", RESULTS + " (WS/CAT/TOPO rows; = F1 run sta/sta_results.tsv)",
                sha256_bytes(read_bytes(os.path.join(CASE, RESULTS)))),
               ("slack_summary.tsv", "diag/package_src/slack_notes.txt", sha256_bytes(notes.encode("utf-8"))),
               ("dot4sat.v", RTL, sha256_bytes(rtl))]
    return files, sources


def listing(files, sources):
    sums = "".join(f"{sha256_bytes(files[n])}  {n}\n" for n in ORDER).encode()
    src = ("# package file\tsource\tsource sha256\n" +
           "".join(f"{n}\t{s}\t{h}\n" for n, s, h in sources)).encode("utf-8")
    return sums, src


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    files, sources = build()
    sums, src = listing(files, sources)
    everything = dict(files, **{"SHA256SUMS": sums, "SOURCES.tsv": src})
    if "--check" in argv:
        bad = [n for n, data in everything.items()
               if not os.path.exists(os.path.join(PACKAGE, n)) or read_bytes(os.path.join(PACKAGE, n)) != data]
        print(f"PACKAGE {'DIFFERS: ' + ', '.join(bad) if bad else 'OK'}")
        return 1 if bad else 0
    for n, data in everything.items():
        write_new_or_same(os.path.join(PACKAGE, n), data)
    print(f"PACKAGE OK: {len(files)} files -> {os.path.relpath(PACKAGE, CASE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
