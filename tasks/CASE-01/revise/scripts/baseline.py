"""The F1 baseline of the CASE-01 stage B comparisons (implementation plan Task 1).

The baseline is always read from the F1 archive originals evidence/F1/archive/20261009-092827-base-T27.91/:
verdict.json, sta/sta_results.tsv and the 12 reports sta/path_{max,min}_<corner>.rpt. verify() checks each of them
against its "./20261009-092827-base-T27.91/..." entry in evidence/F1/archive/SHA256SUMS, and checks that the copies
evidence/F1/f1_run_verdict.json and evidence/F1/sta_results.tsv are byte-identical to the archive verdict.json and
sta/sta_results.tsv. Everything is read only. Python standard library only; Windows and WSL."""
import os

import revpaths as rp

EVIDENCE_F1 = os.path.join(rp.CASE, "evidence", "F1")
RUN = "20261009-092827-base-T27.91"
CORNERS = ("ff_100C_1v95", "ff_n40C_1v95", "ss_100C_1v60", "ss_n40C_1v60", "tt_025C_1v80", "tt_100C_1v80")


def source(root=None):
    """Paths of the baseline originals (and of the two copies), below root (default evidence/F1)."""
    root = root or EVIDENCE_F1
    arch = os.path.join(root, "archive", RUN)
    return {"archive": arch,
            "sums": os.path.join(root, "archive", "SHA256SUMS"),
            "verdict": os.path.join(arch, "verdict.json"),
            "sta_results": os.path.join(arch, "sta", "sta_results.tsv"),
            "path_reports": {kind: {c: os.path.join(arch, "sta", f"path_{kind}_{c}.rpt") for c in CORNERS}
                             for kind in ("max", "min")},
            "copy_verdict": os.path.join(root, "f1_run_verdict.json"),
            "copy_sta_results": os.path.join(root, "sta_results.tsv")}


def verify(root=None):
    """List of problems; empty means every original matches SHA256SUMS and both copies equal their originals."""
    src = source(root)
    probs = []
    originals = {"verdict.json": src["verdict"], "sta/sta_results.tsv": src["sta_results"]}
    for kind in ("max", "min"):
        for c, p in src["path_reports"][kind].items():
            originals[f"sta/path_{kind}_{c}.rpt"] = p
    try:
        lines = rp.read_bytes(src["sums"]).decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        return [f"BASELINE FAIL: {src['sums']} cannot be read ({e.__class__.__name__})"]
    entries = {}
    for ln in lines:
        parts = ln.split(None, 1)
        if len(parts) == 2 and parts[1].startswith(f"./{RUN}/"):
            entries.setdefault(parts[1][len(f"./{RUN}/"):], []).append(parts[0].lower())
    for rel, path in originals.items():
        want = entries.get(rel, [])
        if len(want) != 1:
            probs.append(f"BASELINE FAIL: SHA256SUMS has {len(want)} entries for ./{RUN}/{rel} (expected 1)")
            continue
        try:
            got = rp.sha256(path)
        except OSError as e:
            probs.append(f"BASELINE FAIL: archive {RUN}/{rel} cannot be read ({e.__class__.__name__})")
            continue
        if got != want[0]:
            probs.append(f"BASELINE FAIL: archive {RUN}/{rel}: sha256 {got} != SHA256SUMS {want[0]}")
    for copy_key, orig_key, name in (("copy_verdict", "verdict", "f1_run_verdict.json"),
                                     ("copy_sta_results", "sta_results", "sta_results.tsv")):
        try:
            same = rp.read_bytes(src[copy_key]) == rp.read_bytes(src[orig_key])
        except OSError as e:
            probs.append(f"BASELINE FAIL: copy evidence/F1/{name} or its original cannot be read "
                         f"({e.__class__.__name__})")
            continue
        if not same:
            probs.append(f"BASELINE FAIL: copy evidence/F1/{name} differs from the archive original")
    return probs
