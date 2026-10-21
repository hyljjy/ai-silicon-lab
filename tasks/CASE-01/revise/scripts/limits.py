"""Run limits and process cleanup for the CASE-01 stage B scripts (implementation plan, Global Constraints
"运行上限" and "进程清理"). Python standard library only; Windows (python 3.13) and Linux/WSL (python3 3.12.3).

Ownership (primary):
  - Windows: the target is created suspended (CREATE_SUSPENDED), put into a new Job Object with
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE, and only then resumed, so every descendant belongs to the job from its first
    instruction (no window between Popen and AssignProcessToJobObject). Forced stop: TerminateJobObject; liveness:
    QueryInformationJobObject (active process count, process id list). Closing the job handle at the end also kills
    anything left (safety net), after the result has been measured.
  - Linux: prctl(PR_SET_CHILD_SUBREAPER, 1) on the calling process before the target starts. Orphaned descendants
    (including those in a new session or process group) are re-parented to the caller, so they stay reachable through
    /proc PPid chains: descendants of the root plus processes adopted by the caller that started after the root.
    Limitation: one run_limited at a time per process (concurrent calls could attribute each other's orphans).
  - If the mechanism cannot be set up, IsolationFail ("ISOLATION FAIL ...") is raised and the target never runs.
Registry (secondary): root pid and start time at launch, then every 1 s all descendants with start times. A process is
the same process only when pid AND start time match (pid reuse is not confused with a survivor).
Cleanup: gentle (POSIX: SIGTERM to the root only; Windows: none) -> wait term_wait -> forced (POSIX: SIGKILL to the
root and every registered process still alive with the registered start time; Windows: TerminateJobObject) -> wait
kill_wait -> verify. Anything still alive -> killed_pids_alive; anything unverifiable -> cleanup_unconfirmed.
"""
import collections
import datetime
import json
import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field

MB = 1024 * 1024                                     # "MB" in the limits table = MiB (1024 * 1024 bytes)

Limit = collections.namedtuple("Limit", "timeout stdout_max stderr_max term_wait kill_wait")

# The only source is the "运行上限" table of the implementation plan; keys in table order.
LIMITS = {
    "model": Limit(1800, 50 * MB, 1 * MB, 30, 30),       # model call (claude.exe)
    "preflight": Limit(60, 1 * MB, 1 * MB, 10, 10),      # preflight commands (--version, auth status)
    "yosys": Limit(60, 10 * MB, 10 * MB, 10, 10),        # Yosys (gate)
    "grade": Limit(7200, 50 * MB, 50 * MB, 90, 30),      # grade.py (called by run_grade.py)
    "test": Limit(30, 1 * MB, 1 * MB, 5, 5),             # subprocesses started by tests
}

SCAN_INTERVAL = 1.0
POLL = 0.05
READ_CHUNK = 65536
CLEANUP_SLACK = 10                                    # cleanup total <= term_wait + kill_wait + 10 s
PIPE_EOF_WAIT = 2.0                                   # after cleanup, both pipes must reach EOF within this time


class IsolationFail(RuntimeError):
    pass


@dataclass
class Limited:
    rc: object
    timed_out: bool
    stdout_over: bool
    stderr_over: bool
    stdout: bytes
    stderr: bytes
    stdout_bytes: int
    stderr_bytes: int
    signals_sent: list = field(default_factory=list)
    killed_pids_alive: list = field(default_factory=list)
    cleanup_unconfirmed: bool = False
    registry: list = field(default_factory=list)
    isolation: str = ""
    output_error: object = None                       # str when writing stdout_path/stderr_path failed (run stopped)

    @property
    def incomplete(self):
        """Output is not complete (limit exceeded, output file write failed, or the process was stopped): write
        "超限，输出不完整"."""
        return self.timed_out or self.stdout_over or self.stderr_over or bool(self.output_error)


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")


# ---------------------------------------------------------------------------------------------- platform: Windows
if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _H = wintypes.HANDLE

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in ("ReadOperationCount", "WriteOperationCount",
                                                      "OtherOperationCount", "ReadTransferCount",
                                                      "WriteTransferCount", "OtherTransferCount")]

    class _BASIC_LIMIT(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class _EXT_LIMIT(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _BASIC_LIMIT), ("IoInfo", _IO_COUNTERS),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class _ACCOUNTING(ctypes.Structure):
        _fields_ = [("TotalUserTime", ctypes.c_int64), ("TotalKernelTime", ctypes.c_int64),
                    ("ThisPeriodTotalUserTime", ctypes.c_int64), ("ThisPeriodTotalKernelTime", ctypes.c_int64),
                    ("TotalPageFaultCount", wintypes.DWORD), ("TotalProcesses", wintypes.DWORD),
                    ("ActiveProcesses", wintypes.DWORD), ("TotalTerminatedProcesses", wintypes.DWORD)]

    _MAX_IDS = 4096

    class _PIDLIST(ctypes.Structure):
        _fields_ = [("NumberOfAssignedProcesses", wintypes.DWORD), ("NumberOfProcessIdsInList", wintypes.DWORD),
                    ("ProcessIdList", ctypes.c_size_t * _MAX_IDS)]

    class _THREADENTRY32(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ThreadID", wintypes.DWORD),
                    ("th32OwnerProcessID", wintypes.DWORD), ("tpBasePri", wintypes.LONG),
                    ("tpDeltaPri", wintypes.LONG), ("dwFlags", wintypes.DWORD)]

    def _proto(name, restype, *argtypes):
        fn = getattr(_k32, name)
        fn.restype, fn.argtypes = restype, list(argtypes)
        return fn

    _CreateJobObjectW = _proto("CreateJobObjectW", _H, wintypes.LPVOID, wintypes.LPCWSTR)
    _SetInformationJobObject = _proto("SetInformationJobObject", wintypes.BOOL, _H, ctypes.c_int, wintypes.LPVOID,
                                      wintypes.DWORD)
    _QueryInformationJobObject = _proto("QueryInformationJobObject", wintypes.BOOL, _H, ctypes.c_int,
                                        wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
    _AssignProcessToJobObject = _proto("AssignProcessToJobObject", wintypes.BOOL, _H, _H)
    _TerminateJobObject = _proto("TerminateJobObject", wintypes.BOOL, _H, wintypes.UINT)
    _CloseHandle = _proto("CloseHandle", wintypes.BOOL, _H)
    _OpenProcess = _proto("OpenProcess", _H, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _GetProcessTimes = _proto("GetProcessTimes", wintypes.BOOL, _H, *([ctypes.POINTER(ctypes.c_uint64)] * 4))
    _WaitForSingleObject = _proto("WaitForSingleObject", wintypes.DWORD, _H, wintypes.DWORD)
    _TerminateProcess = _proto("TerminateProcess", wintypes.BOOL, _H, wintypes.UINT)
    _CreateToolhelp32Snapshot = _proto("CreateToolhelp32Snapshot", _H, wintypes.DWORD, wintypes.DWORD)
    _Thread32First = _proto("Thread32First", wintypes.BOOL, _H, ctypes.POINTER(_THREADENTRY32))
    _Thread32Next = _proto("Thread32Next", wintypes.BOOL, _H, ctypes.POINTER(_THREADENTRY32))
    _OpenThread = _proto("OpenThread", _H, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _ResumeThread = _proto("ResumeThread", wintypes.DWORD, _H)

    _JobObjectBasicAccountingInformation = 1
    _JobObjectBasicProcessIdList = 3
    _JobObjectExtendedLimitInformation = 9
    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    _CREATE_SUSPENDED = 0x4
    _PROCESS_TERMINATE = 0x1
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _SYNCHRONIZE = 0x00100000
    _WAIT_OBJECT_0 = 0x0
    _WAIT_TIMEOUT = 0x102
    _ERROR_INVALID_PARAMETER = 87
    _TH32CS_SNAPTHREAD = 0x4
    _THREAD_SUSPEND_RESUME = 0x2
    _INVALID_HANDLE = ctypes.c_void_p(-1).value

    def _winerr(what):
        err = ctypes.get_last_error()
        return OSError(err, f"{what} failed: {ctypes.FormatError(err).strip()}")

    def _open(pid, access):
        """Process handle, or None when no such process exists; any other failure raises OSError."""
        h = _OpenProcess(access, False, pid)
        if not h:
            if ctypes.get_last_error() == _ERROR_INVALID_PARAMETER:
                return None
            raise _winerr(f"OpenProcess({pid})")
        return h

    def _start_of_handle(h):
        c, e, k, u = (ctypes.c_uint64() for _ in range(4))
        if not _GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
            raise _winerr("GetProcessTimes")
        state = _WaitForSingleObject(h, 0)             # signaled = exited (an exit code of 259 is no evidence)
        if state == _WAIT_TIMEOUT:
            return str(c.value)
        if state == _WAIT_OBJECT_0:
            return None
        raise _winerr("WaitForSingleObject")

    def _start_time(pid):
        """Creation time (FILETIME, as a decimal string) of a running process; None when it does not run."""
        h = _open(pid, _PROCESS_QUERY_LIMITED_INFORMATION | _SYNCHRONIZE)
        if h is None:
            return None
        try:
            return _start_of_handle(h)
        finally:
            _CloseHandle(h)

    def _kill_pid(pid):
        h = _open(pid, _PROCESS_TERMINATE)
        if h is not None:
            try:
                _TerminateProcess(h, 1)
            finally:
                _CloseHandle(h)

    class _Job:
        def __init__(self):
            self.handle = _CreateJobObjectW(None, None)
            if not self.handle:
                raise _winerr("CreateJobObjectW")
            info = _EXT_LIMIT()
            info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not _SetInformationJobObject(self.handle, _JobObjectExtendedLimitInformation, ctypes.byref(info),
                                            ctypes.sizeof(info)):
                err = _winerr("SetInformationJobObject")
                _CloseHandle(self.handle)
                raise err

        def assign(self, proc_handle):
            if not _AssignProcessToJobObject(self.handle, _H(int(proc_handle))):
                raise _winerr("AssignProcessToJobObject")

        def active(self):
            info = _ACCOUNTING()
            if not _QueryInformationJobObject(self.handle, _JobObjectBasicAccountingInformation, ctypes.byref(info),
                                              ctypes.sizeof(info), None):
                raise _winerr("QueryInformationJobObject(accounting)")
            return info.ActiveProcesses

        def pids(self):
            info = _PIDLIST()
            if not _QueryInformationJobObject(self.handle, _JobObjectBasicProcessIdList, ctypes.byref(info),
                                              ctypes.sizeof(info), None):
                raise _winerr("QueryInformationJobObject(process id list)")
            return [int(info.ProcessIdList[i]) for i in range(info.NumberOfProcessIdsInList)]

        def terminate(self):
            if not _TerminateJobObject(self.handle, 1):
                raise _winerr("TerminateJobObject")

        def close(self):
            if self.handle:
                _CloseHandle(self.handle)
                self.handle = None

    def _resume_process(pid):
        """Resume the (single) main thread of a process created with CREATE_SUSPENDED."""
        snap = _CreateToolhelp32Snapshot(_TH32CS_SNAPTHREAD, 0)
        if not snap or snap == _INVALID_HANDLE:
            raise _winerr("CreateToolhelp32Snapshot")
        resumed = 0
        try:
            te = _THREADENTRY32()
            te.dwSize = ctypes.sizeof(te)
            ok = _Thread32First(snap, ctypes.byref(te))
            while ok:
                if te.th32OwnerProcessID == pid:
                    th = _OpenThread(_THREAD_SUSPEND_RESUME, False, te.th32ThreadID)
                    if not th:
                        raise _winerr("OpenThread")
                    try:
                        if _ResumeThread(th) == 0xFFFFFFFF:
                            raise _winerr("ResumeThread")
                        resumed += 1
                    finally:
                        _CloseHandle(th)
                ok = _Thread32Next(snap, ctypes.byref(te))
        finally:
            _CloseHandle(snap)
        if not resumed:
            raise OSError(f"no thread of pid {pid} to resume")

    def _setup_isolation():
        """Create the job for one run (raises OSError when the mechanism is unavailable)."""
        return _Job()

    def _isolation_name():
        return "job"

# ------------------------------------------------------------------------------------------------ platform: Linux
else:
    import ctypes

    _PR_SET_CHILD_SUBREAPER = 36
    _PR_GET_CHILD_SUBREAPER = 37

    def _setup_isolation():
        """Make the calling process a child subreaper (raises OSError when that is impossible)."""
        if not os.path.isdir("/proc/self"):
            raise OSError("no /proc: the subreaper mechanism needs Linux")
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(_PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
            err = ctypes.get_errno()
            raise OSError(err, f"prctl(PR_SET_CHILD_SUBREAPER) failed: {os.strerror(err)}")
        flag = ctypes.c_int(0)
        if libc.prctl(_PR_GET_CHILD_SUBREAPER, ctypes.byref(flag), 0, 0, 0) != 0 or flag.value != 1:
            raise OSError("PR_SET_CHILD_SUBREAPER did not take effect")
        return None

    def _isolation_name():
        return "subreaper"

    def _stat(pid):
        """(state, ppid, starttime) from /proc/<pid>/stat; None when the process does not exist."""
        try:
            with open(f"/proc/{pid}/stat", "rb") as f:
                data = f.read().decode("ascii", "replace")
        except (FileNotFoundError, ProcessLookupError):
            return None
        rest = data[data.rindex(")") + 2:].split()
        return rest[0], int(rest[1]), rest[19]

    def _start_time(pid):
        """Start time (clock ticks since boot, as a decimal string) of a running process; None when it does not
        exist or is a zombie (exited, not yet reaped)."""
        st = _stat(pid)
        if st is None or st[0] in ("Z", "X", "x"):
            return None
        return st[2]

    def _table():
        """{pid: (state, ppid, starttime)} for every process; raises OSError when /proc cannot be read."""
        out = {}
        for name in os.listdir("/proc"):
            if name.isdigit():
                st = _stat(int(name))
                if st is not None:
                    out[int(name)] = st
        return out

    def _kill_pid(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def _resume_process(pid):
        pass


def _is_alive(pid, start):
    """True when pid runs AND its start time equals the registered one (a reused pid is not the same process)."""
    return start is not None and _start_time(pid) == start


_NO_REAP = set()                                      # roots owned by a Popen object: never reaped behind its back
_SURVIVORS = []                                       # Popen objects whose process outlived cleanup (KILL FAIL):
                                                      # kept referenced, never silently dropped


def _reap(entries):
    """Collect exit statuses of adopted (subreaper) children so they do not linger as zombies. entries: (pid,
    start) pairs; only a zombie whose parent is this process and whose start time is the registered one is reaped."""
    for p in list(_SURVIVORS):                         # a KILL FAIL survivor that has exited since: collect it
        if p.poll() is not None:
            _SURVIVORS.remove(p)
            for pipe in (p.stdout, p.stderr, p.stdin):
                try:
                    if pipe is not None:
                        pipe.close()
                except (OSError, ValueError):
                    pass
    if os.name == "nt":
        return
    me = os.getpid()
    survivors = {p.pid for p in _SURVIVORS}
    for pid, start in entries:
        if pid in survivors:
            continue
        if pid in _NO_REAP:
            continue
        try:
            st = _stat(pid)
            if st is None or st[0] != "Z" or st[1] != me or st[2] != start:
                continue
            os.waitpid(pid, os.WNOHANG)
        except (OSError, ValueError, IndexError):
            pass


def _force_kill(ctx, pids):
    """Forced stop. ctx is the run's job (Windows) or None; pids: processes verified alive with their start time."""
    if ctx is not None:
        ctx.terminate()
        return
    for pid in pids:
        _kill_pid(pid)


class _Run:
    """State of one supervised process tree: root, registry, ownership context."""

    def __init__(self, root_pid, root_start, ctx, isolation, popen=None, registry=None, prior_children=()):
        self.root_pid, self.root_start, self.ctx, self.isolation, self.popen = root_pid, root_start, ctx, \
            isolation, popen
        self.registry = collections.OrderedDict(registry or [(root_pid, root_start)])
        self.prior_children = set(prior_children)
        self.signals = []
        self.unconfirmed = False

    def root_alive(self):
        """Root still running: the Popen object (when we own it) or the process table, pid AND start time."""
        if self.popen is not None and self.popen.poll() is None:
            return True
        try:
            return _is_alive(self.root_pid, self.root_start)
        except OSError:
            self.unconfirmed = True
            return False

    def scan(self):
        """Add current descendants to the registry. Returns True when the registry changed; on a read failure
        marks the run unconfirmed and returns False."""
        try:
            found = self._members()
        except OSError:
            self.unconfirmed = True
            return False
        changed = False
        for pid, start in found.items():
            if start is not None and pid not in self.registry:
                self.registry[pid] = start
                changed = True
        return changed

    def _members(self):
        if os.name == "nt":
            if self.ctx is None:
                return {}
            return {pid: _start_time(pid) for pid in self.ctx.pids()}
        table = _table()
        me = os.getpid()
        root_ticks = int(self.root_start) if self.root_start and self.root_start.isdigit() else None
        seeds = {pid for pid, st in self.registry.items() if _alive_in(table, pid, st)}
        if root_ticks is not None:
            for pid, (state, ppid, start) in table.items():
                # adopted orphans: re-parented to this (subreaper) process and started after the root
                if ppid == me and pid not in self.prior_children and pid != self.root_pid \
                        and int(start) >= root_ticks and state not in ("Z", "X", "x"):
                    if self.popen is not None or pid in self.registry:
                        seeds.add(pid)
        children = collections.defaultdict(list)
        for pid, (_, ppid, _) in table.items():
            children[ppid].append(pid)
        out, stack = {}, list(seeds)
        while stack:
            pid = stack.pop()
            if pid in out or pid not in table:
                continue
            state, _, start = table[pid]
            if state not in ("Z", "X", "x"):
                out[pid] = start
            stack.extend(children.get(pid, ()))
        return out

    def alive_registered(self):
        """Registered processes (root included) still alive with their registered start time. A failed check counts
        as alive-unknown: the run is marked unconfirmed."""
        _reap(list(self.registry.items()))
        alive = []
        for pid, start in self.registry.items():
            if pid == self.root_pid:
                if self.root_alive():
                    alive.append(pid)
                continue
            try:
                if _is_alive(pid, start):
                    alive.append(pid)
            except OSError:
                self.unconfirmed = True
        return alive

    def job_active(self):
        if os.name != "nt" or self.ctx is None:
            return 0, []
        try:
            n = self.ctx.active()
            return n, (self.ctx.pids() if n else [])
        except OSError:
            self.unconfirmed = True
            return 0, []

    def anything_alive(self):
        n, _ = self.job_active()
        return bool(self.alive_registered()) or n > 0

    def gentle(self, wait):
        """POSIX: SIGTERM to the root only, then wait until everything is gone or `wait` seconds passed."""
        if os.name == "nt" or not self.root_alive():
            return
        try:
            os.kill(self.root_pid, signal.SIGTERM)
            self.signals.append(f"SIGTERM {self.root_pid}")
        except ProcessLookupError:
            return
        self._wait_gone(wait)

    def forced(self, wait):
        """Forced stop of everything registered and still alive (Windows: the whole job), repeated until all are
        gone or `wait` seconds passed (descendants started meanwhile are registered and killed too)."""
        deadline = time.monotonic() + wait
        first = True
        while True:
            self.scan()
            alive = self.alive_registered()
            n, _ = self.job_active()
            if not alive and not n:
                return
            if time.monotonic() >= deadline:
                return
            try:
                _force_kill(self.ctx, alive)
            except OSError:
                pass
            if first:
                if self.ctx is not None:
                    self.signals.append("TerminateJobObject")
                else:
                    name = "TerminateProcess" if os.name == "nt" else "SIGKILL"
                    self.signals.append(name + " " + " ".join(str(p) for p in alive))
                first = False
            time.sleep(POLL * 2)

    def _wait_gone(self, wait):
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            self.scan()
            if not self.anything_alive():
                return
            time.sleep(POLL)

    def stop(self, lim, gentle=True):
        self.scan()
        if gentle:
            self.gentle(lim.term_wait)
        if self.anything_alive():
            self.forced(lim.kill_wait)

    def verify(self):
        """Final check: pids still alive (root always checked; Windows: the job must be empty)."""
        alive = self.alive_registered()
        n, jpids = self.job_active()
        if n:
            alive += [p for p in jpids if p not in alive] or [self.root_pid]
        return sorted(set(alive))

    def record(self):
        return {"root_pid": self.root_pid, "root_start": self.root_start,
                "registry": [[p, s] for p, s in self.registry.items()], "isolation": self.isolation}


def _alive_in(table, pid, start):
    st = table.get(pid)
    return st is not None and st[2] == start and st[0] not in ("Z", "X", "x")


def _write_json(path, obj):
    tmp = path + ".tmp"
    data = (json.dumps(obj, indent=1) + "\n").encode("utf-8")
    with open(tmp, "wb") as f:
        f.write(data)
    for i in range(50):                               # Windows: a concurrent reader can briefly block the replace
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == 49:
                raise
            time.sleep(0.02)


def _open_output(path):
    return open(path, "ab")


class _Reader(threading.Thread):
    """Reads one pipe in chunks: keeps and appends to file at most `limit` bytes, then discards the rest (the
    process is being stopped) while still draining so the writer never blocks on a full pipe. A failed write to the
    output file (e.g. disk full) is recorded in write_error, stops further file writes and triggers the stop path;
    the pipe keeps draining."""

    def __init__(self, fd, limit, path, over_event, on_line=None):
        super().__init__(daemon=True)
        self.fd, self.limit, self.over_event, self.on_line = fd, limit, over_event, on_line
        self.path = path
        self.file = _open_output(path) if path else None
        self.buf = bytearray()
        self.over = False
        self.partial = b""
        self.error = None
        self.write_error = None

    def _write(self, data):
        try:
            self.file.write(data)
            self.file.flush()
        except Exception as e:                      # disk full, I/O error ...: record, stop writing, stop the run
            self.write_error = f"{self.path}: {e.__class__.__name__}: {e}"
            f, self.file = self.file, None
            try:
                f.close()
            except Exception:
                pass
            self.over_event.set()

    def run(self):
        try:
            while True:
                try:
                    chunk = os.read(self.fd, READ_CHUNK)
                except OSError:
                    break
                if not chunk:
                    break
                room = self.limit - len(self.buf)
                keep = chunk[:max(room, 0)]
                if keep:
                    self.buf += keep
                    if self.file:
                        self._write(keep)
                    if self.on_line is not None and self.error is None:
                        self._lines(keep)
                if len(chunk) > room and not self.over:
                    self.over = True
                    self.over_event.set()
        finally:
            if self.file:
                try:
                    self.file.close()
                except Exception as e:
                    if self.write_error is None:
                        self.write_error = f"{self.path}: {e.__class__.__name__}: {e}"

    def _lines(self, data):
        self.partial += data
        *lines, self.partial = self.partial.split(b"\n")
        for line in lines:
            try:
                self.on_line(line.rstrip(b"\r").decode("utf-8", "replace"))
            except BaseException as e:            # reported to the caller after cleanup
                self.error = e
                self.over_event.set()
                return


def _children_of_me():
    if os.name == "nt":
        return set()
    try:
        me = os.getpid()
        return {pid for pid, (_, ppid, _) in _table().items() if ppid == me}
    except OSError:
        return set()


def run_limited(argv, kind, cwd=None, env=None, stdin_bytes=None, stdout_path=None, stderr_path=None,
                proc_path=None, on_line=None):
    """Run argv under the limits of LIMITS[kind] with full process-tree cleanup. See the module docstring."""
    lim = LIMITS[kind]
    try:
        ctx = _setup_isolation()
    except OSError as e:
        raise IsolationFail(f"ISOLATION FAIL: {_isolation_name()} unavailable: {e}; the target was not started")
    isolation = _isolation_name()
    prior = _children_of_me()
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = _CREATE_SUSPENDED
    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE if stdin_bytes is not None
                                else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)
    except BaseException:
        if ctx is not None:
            ctx.close()
        raise
    try:
        if ctx is not None:
            try:
                ctx.assign(proc._handle)
            except OSError as e:
                proc.kill()                            # still suspended: it never ran a single instruction
                proc.wait()
                raise IsolationFail(f"ISOLATION FAIL: job: {e}; the target was not started")
            root_start = _start_of_handle(int(proc._handle))
            _resume_process(proc.pid)
        else:
            _NO_REAP.add(proc.pid)
            root_start = _start_time(proc.pid)
    except BaseException:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        if ctx is not None:
            ctx.close()
        raise
    return _supervise(proc, ctx, isolation, root_start, prior, lim, stdin_bytes, stdout_path, stderr_path,
                      proc_path, on_line)


def _supervise(proc, ctx, isolation, root_start, prior, lim, stdin_bytes, stdout_path, stderr_path, proc_path,
               on_line):
    run = _Run(proc.pid, root_start, ctx, isolation, popen=proc, prior_children=prior)
    started_at = _now()

    def save(extra=None):
        if proc_path:
            rec = run.record()
            rec["started_at"] = started_at
            rec.update(extra or {})
            _write_json(proc_path, rec)

    out = err = None
    completed = False
    try:
        save()
        over_event = threading.Event()
        out = _Reader(proc.stdout.fileno(), lim.stdout_max, stdout_path, over_event, on_line)
        err = _Reader(proc.stderr.fileno(), lim.stderr_max, stderr_path, over_event)
        out.start()
        err.start()
        if stdin_bytes is not None:
            def feed():
                try:
                    proc.stdin.write(stdin_bytes)
                    proc.stdin.close()
                except (OSError, ValueError):
                    pass
            threading.Thread(target=feed, daemon=True).start()

        t0 = time.monotonic()
        deadline, next_scan = t0 + lim.timeout, t0 + SCAN_INTERVAL
        timed_out = False
        while proc.poll() is None:
            if over_event.is_set():
                break
            now = time.monotonic()
            if now >= deadline:
                timed_out = True
                break
            if now >= next_scan:
                if run.scan():
                    save()
                next_scan = now + SCAN_INTERVAL
            over_event.wait(POLL)

        run.stop(lim, gentle=proc.poll() is None)
        try:
            proc.wait(timeout=1 if proc.poll() is None else None)
        except subprocess.TimeoutExpired:
            pass
        alive = run.verify()
        # every process holding our pipes is dead only if both pipes reach EOF; a pipe still open means some process
        # outside the registry and the ownership mechanism holds it: the cleanup cannot be confirmed
        eof_deadline = time.monotonic() + PIPE_EOF_WAIT
        for r in (out, err):
            r.join(timeout=max(0.0, eof_deadline - time.monotonic()))
        if out.is_alive() or err.is_alive():
            run.unconfirmed = True
        output_error = "; ".join(e for e in (out.write_error, err.write_error) if e) or None
        res = Limited(rc=proc.poll(), timed_out=timed_out, stdout_over=out.over, stderr_over=err.over,
                      stdout=bytes(out.buf), stderr=bytes(err.buf), stdout_bytes=len(out.buf),
                      stderr_bytes=len(err.buf), signals_sent=list(run.signals), killed_pids_alive=alive,
                      cleanup_unconfirmed=run.unconfirmed, registry=list(run.registry.items()), isolation=isolation,
                      output_error=output_error)
        save({"ended_at": _now(), "alive_after": alive, "cleanup_unconfirmed": run.unconfirmed,
              "output_error": output_error})
        completed = True
    finally:
        if not completed:
            _emergency_stop(run, lim, save)
        if ctx is not None:
            ctx.close()                                # KILL_ON_JOB_CLOSE: nothing outlives the job handle
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        for r, pipe in ((out, proc.stdout), (err, proc.stderr)):
            if r is not None:
                r.join(timeout=0.5 if ctx is not None else 0)
            if r is None or not r.is_alive():          # a reader still blocked on a pipe keeps it (daemon thread)
                pipe.close()
        if proc.stdin is not None and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except OSError:
                pass
        if proc.poll() is None:
            _SURVIVORS.append(proc)
        _NO_REAP.discard(proc.pid)
    if out is not None and out.error is not None:
        raise out.error
    return res


def _emergency_stop(run, lim, save):
    """The normal path raised (bad output path, proc record write failure, KeyboardInterrupt ...): force-stop the
    whole tree and verify before the exception propagates; record ended_at/alive_after when possible."""
    alive, unconfirmed = None, True
    try:
        run.scan()
        run.forced(lim.kill_wait)
        alive = run.verify()
        unconfirmed = run.unconfirmed
    except BaseException:
        pass
    try:
        save({"ended_at": _now(), "alive_after": alive if alive is not None else [run.root_pid],
              "cleanup_unconfirmed": unconfirmed, "aborted": True})
    except BaseException:
        pass


def still_alive(proc_record):
    """(alive pids, unconfirmed) for a lifecycle record: the root and every registry entry, same pid AND same start
    time. The second value is True when the process table could not be read for some entry."""
    entries = collections.OrderedDict([(proc_record["root_pid"], proc_record.get("root_start"))])
    for pid, start in proc_record.get("registry", []):
        entries.setdefault(int(pid), start)
    alive, unconfirmed = [], False
    _reap(list(entries.items()))
    for pid, start in entries.items():
        try:
            if _is_alive(int(pid), start):
                alive.append(int(pid))
        except OSError:
            unconfirmed = True
    return alive, unconfirmed


def cleanup(proc_record, kind):
    """The same two-stage cleanup as run_limited, for processes of an earlier run (from its lifecycle record)."""
    lim = LIMITS[kind]
    reg = [(proc_record["root_pid"], proc_record.get("root_start"))]
    reg += [(int(p), s) for p, s in proc_record.get("registry", []) if int(p) != proc_record["root_pid"]]
    run = _Run(proc_record["root_pid"], proc_record.get("root_start"), None,
               proc_record.get("isolation", ""), registry=reg)
    run.stop(lim, gentle=True)
    alive = run.verify()
    return Limited(rc=None, timed_out=False, stdout_over=False, stderr_over=False, stdout=b"", stderr=b"",
                   stdout_bytes=0, stderr_bytes=0, signals_sent=list(run.signals), killed_pids_alive=alive,
                   cleanup_unconfirmed=run.unconfirmed, registry=list(run.registry.items()),
                   isolation=run.isolation)
