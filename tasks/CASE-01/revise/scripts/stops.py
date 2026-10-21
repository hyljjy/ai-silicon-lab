"""Stop records, clearances and round locks for the CASE-01 stage B scripts (implementation plan Task 1 and data
contract; protocol v0.4 section 16).

- raise_stop writes revise/stops/r<rnd>/<stop_id>.json once ({stop_id, rnd, side, reason, code, details, time});
  stop_id = local timestamp + "-" + 4 random characters [a-z0-9]. The record is never rewritten.
- open_stops(rnd) returns every stop record of the round (both sides, "call" and "eval") that has no valid clearance.
  A clearance revise/stops/r<rnd>/<stop_id>.cleared.md is valid only when it is tracked by git and equal to HEAD, and
  its first two lines are exactly "stop_id: <id>" and "stop_sha256: <sha256 of the stop record file>". An unreadable
  stop record counts as open. The records are the union of the working tree and HEAD: a record committed in HEAD
  that is missing from the working tree or differs from HEAD counts as open (deleting a record never clears it).
- round_lock(rnd, side) holds revise/outputs/r<rnd>/.lock (side "call") or revise/results/r<rnd>/.lock (side "eval"),
  created with O_CREAT | O_EXCL; content {pid, start, side, acquired_at, platform}. These trees are shared by Windows
  and WSL (/mnt/d), where pids and start times mean different things: a lock written on another platform
  (sys.platform differs or is missing) -> LockError "LOCKED ... held from another OS", never taken over. Same
  platform: a holder that still runs (same pid AND start time, limits.still_alive) or cannot be verified -> LOCKED;
  a holder that has exited -> takeover, mutually exclusive among all takers (Codex BC1-04): the takeover guard
  <lock>.takeover is created with O_CREAT | O_EXCL (content {pid, start, platform, acquired_at, guards, nonce});
  only while it is held the lock is re-read, must be byte-identical to the stale content judged and its holder must
  still have exited; then os.replace(<unique temporary file>, lock) puts our content in place, so the lock is never
  absent and never moved aside; one line is appended to revise/stops/r<rnd>/lock_history.txt (time, old holder, new
  holder) and the guard is removed. An existing guard: held from another OS, by a running or unverifiable creator,
  or unreadable -> LOCKED; its creator provably exited on this platform -> the guard is broken by the same protocol
  under <lock>.takeover.takeover (a history line "takeover guard broken"); an existing <lock>.takeover.takeover is
  never broken (LOCKED, check by hand). No OS byte-range locks: they do not work between Windows and WSL on /mnt/d.
  Release removes the lock (and a guard) only while it still holds our own content.
Every function takes revise= (the revise directory) so tests can work in a temporary repository.
Python standard library only; Windows and WSL."""
import contextlib
import datetime
import json
import os
import secrets
import sys

import limits
import prereg
import revpaths as rp

SIDES = ("call", "eval")
_ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"


class StopsError(Exception):
    pass


class LockError(StopsError):
    pass


def _side(side):
    if side not in SIDES:
        raise ValueError(f"side must be one of {SIDES}, not {side!r}")
    return side


def _rnd(rnd):
    if isinstance(rnd, bool) or not isinstance(rnd, int) or rnd < 1:
        raise ValueError(f"round must be a positive integer, not {rnd!r}")
    return rnd


def stops_dir(rnd, revise=None):
    return os.path.join(revise or rp.REVISE, "stops", f"r{_rnd(rnd)}")


def lock_path(rnd, side, revise=None):
    base = "outputs" if _side(side) == "call" else "results"
    return os.path.join(revise or rp.REVISE, base, f"r{_rnd(rnd)}", ".lock")


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")


def raise_stop(rnd, side, reason, code=None, details=None, revise=None):
    """Write a new stop record; returns its stop_id."""
    _side(side)
    d = stops_dir(rnd, revise)
    os.makedirs(d, exist_ok=True)
    for _ in range(100):
        stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        stop_id = f"{stamp}-{''.join(secrets.choice(_ALNUM) for _ in range(4))}"
        rec = {"stop_id": stop_id, "rnd": rnd, "side": side, "reason": str(reason), "code": code,
               "details": details, "time": _now()}
        data = (json.dumps(rec, indent=1, ensure_ascii=False, default=str) + "\n").encode("utf-8")
        try:
            with open(os.path.join(d, f"{stop_id}.json"), "xb") as f:
                f.write(data)
            return stop_id
        except FileExistsError:
            continue
    raise StopsError("could not choose a new stop_id")


def _clearance_problem(d, stop_id, record_sha):
    path = os.path.join(d, f"{stop_id}.cleared.md")
    if not os.path.isfile(path):
        return "no clearance"
    if not prereg.committed_unchanged(path):
        return "clearance not committed (untracked or differs from HEAD)"
    lines = rp.read_bytes(path).decode("utf-8", "replace").split("\n")
    if len(lines) < 2:
        return "clearance has fewer than two lines"
    if lines[0].rstrip() != f"stop_id: {stop_id}":
        return f"clearance line 1 is {lines[0].rstrip()!r}, not 'stop_id: {stop_id}'"
    if lines[1].rstrip() != f"stop_sha256: {record_sha}":
        return f"clearance line 2 is {lines[1].rstrip()!r}, not 'stop_sha256: {record_sha}'"
    return None


def _head_record_names(d, revise):
    """File names of the stop records (*.json) of directory d committed in HEAD; empty when there is no HEAD."""
    base = revise or rp.REVISE
    rc, _ = prereg.git(["rev-parse", "--verify", "-q", "HEAD^{commit}"], base)
    if rc != 0:
        return set()
    rel = os.path.relpath(d, base).replace(os.sep, "/")
    rc, out = prereg.git(["ls-tree", "-z", "--name-only", "--full-name", "HEAD", "--", rel + "/"], base)
    if rc != 0:
        raise StopsError(f"git ls-tree HEAD {rel}/ failed; open stops cannot be determined")
    names = set()
    for full in out.decode("utf-8").split("\0"):
        name = full.rsplit("/", 1)[-1]
        if full and name.endswith(".json"):
            names.add(name)
    return names


def open_stops(rnd, revise=None):
    """Stop records of round rnd (both sides) without a valid clearance. Each item is the stop record plus
    "file", "sha256" and "why_open"; sorted by stop_id. Records are taken from the working tree and from HEAD."""
    d = stops_dir(rnd, revise)
    work = {n for n in os.listdir(d) if n.endswith(".json")} if os.path.isdir(d) else set()
    head = _head_record_names(d, revise)
    out = []
    for name in sorted(work | head):
        stop_id = name[:-len(".json")]
        path = os.path.join(d, name)
        if name in head:
            base = revise or rp.REVISE
            rel = os.path.relpath(path, base).replace(os.sep, "/")
            rc, committed = prereg.git(["cat-file", "blob", f"HEAD:./{rel}"], base)
            if rc != 0:
                raise StopsError(f"cannot read {rel} from HEAD; open stops cannot be determined")
            current = rp.read_bytes(path) if name in work else None
            if current != committed:
                try:
                    rec = json.loads(committed.decode("utf-8"))
                    rec = rec if isinstance(rec, dict) else {}
                except ValueError:
                    rec = {}
                out.append(dict(rec, stop_id=stop_id, file=path, sha256=rp.sha256_bytes(committed),
                                why_open="stop record missing or changed vs HEAD"))
                continue
        data = rp.read_bytes(path)
        sha = rp.sha256_bytes(data)
        try:
            rec = json.loads(data.decode("utf-8"))
            if not isinstance(rec, dict) or rec.get("stop_id") != stop_id:
                raise ValueError("stop_id field does not match the file name")
        except ValueError as e:
            out.append({"stop_id": stop_id, "rnd": rnd, "side": None, "reason": None, "file": path, "sha256": sha,
                        "why_open": f"unreadable stop record: {e}"})
            continue
        why = _clearance_problem(d, stop_id, sha)
        if why is not None:
            out.append(dict(rec, file=path, sha256=sha, why_open=why))
    return out


def _holder_text(rec):
    return f"pid={rec.get('pid')} start={rec.get('start')} acquired_at={rec.get('acquired_at')}"


def _hook(point, path):
    """Test seam, does nothing: called with "judged" when the holder of path (the lock or its takeover guard) has
    just been judged to have exited, before the takeover guard is taken, and with "guarded" when the takeover guard
    of path is held, before path is re-read."""


def _create_excl(path, data):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def _remove_if_mine(path, data):
    """Remove path only when it still holds exactly data (our own lock or guard)."""
    try:
        if rp.read_bytes(path) == data:
            os.remove(path)
    except OSError:
        pass


def _history(rnd, revise, text):
    hist_dir = stops_dir(rnd, revise)
    os.makedirs(hist_dir, exist_ok=True)
    with open(os.path.join(hist_dir, "lock_history.txt"), "ab") as f:
        f.write(f"{_now()}\t{text}\n".encode("utf-8"))


def _judge_exited(path, raw, what, rnd, side):
    """The holder record raw of path (the lock, or a takeover guard); returned only when its holder provably has
    exited on this platform, otherwise LockError."""
    where = f"round {rnd} side {side}"
    try:
        rec = json.loads(raw.decode("utf-8"))
        pid, start = int(rec["pid"]), rec["start"]
        if not isinstance(start, str) or not start:
            raise ValueError("no start time")
    except (ValueError, KeyError, TypeError) as e:
        raise LockError(f"LOCKED: {path} exists and cannot be read ({e}); remove it only after checking "
                        f"by hand that no run of {where} is active") from None
    if rec.get("platform") != sys.platform:
        raise LockError(f"LOCKED: {where}: the {what} is held from another OS (platform {rec.get('platform')!r}, "
                        f"here {sys.platform!r}; {_holder_text(rec)}); cannot verify the holder from here, the "
                        f"{what} is not taken over")
    alive, unconfirmed = limits.still_alive({"root_pid": pid, "root_start": start, "registry": []})
    if alive:
        raise LockError(f"LOCKED: {where}: the {what} is held by a running process ({_holder_text(rec)})")
    if unconfirmed:
        raise LockError(f"LOCKED: {where}: cannot confirm that the holder of the {what} ({_holder_text(rec)}) "
                        f"has exited")
    return rec


def _take_over(path, old_raw, new_data, ident, depth, rnd, side, revise):
    """Replace path, whose content old_raw was judged to belong to an exited holder, by new_data, mutually exclusive
    with every other taker. The takeover guard path + ".takeover" is created with O_CREAT | O_EXCL; only while it
    is held, path is re-read, must still be exactly old_raw and its holder must still have exited; then
    os.replace(<unique temporary file>, path), so path is never absent and never moved aside. The guard is removed
    afterwards (only if it still holds our content). depth 0: path is the lock; depth 1: path is the lock's takeover
    guard. An existing guard at depth 0 whose creator provably exited on this platform is broken the same way (under
    its own guard); an existing guard at depth 1 is never broken (LOCKED, to be checked by hand)."""
    where = f"round {rnd} side {side}"
    what = "lock" if depth == 0 else "takeover guard"
    guard = path + ".takeover"
    gdata = (json.dumps(dict(ident, acquired_at=_now(), guards=os.path.basename(path),
                             nonce=secrets.token_hex(6))) + "\n").encode("utf-8")
    try:
        _create_excl(guard, gdata)
    except FileExistsError:
        if depth >= 1:
            raise LockError(f"LOCKED: {where}: {guard} exists (a takeover of the takeover guard is running or was "
                            f"interrupted); remove it only after checking by hand that no run of {where} is "
                            f"active") from None
        try:
            graw = rp.read_bytes(guard)
        except FileNotFoundError:
            raise LockError(f"LOCKED: {where}: the takeover guard changed while it was checked") from None
        g = _judge_exited(guard, graw, "takeover guard", rnd, side)
        _hook("judged", guard)
        _take_over(guard, graw, gdata, ident, depth + 1, rnd, side, revise)   # we now hold the guard
        _history(rnd, revise, f"side={side}\ttakeover guard broken\told: {_holder_text(g)} (exited)\t"
                              f"new: {_holder_text(ident)}")
    try:
        _hook("guarded", path)
        try:
            cur = rp.read_bytes(path)
        except FileNotFoundError:
            cur = None
        if cur != old_raw:
            raise LockError(f"LOCKED: {where}: another process took the {what} over first (or it changed while it "
                            f"was checked); it is left as it is")
        _judge_exited(path, cur, what, rnd, side)
        tmp = f"{path}.new-{secrets.token_hex(6)}"
        _create_excl(tmp, new_data)
        try:
            os.replace(tmp, path)
        except OSError as e:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise LockError(f"LOCKED: {where}: the stale {what} could not be replaced ({e})") from None
    finally:
        _remove_if_mine(guard, gdata)


@contextlib.contextmanager
def round_lock(rnd, side, revise=None):
    """Exclusive ownership of round rnd on one side for the duration of the with-block (see module doc)."""
    path = lock_path(rnd, side, revise)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    start = limits._start_time(os.getpid())
    if start is None:
        raise LockError("LOCKED: the start time of this process cannot be read; lock not taken")
    ident = {"pid": os.getpid(), "start": start, "platform": sys.platform}
    mine = {"pid": os.getpid(), "start": start, "side": side, "acquired_at": _now(), "platform": sys.platform}
    data = (json.dumps(mine) + "\n").encode("utf-8")
    try:
        _create_excl(path, data)
    except FileExistsError:
        try:
            old_raw = rp.read_bytes(path)
        except FileNotFoundError:
            raise LockError(f"LOCKED: round {rnd} side {side}: the lock changed while it was checked") from None
        old = _judge_exited(path, old_raw, "lock", rnd, side)
        _hook("judged", path)
        try:
            _take_over(path, old_raw, data, ident, 0, rnd, side, revise)
            _history(rnd, revise, f"side={side}\ttaken over\told: {_holder_text(old)} (exited)\t"
                                  f"new: {_holder_text(mine)}")
        except BaseException:
            _remove_if_mine(path, data)
            raise
    try:
        yield mine
    finally:
        _remove_if_mine(path, data)
