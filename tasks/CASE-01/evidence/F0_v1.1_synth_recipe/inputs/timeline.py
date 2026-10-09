"""Valid/reset timeline of spec 2.3, written independently of the TB.

Index n = rising edge R_n. Observation O_k is read on F_(k-1), k = 1..len(rst).
"""


def expected_valid(rst, valid, L, k):
    """O_k.valid = valid[k-L] AND rst[j] == 0 for every j in [k-L, k-1]."""
    n = k - L
    if n < 0:
        return False
    return bool(valid[n]) and not any(rst[j] for j in range(n, k))


def classify(rst, valid, L):
    """Per input edge n: idle | blocked | cancelled | delivered | undelivered."""
    total = len(rst)
    kinds = []
    for n in range(total):
        if not valid[n]:
            kinds.append("idle")
        elif rst[n]:
            kinds.append("blocked")
        elif any(rst[j] for j in range(n + 1, min(n + L, total))):
            kinds.append("cancelled")
        elif n + L <= total:
            kinds.append("delivered")
        else:
            kinds.append("undelivered")
    return kinds
