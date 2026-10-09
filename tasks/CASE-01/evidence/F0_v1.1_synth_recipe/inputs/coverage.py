"""Coverage of spec 3.4, computed from the raw timeline (only transactions that are actually compared count)."""

from model import OUT_MAX, OUT_MIN, decode16, full_sum
from timeline import classify

V5 = (-32768, -1, 0, 1, 32767)
BUBBLE_PATTERNS = ("10101010", "11001100", "11101110")
MIN_BURST = 32
POR_EDGES = 4
BOOKKEEPING = ("generated_valid", "accepted", "cancelled", "checked", "undelivered")


def _pulses(rst):
    """Reset pulses after power-on reset: list of (start, length)."""
    out, n = [], POR_EDGES
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
    kinds = classify(rst, valid, L)
    delivered = [n for n, k in enumerate(kinds) if k == "delivered"]
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

    mask = "".join("1" if k == "delivered" else "0" for k in kinds)
    run = best = 0
    for ch in mask:
        run = run + 1 if ch == "1" else 0
        best = max(best, run)
    pulses = _pulses(rst)
    counts = {
        "generated_valid": sum(valid[: len(cycles)]),
        "accepted": sum(1 for k in kinds if k in ("cancelled", "delivered", "undelivered")),
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
        "cancel": cancel,
        "burst_max_run": best,
        "bubble_patterns": sum(1 for p in BUBBLE_PATTERNS if p in mask),
        "rst_block": sum(1 for n in range(POR_EDGES, len(rst)) if kinds[n] == "blocked"),
        "rst_cancel": kinds.count("cancelled"),
        "rst_after_delivery": sum(1 for n in delivered if n + L < len(rst) and rst[n + L]),
        "rst_single_pulse": sum(1 for _, ln in pulses if ln == 1),
        "rst_multi_pulse": sum(1 for _, ln in pulses if ln >= 2),
        "rst_recover": sum(1 for s, ln in pulses if s + ln < len(kinds) and kinds[s + ln] == "delivered"),
        "rand_checked": sum(1 for n in delivered if cycles[n][4].startswith("rand_")),
    }
    required = {k: 1 for k in counts if k not in BOOKKEEPING}
    required.update({"sign_bins": 100, "burst_max_run": MIN_BURST, "bubble_patterns": len(BUBBLE_PATTERNS)})
    not_applicable = {}
    if L == 1:
        del required["rst_cancel"]
        not_applicable["rst_cancel"] = ("L=1: an accepted transaction is delivered before the next edge, "
                                        "so no edge can cancel it")
    failures = [f"{k}={counts[k]} < {v}" for k, v in required.items() if counts[k] < v]
    if counts["undelivered"]:
        failures.append(f"undelivered={counts['undelivered']} (drain too short)")
    if L == 1 and counts["rst_cancel"] != 0:
        failures.append("rst_cancel must be 0 when L=1")
    return {"counts": counts, "required": required, "not_applicable": not_applicable,
            "failures": failures, "ok": not failures}
