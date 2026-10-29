"""Build the materials package given to every model (protocol v0.3 section 6.2). Copied and adapted from
tasks/CASE-01/diag/scripts/build_package.py (rules/copied_from.tsv).
  python3 -B scripts/build_package.py [--check] [--selftest]
Writes package/{intent.md, values.txt, summary_R1.tsv, summary_R2.tsv, path_R1.rpt, path_R2.rpt, dot4sat.v, context.md},
SHA256SUMS and SOURCES.tsv (neutral: "formal run R<k>" + sha256; the full mapping to the version directories goes to
the sealed sources_full.tsv and is committed only after unblinding). context.md is a byte copy of the tier-1 frozen
package_src/context.md (refused when they differ). The R1/R2 -> version assignment comes from contexts.resolve.
An existing package must be byte-identical (never rewritten); --check only compares and exits 1 on any difference."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2paths import CASE, CASE01, PACKAGE, PACKAGE_SRC, QUERIES, read_bytes, sha256_bytes, write_new_or_same  # noqa: E402
import contexts  # noqa: E402

ORDER = ("intent.md", "values.txt", "summary_R1.tsv", "summary_R2.tsv", "path_R1.rpt", "path_R2.rpt", "dot4sat.v", "context.md")
RTL_SHA = "422ba000b48903558d797510cd4d0189b3fac9f83ba4ce4a1b22eb497194c802"
F1_CFG_SHA = "652c1f1f25be0e0996b841ba371fef5bb667d1609eb92c8e4691c9df4a63bf89"
PATH_REPORT = "cat_ss_n40C_1v60_in2reg_max.rpt"


def summary(tsv_text):
    rows = [l for l in tsv_text.splitlines() if l.split("\t", 1)[0] in ("WS", "CAT", "TOPO")]
    return "\n".join(rows) + "\n"


def values(cfg_text):
    kv = {}
    for raw in cfg_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if "=" in line:
            k, v = (s.strip() for s in line.split("=", 1))
            kv[k] = v
    return f"T_ns = {kv['T_ns']}\nC_load_pF = {kv['C_load_pF']}\n"


def intent_text():
    return read_bytes(os.path.join(CASE, "intent.md")).decode("utf-8")


def check_frozen_context(frozen, built):
    if frozen != built:
        raise SystemExit("CASE02 FAIL: package context.md differs from the tier-1 frozen package_src/context.md")


def build(assign, formal_root=None, frozen_context=None):
    """({package file: bytes}, [(package file, neutral source description, source sha256)])."""
    root = formal_root or os.path.join(QUERIES, "formal")
    rtl = read_bytes(os.path.join(CASE01, "rtl", "dot4sat.v"))
    cfg = read_bytes(os.path.join(CASE01, "config", "f1.cfg"))
    if sha256_bytes(rtl) != RTL_SHA or sha256_bytes(cfg) != F1_CFG_SHA:
        raise SystemExit("CASE02 FAIL: rtl/dot4sat.v or config/f1.cfg is not the frozen source")
    frozen = frozen_context if frozen_context is not None else read_bytes(os.path.join(PACKAGE_SRC, "context.md"))
    intent = intent_text().encode("utf-8")
    files = {"intent.md": intent, "values.txt": values(cfg.decode("utf-8")).encode("utf-8")}
    sources = [("intent.md", "intent.md", sha256_bytes(intent)),
               ("values.txt", "tasks/CASE-01/config/f1.cfg (T_ns, C_load_pF)", sha256_bytes(cfg))]
    for ctx in ("R1", "R2"):
        vdir = os.path.join(root, assign[ctx])
        tsv = read_bytes(os.path.join(vdir, "sta_results.tsv"))
        rpt = read_bytes(os.path.join(vdir, PATH_REPORT))
        files[f"summary_{ctx}.tsv"] = summary(tsv.decode("utf-8")).encode("utf-8")
        files[f"path_{ctx}.rpt"] = rpt
        sources.append((f"summary_{ctx}.tsv", f"正式运行 {ctx} 的 sta_results.tsv（WS/CAT/TOPO 行）", sha256_bytes(tsv)))
        sources.append((f"path_{ctx}.rpt", f"正式运行 {ctx} 的 {PATH_REPORT}", sha256_bytes(rpt)))
    files["dot4sat.v"] = rtl
    files["context.md"] = frozen
    sources.append(("dot4sat.v", "tasks/CASE-01/rtl/dot4sat.v", sha256_bytes(rtl)))
    sources.append(("context.md", "package_src/context.md (tier-1 frozen)", sha256_bytes(frozen)))
    return {n: files[n] for n in ORDER}, sources


def sources_full(assign, formal_root=None):
    root = formal_root or os.path.join(QUERIES, "formal")
    lines = ["# package file\tcontext\tversion\tsource path\tsource sha256"]
    for ctx in ("R1", "R2"):
        v = assign[ctx]
        for name, src in ((f"summary_{ctx}.tsv", "sta_results.tsv"), (f"path_{ctx}.rpt", PATH_REPORT)):
            p = os.path.join(root, v, src)
            lines.append(f"{name}\t{ctx}\t{v}\t{os.path.relpath(p, CASE).replace(os.sep, '/')}\t{sha256_bytes(read_bytes(p))}")
    return "\n".join(lines) + "\n"


def listing(files, sources):
    sums = "".join(f"{sha256_bytes(files[n])}  {n}\n" for n in ORDER).encode()
    src = ("# package file\tsource\tsource sha256\n" + "".join(f"{n}\t{s}\t{h}\n" for n, s, h in sources)).encode("utf-8")
    return sums, src


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    selftest = "--selftest" in argv
    assign = {ctx: contexts.resolve(ctx, selftest=selftest) for ctx in ("R1", "R2")}
    root = os.path.join(QUERIES, "selftest" if selftest else "formal")
    files, sources = build(assign, formal_root=root)
    check_frozen_context(read_bytes(os.path.join(PACKAGE_SRC, "context.md")), files["context.md"])
    sums, src = listing(files, sources)
    everything = dict(files, **{"SHA256SUMS": sums, "SOURCES.tsv": src})
    if "--check" in argv:
        bad = [n for n, data in everything.items()
               if not os.path.exists(os.path.join(PACKAGE, n)) or read_bytes(os.path.join(PACKAGE, n)) != data]
        print(f"PACKAGE {'DIFFERS: ' + ', '.join(bad) if bad else 'OK'}")
        return 1 if bad else 0
    if selftest:
        print("PACKAGE (selftest, not written): " + ", ".join(f"{n} {len(d)}B" for n, d in files.items()))
        return 0
    for n, data in everything.items():
        write_new_or_same(os.path.join(PACKAGE, n), data)
    sealed = os.path.join(contexts.sealed_dir(), "sources_full.tsv")
    os.makedirs(os.path.dirname(sealed), exist_ok=True)
    write_new_or_same(sealed, sources_full(assign).encode("utf-8"))
    print(f"PACKAGE OK: {len(files)} files -> {os.path.relpath(PACKAGE, CASE)}; full source map sealed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
