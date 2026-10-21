"""The salted code mapping of the CASE-01 stage B rounds (implementation plan Task 1 and data contract; protocol v0.4
section 7.1). This is the only module that reads or writes the sealed mapping.

commit_codes(rnd, models, prev) writes, all new (never rewritten):
  <sealed>/mapping_r<rnd>.json              {"round", "salt", "entries": [{"model", "code", "prev_code"}]}
  revise/outputs/r<rnd>/codes.txt           the round's codes, one per line, sorted; no model names
  revise/outputs/mapping_r<rnd>.sha256      "<sha256 of the sealed file>  mapping_r<rnd>.json"
Codes are "cand_" + 4 characters [a-z0-9] (secrets.choice), unique within the round and against every existing
revise/outputs/r*/codes.txt (regenerated on a collision). The salt has 128 bits (32 hex digits).
Committing codes.txt and the .sha256 file (stage A) is the caller's job (diag_commit.sh).
load(rnd) checks that mapping_r<rnd>.sha256 and codes.txt are tracked and equal to HEAD, that the sealed file's sha256
equals the committed one, and that codes.txt lists exactly the mapping's codes; otherwise MappingError.
code_of / model_of / prev_code work on the dict returned by load.
Every function takes revise= and sealed= so tests never touch the real directories. Python standard library only."""
import json
import os
import re
import secrets

import prereg
import revpaths as rp

SEALED = os.path.join(rp.SANDBOX, "sealed")
_ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"
CODE_RE = re.compile(r"cand_[a-z0-9]{4}")
MAX_TRIES = 1000


class MappingError(Exception):
    pass


def _new_code():
    return "cand_" + "".join(secrets.choice(_ALNUM) for _ in range(4))


def _paths(rnd, revise, sealed):
    if isinstance(rnd, bool) or not isinstance(rnd, int) or rnd < 1:
        raise MappingError(f"round must be a positive integer, not {rnd!r}")
    outputs = os.path.join(revise or rp.REVISE, "outputs")
    return {"outputs": outputs,
            "sealed": os.path.join(sealed or SEALED, f"mapping_r{rnd}.json"),
            "codes": os.path.join(outputs, f"r{rnd}", "codes.txt"),
            "sha": os.path.join(outputs, f"mapping_r{rnd}.sha256")}


def _used_codes(outputs):
    used = set()
    if not os.path.isdir(outputs):
        return used
    for name in os.listdir(outputs):
        p = os.path.join(outputs, name, "codes.txt")
        if re.fullmatch(r"r\d+", name) and os.path.isfile(p):
            used.update(ln.strip() for ln in rp.read_bytes(p).decode("utf-8").splitlines() if ln.strip())
    return used


def commit_codes(rnd, models, prev, revise=None, sealed=None):
    """New codes for `models` (list, in that order) of round rnd; prev = {model: code of round rnd-1} for rnd >= 2
    (checked against the committed mapping of round rnd-1), None for round 1. Returns the codes in model order."""
    p = _paths(rnd, revise, sealed)
    models = list(models)
    if not models or len(set(models)) != len(models) or not all(isinstance(m, str) and m for m in models):
        raise MappingError(f"models must be distinct non-empty names: {models!r}")
    for key in ("sealed", "codes", "sha"):
        if os.path.exists(p[key]):
            raise MappingError(f"round {rnd} already has {p[key]}; codes are committed once per round")
    if rnd == 1:
        if prev:
            raise MappingError("round 1 has no previous codes")
        prev_of = {m: None for m in models}
    else:
        if not isinstance(prev, dict) or set(prev) != set(models):
            raise MappingError(f"round {rnd} needs the previous code of every model")
        before = load(rnd - 1, revise=revise, sealed=sealed)
        for m in models:
            if code_of(before, m) != prev[m]:
                raise MappingError(f"previous code given for a model does not match the committed round {rnd - 1}")
        prev_of = dict(prev)

    used = _used_codes(p["outputs"])
    codes = []
    for _ in models:
        for _ in range(MAX_TRIES):
            c = _new_code()
            if CODE_RE.fullmatch(c) and c not in used:
                break
        else:
            raise MappingError("could not generate a new unique code")
        used.add(c)
        codes.append(c)

    doc = {"round": rnd, "salt": secrets.token_hex(16),
           "entries": [{"model": m, "code": c, "prev_code": prev_of[m]} for m, c in zip(models, codes)]}
    sealed_bytes = (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    rp.write_new_or_same(p["sealed"], sealed_bytes)
    rp.write_new_or_same(p["codes"], "".join(c + "\n" for c in sorted(codes)).encode("ascii"))
    rp.write_new_or_same(p["sha"], f"{rp.sha256_bytes(sealed_bytes)}  mapping_r{rnd}.json\n".encode("ascii"))
    return codes


def load(rnd, revise=None, sealed=None):
    """The sealed mapping of round rnd after checking it against the committed commitment (see module doc)."""
    p = _paths(rnd, revise, sealed)
    for key in ("sha", "codes"):
        if not prereg.committed_unchanged(p[key]):
            raise MappingError(f"MAPPING FAIL: {p[key]} is missing, untracked or differs from HEAD")
    parts = rp.read_bytes(p["sha"]).decode("ascii", "replace").split()
    if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]) or parts[1] != f"mapping_r{rnd}.json":
        raise MappingError(f"MAPPING FAIL: {p['sha']} is malformed")
    try:
        data = rp.read_bytes(p["sealed"])
    except OSError as e:
        raise MappingError(f"MAPPING FAIL: sealed mapping of round {rnd} cannot be read ({e.__class__.__name__})")
    got = rp.sha256_bytes(data)
    if got != parts[0]:
        raise MappingError(f"MAPPING FAIL: sealed mapping of round {rnd}: sha256 {got} != committed {parts[0]}")
    try:
        doc = json.loads(data.decode("utf-8"))
        entries = doc["entries"]
        ok = (doc["round"] == rnd and isinstance(doc["salt"], str) and len(doc["salt"]) >= 32
              and isinstance(entries, list) and entries
              and all(set(e) == {"model", "code", "prev_code"} and CODE_RE.fullmatch(e["code"]) for e in entries))
    except (ValueError, KeyError, TypeError) as e:
        raise MappingError(f"MAPPING FAIL: sealed mapping of round {rnd} is malformed ({e})") from None
    if not ok:
        raise MappingError(f"MAPPING FAIL: sealed mapping of round {rnd} is malformed")
    codes = [e["code"] for e in entries]
    models = [e["model"] for e in entries]
    if len(set(codes)) != len(codes) or len(set(models)) != len(models):
        raise MappingError(f"MAPPING FAIL: sealed mapping of round {rnd} repeats a code or a model")
    listed = rp.read_bytes(p["codes"]).decode("utf-8").splitlines()
    if listed != sorted(codes):
        raise MappingError(f"MAPPING FAIL: {p['codes']} does not list exactly the codes of the mapping")
    return doc


def _entry(m, key, value):
    hits = [e for e in m["entries"] if e[key] == value]
    if len(hits) != 1:
        raise MappingError(f"round {m['round']}: no single entry with this {key}")
    return hits[0]


def code_of(m, model):
    return _entry(m, "model", model)["code"]


def model_of(m, code):
    return _entry(m, "code", code)["model"]


def prev_code(m, code):
    return _entry(m, "code", code)["prev_code"]
