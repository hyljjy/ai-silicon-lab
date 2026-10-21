"""Shared paths, hashes and small checks for the CASE-01 stage B (revise) scripts (protocol v0.4).
Python standard library only; works on Windows (python 3.13) and in WSL (python3 3.12.3)."""
import datetime
import hashlib
import json
import os
import re
import shutil
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
REVISE = os.path.dirname(HERE)                       # tasks/CASE-01/revise
CASE = os.path.dirname(REVISE)                       # tasks/CASE-01
REPO = os.path.dirname(os.path.dirname(CASE))        # repository root
RULES = os.path.join(REVISE, "rules")
PROMPTS = os.path.join(REVISE, "prompts")
PACKAGE = os.path.join(REVISE, "package")
OUTPUTS = os.path.join(REVISE, "outputs")
RESULTS = os.path.join(REVISE, "results")
PREDICTIONS = os.path.join(REVISE, "predictions")
DIAG_SCRIPTS = os.path.join(CASE, "diag", "scripts")
SANDBOX = r"D:\study\revise_sandbox" if os.name == "nt" else "/mnt/d/study/revise_sandbox"

REUSED_SHA256 = os.path.join(RULES, "reused.sha256")
METRIC_DIRECTIONS = os.path.join(RULES, "metric_directions.json")

GB = 1024 ** 3                                       # disk threshold unit: GiB (the conservative reading of "GB")
WSL_DISTRO = "Ubuntu-24.04"
# the two volumes of the disk check (Global Constraints "磁盘"): WSL root file system and the repository volume
DISK_VOLUMES = ("WSL /", "D:\\") if os.name == "nt" else ("/", "/mnt/d")


_SUM_LINE = re.compile(r"^([0-9a-fA-F]{64}) [ *](\S.*)$")


class RevpathsError(Exception):
    pass


class MeasureKillFail(OSError):
    """A disk measurement whose process cleanup failed (killed_pids_alive non-empty or cleanup_unconfirmed, also
    after a SupervisionError): disk_problems reports it as a KILL_FAIL problem, and the caller writes a stop."""

    def __init__(self, message, alive=(), unconfirmed=False):
        super().__init__(message)
        self.alive = list(alive)
        self.unconfirmed = bool(unconfirmed)


KILL_FAIL = "KILL FAIL"                               # prefix of a disk_problems entry whose measurement left processes


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def load_json_decimal(path):
    """JSON with every non-integer number as decimal.Decimal (all digits kept); integers stay int."""
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"), parse_float=Decimal)


def fmt6(value):
    """Six decimals, ROUND_HALF_UP (away from zero on a tie): 11.3172215 -> 11.317222."""
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    return str(d.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def write_new_or_same(path, data):
    """Write bytes to a new file; an existing file must already hold exactly these bytes (never rewritten).
    Returns True when written, False when the same bytes were already there."""
    if os.path.exists(path):
        if read_bytes(path) != data:
            raise RevpathsError(f"{path} exists with different content; it is not rewritten")
        return False
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "xb") as f:
        f.write(data)
    return True


def reused_problems(hash_file=None):
    """Check the reused stage-A files against revise/rules/reused.sha256 ("<sha256>  <path from repo root>" lines).
    Returns a list of problems; empty means every listed file matches."""
    hash_file = hash_file or REUSED_SHA256
    try:
        with open(hash_file, encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f if ln.strip() and not ln.startswith("#")]
    except OSError as e:
        return [f"REUSED FAIL: cannot read {hash_file}: {e}"]
    if not lines:
        return [f"REUSED FAIL: {hash_file} lists no files"]
    problems = []
    for ln in lines:
        m = _SUM_LINE.match(ln)                       # sha256sum text ("  ") and binary (" *") forms
        if not m:
            problems.append(f"REUSED FAIL: malformed line in {hash_file}: {ln!r}")
            continue
        want, rel = m.group(1).lower(), m.group(2).strip()
        path = os.path.join(REPO, *rel.split("/"))
        try:
            got = sha256(path)
        except OSError as e:
            problems.append(f"REUSED FAIL: {rel}: cannot read ({e.__class__.__name__})")
            continue
        if got != want:
            problems.append(f"REUSED FAIL: {rel}: sha256 {got} != recorded {want}")
    return problems


def _measure_free(volume):
    """Free bytes of one of DISK_VOLUMES. On Windows the WSL root file system is measured inside WSL."""
    if volume == "WSL /":
        import limits                                 # local import: limits does not depend on revpaths
        try:
            res = limits.run_limited(["wsl.exe", "-d", WSL_DISTRO, "--exec", "df", "-B1", "--output=avail", "/"],
                                     "preflight")
        except limits.SupervisionError as e:          # started, then supervision failed: no measurement
            msg = (f"df in WSL failed after it had started ({e.cause_type}; alive after cleanup: "
                   f"{e.killed_pids_alive}, unconfirmed: {e.cleanup_unconfirmed})")
            if e.killed_pids_alive or e.cleanup_unconfirmed:
                raise MeasureKillFail(msg, e.killed_pids_alive, e.cleanup_unconfirmed) from None
            raise OSError(msg) from None
        if res.killed_pids_alive or res.cleanup_unconfirmed:
            raise MeasureKillFail(f"df in WSL: processes alive after cleanup: {res.killed_pids_alive}, unconfirmed: "
                                  f"{res.cleanup_unconfirmed}", res.killed_pids_alive, res.cleanup_unconfirmed)
        if res.rc != 0 or res.timed_out:
            raise OSError(f"df in WSL failed: rc={res.rc} timed_out={res.timed_out}")
        return int(res.stdout.decode("ascii", "replace").split()[-1])
    return shutil.disk_usage(volume).free


def disk_problems(min_gb=20, free_bytes=None):
    """Both volumes need at least min_gb GiB free. free_bytes (tests): dict volume -> bytes or callable(volume).
    Every problem names the volume, the measured bytes and the measurement time. A measurement whose process cleanup
    failed (MeasureKillFail) gives a problem starting with KILL_FAIL (kill_fail_problems): the caller writes a stop
    record (its own side) and prints the instruction to commit it now (ruling R12)."""
    problems = []
    for vol in DISK_VOLUMES:
        when = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            if free_bytes is None:
                free = _measure_free(vol)
            elif callable(free_bytes):
                free = free_bytes(vol)
            else:
                free = free_bytes[vol]
        except MeasureKillFail as e:
            problems.append(f"{KILL_FAIL}: {vol}: disk measurement at {when} left processes behind or their exit "
                            f"cannot be confirmed (alive: {e.alive}, unconfirmed: {e.unconfirmed}): {e}")
            continue
        except (OSError, KeyError, ValueError, IndexError) as e:
            problems.append(f"DISK FAIL: {vol}: free space could not be measured at {when}: {e}")
            continue
        if free < min_gb * GB:
            problems.append(f"DISK FAIL: {vol}: {free} bytes free ({free / GB:.2f} GiB) < {min_gb} GiB, "
                            f"measured at {when}")
    return problems


def kill_fail_problems(problems):
    """The disk_problems entries of measurements whose process cleanup failed (they call for a stop record)."""
    return [p for p in problems if p.startswith(KILL_FAIL + ":")]


def directions(path=None):
    """metric_directions.json: {metric: {"better": "increase"|"decrease", "epsilon": "<decimal>"} | {"compare":
    "equal"}}; epsilon is returned as Decimal."""
    raw = load_json_decimal(path or METRIC_DIRECTIONS)
    if not isinstance(raw, dict) or not raw:
        raise RevpathsError("metric_directions.json: expected a non-empty object")
    out = {}
    for metric, spec in raw.items():
        if spec == {"compare": "equal"}:
            out[metric] = {"compare": "equal"}
        elif (isinstance(spec, dict) and set(spec) == {"better", "epsilon"}
              and spec["better"] in ("increase", "decrease") and isinstance(spec["epsilon"], str)):
            eps = Decimal(spec["epsilon"])
            if not eps.is_finite() or eps < 0:
                raise RevpathsError(f"metric_directions.json: {metric}: bad epsilon {spec['epsilon']!r}")
            out[metric] = {"better": spec["better"], "epsilon": eps}
        else:
            raise RevpathsError(f"metric_directions.json: {metric}: unexpected entry {spec!r}")
    return out
