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
  a holder that has exited -> the lock is moved aside (os.replace to a unique name, content re-checked), one line is
  appended to revise/stops/r<rnd>/lock_history.txt (time, old holder, new holder), and the lock is created anew.
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


@contextlib.contextmanager
def round_lock(rnd, side, revise=None):
    """Exclusive ownership of round rnd on one side for the duration of the with-block (see module doc)."""
    path = lock_path(rnd, side, revise)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    start = limits._start_time(os.getpid())
    if start is None:
        raise LockError("LOCKED: the start time of this process cannot be read; lock not taken")
    mine = {"pid": os.getpid(), "start": start, "side": side, "acquired_at": _now(), "platform": sys.platform}
    data = (json.dumps(mine) + "\n").encode("utf-8")

    def create():
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o644)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)

    try:
        create()
    except FileExistsError:
        old_raw = rp.read_bytes(path)
        try:
            old = json.loads(old_raw.decode("utf-8"))
            old_pid, old_start = int(old["pid"]), old["start"]
            if not isinstance(old_start, str) or not old_start:
                raise ValueError("no start time")
        except (ValueError, KeyError, TypeError) as e:
            raise LockError(f"LOCKED: {path} exists and cannot be read ({e}); remove it only after checking "
                            f"by hand that no run of round {rnd} side {side} is active") from None
        if old.get("platform") != sys.platform:
            raise LockError(f"LOCKED: round {rnd} side {side} is held from another OS (platform "
                            f"{old.get('platform')!r}, here {sys.platform!r}; {_holder_text(old)}); cannot verify "
                            f"the holder from here, the lock is not taken over")
        alive, unconfirmed = limits.still_alive({"root_pid": old_pid, "root_start": old_start, "registry": []})
        if alive:
            raise LockError(f"LOCKED: round {rnd} side {side} is held by a running process ({_holder_text(old)})")
        if unconfirmed:
            raise LockError(f"LOCKED: round {rnd} side {side}: cannot confirm that the holder "
                            f"({_holder_text(old)}) has exited")
        # move the stale lock aside under a unique name, then check that what was moved is the lock just verified
        aside = f"{path}.stale-{secrets.token_hex(6)}"
        try:
            os.replace(path, aside)
        except FileNotFoundError:
            raise LockError(f"LOCKED: round {rnd} side {side}: the lock changed while it was checked") from None
        if rp.read_bytes(aside) != old_raw:         # another process took it over meanwhile: put its lock back
            try:
                os.link(aside, path)                # fails when a lock exists again; never overwrites one
                os.remove(aside)
                note = "its lock was put back"
            except OSError as e:
                note = f"its lock could not be put back ({e}); it is kept at {aside}"
            raise LockError(f"LOCKED: round {rnd} side {side}: another process took the lock over first; {note}")
        os.remove(aside)
        hist_dir = stops_dir(rnd, revise)
        os.makedirs(hist_dir, exist_ok=True)
        with open(os.path.join(hist_dir, "lock_history.txt"), "ab") as f:
            f.write(f"{_now()}\tside={side}\ttaken over\told: {_holder_text(old)} (exited)\t"
                    f"new: {_holder_text(mine)}\n".encode("utf-8"))
        try:
            create()
        except FileExistsError:
            raise LockError(f"LOCKED: round {rnd} side {side}: another process took the lock over first") from None
    try:
        yield mine
    finally:
        try:
            if rp.read_bytes(path) == data:
                os.remove(path)
        except OSError:
            pass
