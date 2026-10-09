"""Coverage of spec 3.4, computed from the raw timeline: only transactions that are actually compared count,
and every required scenario is counted separately (P1 M4).
"""

from model import OUT_MAX, OUT_MIN, decode16, full_sum
from timeline import classify

V5 = (-32768, -1, 0, 1, 32767)
BUBBLE_PATTERNS = ("10101010", "11001100", "11101110")
MIN_BURST = 32
FAR = 1 << 30            # "far beyond" a bound: raw sum exceeds it by at least 2^30
BOOKKEEPING = ("generated_valid", "accepted", "cancelled", "checked", "undelivered")


def _por_end(rst):
    """First edge after the initial (power-on) reset run."""
    n = 0
    while n < len(rst) and rst[n]:
        n += 1
    return n


def _pulses(rst):
    """Reset pulses after the power-on reset run: list of (start, length)."""
    out, n = [], _por_end(rst)
    while n < len(rst):
        if rst[n]:
            start = n
            while n < len(rst) and rst[n]:
                n += 1
            out.append((start, n - start))
        else:
            n += 1
    return out


def compute(cycles, L, drain):
    """cycles: list of (rst, valid, a_bits, b_bits, tag). Returns the coverage dict stored in the manifest."""
    rst = [c[0] for c in cycles] + [0] * drain
    valid = [c[1] for c in cycles] + [0] * drain
    tags = [c[4] for c in cycles] + ["drain"] * drain
    kinds = classify(rst, valid, L)
    delivered = [n for n, k in enumerate(kinds) if k == "delivered"]
    accepted = {n for n, k in enumerate(kinds) if k in ("cancelled", "delivered", "undelivered")}
    sums = {n: full_sum(cycles[n][2], cycles[n][3]) for n in delivered}

    sign_bins = set()
    cancel = 0
    for n in delivered:
        a = [decode16(x) for x in cycles[n][2]]
        b = [decode16(x) for x in cycles[n][3]]
        for lane in range(4):
            if a[lane] in V5 and b[lane] in V5:
                sign_bins.add((lane, a[lane], b[lane]))
        prods = [x * y for x, y in zip(a, b)]
        if any(p > 0 for p in prods) and any(p < 0 for p in prods) and abs(sums[n]) <= 1:
            cancel += 1

    cancel_at = {m: 0 for m in range(1, L)}           # first reset edge R_(n+m) that cancels accepted n
    for n, k in enumerate(kinds):
        if k == "cancelled":
            m = next(j for j in range(n + 1, n + L) if rst[j]) - n
            cancel_at[m] += 1

    mask = "".join("1" if k == "delivered" else "0" for k in kinds)
    run = best = 0
    for ch in mask:
        run = run + 1 if ch == "1" else 0
        best = max(best, run)

    def in_traffic(s, ln):   # accepted transaction within L edges before the pulse, delivery right after it
        before = any(j in accepted for j in range(max(0, s - L), s))
        after = s + ln < len(kinds) and kinds[s + ln] == "delivered"
        return before and after

    pulses = _pulses(rst)
    por_end = _por_end(rst)
    counts = {
        "generated_valid": sum(valid[: len(cycles)]),
        "accepted": len(accepted),
        "cancelled": kinds.count("cancelled"),
        "checked": len(delivered),
        "undelivered": kinds.count("undelivered"),
        "sign_bins": len(sign_bins),
        "sat_hi_exact": sum(1 for n in delivered if sums[n] == OUT_MAX),
        "sat_hi_over1": sum(1 for n in delivered if sums[n] == OUT_MAX + 1),
        "sat_lo_exact": sum(1 for n in delivered if sums[n] == OUT_MIN),
        "sat_lo_over1": sum(1 for n in delivered if sums[n] == OUT_MIN - 1),
        "sat_pos": sum(1 for n in delivered if sums[n] > OUT_MAX),
        "sat_neg": sum(1 for n in delivered if sums[n] < OUT_MIN),
        "sat_pos_far": sum(1 for n in delivered if sums[n] - OUT_MAX >= FAR),
        "sat_neg_far": sum(1 for n in delivered if OUT_MIN - sums[n] >= FAR),
        "cancel": cancel,
        "burst_max_run": best,
        "bubble_patterns": sum(1 for p in BUBBLE_PATTERNS if p in mask),
        "bubble_rand_gaps": sum(1 for n in delivered if tags[n] == "bubble_rand" and n > 0 and not valid[n - 1]),
        "rst_block": sum(1 for n in range(por_end, len(rst)) if kinds[n] == "blocked"),
        "rst_after_delivery": sum(1 for n in delivered if n + L < len(rst) and rst[n + L]),
        "rst_single_in_traffic": sum(1 for s, ln in pulses if ln == 1 and in_traffic(s, ln)),
        "rst_multi_in_traffic": sum(1 for s, ln in pulses if ln >= 2 and in_traffic(s, ln)),
        "rand_uniform_checked": sum(1 for n in delivered if tags[n] == "rand_uniform"),
        "rand_extreme_checked": sum(1 for n in delivered if tags[n] == "rand_extreme"),
    }
    for m, c in cancel_at.items():
        counts[f"rst_cancel_m{m}"] = c
    required = {k: 1 for k in counts if k not in BOOKKEEPING}
    required.update({"sign_bins": 100, "burst_max_run": MIN_BURST, "bubble_patterns": len(BUBBLE_PATTERNS)})
    not_applicable = {}
    if L == 1:
        not_applicable["rst_cancel"] = ("L=1: an accepted transaction is delivered before the next edge, "
                                        "so no edge R_(n+m), m = 1..L-1, exists to cancel it")
    failures = [f"{k}={counts[k]} < {v}" for k, v in required.items() if counts[k] < v]
    if counts["undelivered"]:
        failures.append(f"undelivered={counts['undelivered']} (drain too short)")
    if L == 1 and counts["cancelled"] != 0:
        failures.append("cancelled must be 0 when L=1")
    return {"counts": counts, "required": required, "not_applicable": not_applicable,
            "definitions": {"far": f"raw sum beyond the bound by >= 2^30 ({FAR})",
                            "in_traffic": "an accepted transaction within L edges before the pulse and a "
                                          "delivered transaction on the first edge after it",
                            "power_on_reset": "the initial run of rst=1 is excluded from pulse counts"},
            "failures": failures, "ok": not failures}
