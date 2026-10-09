"""CASE-01 reference function f(a, b) (spec 3.1). Independent of the RTL: arbitrary-precision integers."""

OUT_MIN = -(1 << 31)
OUT_MAX = (1 << 31) - 1
LANES = 4


def decode16(bits):
    """16-bit two's-complement pattern -> int in [-32768, 32767]."""
    if not isinstance(bits, int) or not 0 <= bits <= 0xFFFF:
        raise ValueError(f"not a 16-bit pattern: {bits!r}")
    return bits - 0x10000 if bits & 0x8000 else bits


def full_sum(a_bits, b_bits):
    """Exact sum of the four signed products (no truncation, no early saturation)."""
    if len(a_bits) != LANES or len(b_bits) != LANES:
        raise ValueError("need exactly 4 lanes")
    return sum(decode16(a) * decode16(b) for a, b in zip(a_bits, b_bits))


def ref(a_bits, b_bits):
    """Clamp the exact sum to the 32-bit signed range; return the 32-bit two's-complement pattern."""
    s = full_sum(a_bits, b_bits)
    return min(max(s, OUT_MIN), OUT_MAX) & 0xFFFFFFFF
