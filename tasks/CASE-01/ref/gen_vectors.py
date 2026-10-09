"""Generate CASE-01 vectors and manifest (spec 3.2-3.4).

Usage: python3 ref/gen_vectors.py --L 1 --lmax 3 --seed 1 --out <dir>
Writes <dir>/vectors.txt (one line per rising edge) and <dir>/manifest.json; exits 1 if coverage fails.
Line format: rst valid a0 a1 a2 a3 b0 b1 b2 b3 y tag   (a/b: 4 hex digits, y: 8 hex digits)
"""
import argparse
import hashlib
import json
import os
import random
import sys

import coverage
from model import ref

BOUNDARY = [  # spec 3.3 item 2: (a lanes 0..3, b lanes 0..3, tag)
    ((-32768, -32768, -1, 0), (-32768, -32768, 1, 0), "sat_hi_exact"),
    ((-32768, -32768, 0, 0), (-32768, -32768, 0, 0), "sat_hi_over1"),
    ((-32768, -32768, -32768, 0), (32767, 32767, 2, 0), "sat_lo_exact"),
    ((-32768, -32768, -32768, -1), (32767, 32767, 2, 1), "sat_lo_over1"),
]
ZERO4 = (0, 0, 0, 0)
EXTREMES = (-32768, -32767, -2, -1, 0, 1, 2, 32766, 32767)
POR_EDGES = 4        # power-on reset length (spec 2.4: at least 4 rising edges)
SCENARIO_PARAMS = {  # recorded in the manifest (P1 M4); must match build() below
    "por_edges": POR_EDGES, "sign_values": list(coverage.V5), "cancel_pairs": 64, "burst": 64,
    "bubble_fixed": {"patterns": list(coverage.BUBBLE_PATTERNS), "repeats": 4},
    "bubble_rand": {"edges": 64, "p_valid": 0.5},
    "resets": {"single_with_valid": 1, "multi_edges": 3, "cancel_positions": "m = 1..L-1", "after_delivery": "m = L"},
    "rand_uniform": {"edges": 2000, "p_valid": 0.85, "p_rst": 0.01},
    "rand_extreme": {"edges": 1000, "p_valid": 0.85, "p_pick_extreme": 0.7, "extremes": list(EXTREMES)},
}


def build(L, seed):
    """Return the vector list: (rst, valid, a_bits[4], b_bits[4], tag) per rising edge."""
    rng = random.Random(seed)
    cyc = []

    def add(rst, valid, a, b, tag):
        cyc.append((int(rst), int(valid), tuple(v & 0xFFFF for v in a), tuple(v & 0xFFFF for v in b), tag))

    def r16():
        return rng.randint(-32768, 32767)

    def r4():
        return tuple(r16() for _ in range(4))

    def stream(count, tag):
        for _ in range(count):
            add(0, 1, r4(), r4(), tag)

    def pick():
        return rng.choice(EXTREMES) if rng.random() < 0.7 else r16()

    for _ in range(POR_EDGES):                               # power-on reset (spec 2.4)
        add(1, 0, ZERO4, ZERO4, "por")
    for lane in range(4):                                    # sign boundaries
        for av in coverage.V5:
            for bv in coverage.V5:
                a, b = list(r4()), list(r4())
                a[lane], b[lane] = av, bv
                add(0, 1, a, b, f"sign_l{lane}")
    for a, b, tag in BOUNDARY:                               # exact saturation boundaries
        add(0, 1, a, b, tag)
    add(0, 1, (-32768,) * 4, (-32768,) * 4, "sat_hi_far")
    add(0, 1, (-32768,) * 4, (32767,) * 4, "sat_lo_far")
    for i in range(64):                                      # cancellation
        x, y = r16(), r16()
        u, w = rng.randint(-32767, 32767), rng.randint(-32767, 32767)
        if i % 2 == 0:
            add(0, 1, (x, x, y, y), (u, -u, w, -w), "cancel")
        else:
            add(0, 1, (x, x, 1, 0), (u, -u, rng.choice((1, -1)), 0), "cancel")
    stream(64, "burst")                                      # consecutive valid
    for pattern in coverage.BUBBLE_PATTERNS:                 # fixed bubble patterns, 4 repeats each
        for ch in pattern * 4:
            add(0, ch == "1", r4(), r4(), "bubble_fixed")
    for _ in range(64):
        add(0, rng.random() < 0.5, r4(), r4(), "bubble_rand")
    # resets inside traffic (spec 3.3 item 6), for the actual L
    stream(4, "rst_pre")
    add(1, 1, r4(), r4(), "rst_single_block")
    stream(4, "rst_recover")
    stream(4, "rst_pre")
    for _ in range(3):
        add(1, 1, r4(), r4(), "rst_multi")
    stream(4, "rst_recover")
    for m in range(1, L):                                    # cancel at R_(n+m), m = 1..L-1
        stream(4, "rst_pre")
        add(0, 1, r4(), r4(), f"rst_cancel_target_m{m}")
        stream(m - 1, "rst_pre")
        add(1, 0, ZERO4, ZERO4, f"rst_cancel_m{m}")
        stream(4, "rst_recover")
    stream(4, "rst_pre")                                     # reset exactly at R_(n+L)
    add(0, 1, r4(), r4(), "rst_after_target")
    stream(L - 1, "rst_pre")
    add(1, 0, ZERO4, ZERO4, "rst_after_delivery")
    stream(4, "rst_recover")
    for _ in range(2000):                                    # random, with rare resets
        add(rng.random() < 0.01, rng.random() < 0.85, r4(), r4(), "rand_uniform")
    for _ in range(1000):
        add(0, rng.random() < 0.85, [pick() for _ in range(4)], [pick() for _ in range(4)], "rand_extreme")
    return cyc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, required=True)
    ap.add_argument("--lmax", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if not 1 <= args.lmax <= 3 or not 1 <= args.L <= args.lmax:
        print(f"FAIL: need 1 <= L <= lmax <= 3, got L={args.L} lmax={args.lmax}")
        return 1
    drain = args.lmax + 1
    cyc = build(args.L, args.seed)
    lines = []
    for rst, valid, a, b, tag in cyc:
        fields = [str(rst), str(valid)] + [f"{x:04x}" for x in a] + [f"{x:04x}" for x in b]
        lines.append(" ".join(fields + [f"{ref(list(a), list(b)):08x}", tag]))
    text = "\n".join(lines) + "\n"
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "vectors.txt"), "w", newline="\n") as f:
        f.write(text)
    cov = coverage.compute(cyc, args.L, drain)
    generated = {}
    for _rst, valid, _a, _b, tag in cyc:
        g = generated.setdefault(tag, {"edges": 0, "valid": 0})
        g["edges"] += 1
        g["valid"] += valid
    manifest = {"seed": args.seed, "L": args.L, "lmax": args.lmax, "drain": drain,
                "n_vectors": len(cyc), "expected_checked": cov["counts"]["checked"],
                "vectors_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "scenario_params": SCENARIO_PARAMS, "generated_by_tag": generated, "coverage": cov}
    with open(os.path.join(args.out, "manifest.json"), "w", newline="\n") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    if not cov["ok"]:
        print("FAIL: coverage: " + "; ".join(cov["failures"]))
        return 1
    print(f"OK: {len(cyc)} vectors, expected_checked={cov['counts']['checked']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
