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
    Run token (cross-lifetime ownership, Codex BC1-02): the subreaper adoption belongs to the wrapper process and is
    lost when the wrapper dies. Each run therefore draws a random token (secrets.token_hex(16); no model identity, no
    secret), records it in the lifecycle record BEFORE Popen, and passes TOKEN_VAR=<token> in the target's environment.
    The environment is inherited by every descendant, also in a new session (grade.py builds its tool environments
    from os.environ, grade.py:597, 643). Any process, also a fresh one after the wrapper died, finds every process of
    the run by reading /proc/<pid>/environ of the processes started since the launch (launch_ticks). A process of
    this user whose environment cannot be read makes the result unconfirmed (other users' processes cannot carry the
    token unless a set-uid program was run, which the graded flow does not do), except when it lies outside the
    wrapper's cgroup v2 subtree recorded at launch ("cgroup"): every descendant inherits that cgroup, and cgroup v2
    lets an unprivileged process migrate only below a common ancestor whose cgroup.procs it may write (here a
    root-owned one). This exempts e.g. "systemd --user" and "(sd-pam)" (same uid, not dumpable after their credential
    change, in user@<uid>.service), which a new WSL session starts. Without cgroup v2 information ("0::/" or none)
    there is no exemption. This unreadable-process rule applies only after the wrapper is gone (still_alive, cleanup);
    while the wrapper lives, the subreaper adoption already brings every orphan back to it, so the live verification
    merges token matches but does not count unreadable processes (they would only be false alarms: ssh-agent,
    gpg-agent, sudo ... started by the user meanwhile in the same cgroup). The unreadable pids are reported
    (Limited.unreadable, still_alive(details=...)) so the author knows what to clear. boot_id: in another boot nothing
    of the run exists.
    Launch window (Codex BC3-01): a child between fork and exec does not carry the token yet (Popen returns only
    after exec succeeded). A record without the root identity (phase "launching": the wrapper died before the
    "running" save) therefore never counts as confirmed: still_alive / cleanup report it unconfirmed (cleanup still
    stops every token carrier it finds) and recovery stops, whatever the token scan finds.
    Stable snapshot (Codex BC3-02): a token scan that sees a listed process vanish during the pass (its stat or
    environment can no longer be read or reads as 0 bytes, as for a zombie or a task inside do_exit, a token carrier
    exits after its environment was read, a new zombie) is repeated from a fresh /proc listing, since a process forked
    by it before it exited is listed only by then; when SCAN_PASSES passes in a row see such a disappearance, the
    result is unconfirmed (still_alive, cleanup, verify). Kernel threads (PF_KTHREAD) are left out of the listing.
    Residual limits: (1) conservative, not unsafe: on a busy system unrelated processes started since the launch that
    exit during every pass, or a user process whose environment is really empty, make the result unconfirmed (a stop
    the author clears), never a false confirmation. (2) A /proc readdir is not an atomic snapshot: with pid
    wraparound during one listdir, a carrier whose pid the cursor has not reached yet can fork a child with a lower
    pid (already passed) and exit and be reaped before the cursor reaches it; neither then appears in that pass. The
    stable-scan rule narrows this window (the next pass lists the child) but does not eliminate it, since the same
    can happen in every pass; everywhere else the result direction stays conservative. (3) A
    migration mediated by PID 1 or by root (e.g. "systemd-run --user --scope", which asks the user manager to move
    the process into user@<uid>.service) can carry a descendant out of the launch cgroup; if it is then also unreadable
    it is not counted. The graded flow (grade.py and its tools) does neither.
  - Windows across lifetimes: the job is unnamed and its only handle belongs to the wrapper; when the wrapper process
    exits, the handle is closed and KILL_ON_JOB_CLOSE ends every member, registered or not. A fresh process cannot open
    the job, so it checks the root and the registry by pid AND start time and relies on that guarantee (recovery runs
    under the round lock, which first verifies that the previous holder exited). A record without the root identity
    (phase "launching": the wrapper died between Popen and AssignProcessToJobObject, leaving a suspended process
    outside any job) cannot be confirmed.
  - If the mechanism cannot be set up, IsolationFail ("ISOLATION FAIL ...") is raised and the target never runs.
Lifecycle record phases (proc_path; Codex BC1-01): "launching" (written before Popen: isolation, started_at and, on
Linux, token/launch_ticks/boot_id; no pid yet) -> Windows only: "pending_release" (root identity, the process is in the
job and still suspended; written before ResumeThread) -> "running" (written when supervision starts, then on every
registry change) -> ended_at/alive_after/cleanup_unconfirmed at the end (plus aborted/abort_error after a supervision
failure). "not_started": Popen failed, or the still suspended target was killed before release.
Failures: OSError / IsolationFail = the target never ran (Popen failed, or Windows: it was killed while still
suspended). SupervisionError = the target had started and supervising it failed (record or output file write, ...):
the tree was force-stopped first, and the error carries the pid identity, the cleanup result and the captured byte
counts.
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
import secrets
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
TOKEN_VAR = "CASE01_LIMITS_RUN_TOKEN"                 # Linux: environment variable carrying the run token
SCAN_PASSES = 5                                       # Linux: token scan passes until one sees no process vanish


class IsolationFail(RuntimeError):
    pass


class SupervisionError(RuntimeError):
    """The target had started (Linux: exec done; Windows: resumed) and supervising it failed. The whole tree was
    force-stopped and verified before this was raised. Not an OSError: callers must not take it for a launch failure.
    Fields: pid, root_start, isolation, rc (None while unknown), timed_out, signals_sent, killed_pids_alive,
    cleanup_unconfirmed, stdout_bytes, stderr_bytes, stdout_over, stderr_over, cause_type (class name of the
    original exception, which is also __cause__)."""

    def __init__(self, message, **fields):
        super().__init__(message)
        self.pid = fields.get("pid")
        self.root_start = fields.get("root_start")
        self.isolation = fields.get("isolation", "")
        self.rc = fields.get("rc")
        self.timed_out = bool(fields.get("timed_out"))
        self.signals_sent = list(fields.get("signals_sent") or [])
        self.killed_pids_alive = list(fields.get("killed_pids_alive") or [])
        self.cleanup_unconfirmed = bool(fields.get("cleanup_unconfirmed"))
        self.stdout_bytes = int(fields.get("stdout_bytes") or 0)
        self.stderr_bytes = int(fields.get("stderr_bytes") or 0)
        self.stdout_over = bool(fields.get("stdout_over"))
        self.stderr_over = bool(fields.get("stderr_over"))
        self.cause_type = fields.get("cause_type")


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
    unreadable: list = field(default_factory=list)    # recovery: pids of this user whose environment is unreadable
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

    def _prctl():
        """prctl with an explicit prototype: int prctl(int option, unsigned long arg2, unsigned long arg3,
        unsigned long arg4, unsigned long arg5) (the kernel ABI: every argument after option is an unsigned long;
        a pointer argument is passed as its address)."""
        fn = ctypes.CDLL(None, use_errno=True).prctl
        fn.restype = ctypes.c_int
        fn.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        return fn

    def _setup_isolation():
        """Make the calling process a child subreaper (raises OSError when that is impossible)."""
        if not os.path.isdir("/proc/self"):
            raise OSError("no /proc: the subreaper mechanism needs Linux")
        prctl = _prctl()
        if prctl(_PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
            err = ctypes.get_errno()
            raise OSError(err, f"prctl(PR_SET_CHILD_SUBREAPER) failed: {os.strerror(err)}")
        flag = ctypes.c_int(0)                         # read back: the kernel writes an int at the address
        if prctl(_PR_GET_CHILD_SUBREAPER, ctypes.addressof(flag), 0, 0, 0) != 0 or flag.value != 1:
            raise OSError("PR_SET_CHILD_SUBREAPER did not take effect")
        return None

    def _isolation_name():
        return "subreaper"

    _PF_KTHREAD = 0x00200000                           # task flag of kernel threads (include/linux/sched.h)

    def _stat(pid, flags=False):
        """(state, ppid, starttime) from /proc/<pid>/stat (with flags=True: plus the task flags as an int); None when
        the process does not exist."""
        try:
            with open(f"/proc/{pid}/stat", "rb") as f:
                data = f.read().decode("ascii", "replace")
        except (FileNotFoundError, ProcessLookupError):
            return None
        rest = data[data.rindex(")") + 2:].split()
        if flags:
            return rest[0], int(rest[1]), rest[19], int(rest[6])
        return rest[0], int(rest[1]), rest[19]

    def _start_time(pid):
        """Start time (clock ticks since boot, as a decimal string) of a running process; None when it does not
        exist or is a zombie (exited, not yet reaped)."""
        st = _stat(pid)
        if st is None or st[0] in ("Z", "X", "x"):
            return None
        return st[2]

    def _table_scan(listdir=None, stat=None):
        """({pid: (state, ppid, starttime)} for every process except kernel threads, {pids listed in /proc that
        vanished before their stat could be read}); raises OSError when /proc cannot be read. Kernel threads (task
        flag PF_KTHREAD; kthreadd and its children, e.g. kworkers) are left out: they never belong to a run and their
        empty environment would make every token scan pass repeat (BC3-02 fix 1). They are recognised by the flag,
        not by "parent pid 2": in WSL pid 2 is a user-space init whose children are ordinary processes.
        listdir / stat: injectable readers (tests); stat(pid, flags=True) like _stat."""
        listdir = listdir or os.listdir
        stat = stat or _stat
        out, vanished = {}, set()
        for name in listdir("/proc"):
            if name.isdigit():
                st = stat(int(name), flags=True)
                if st is None:
                    vanished.add(int(name))
                elif not st[3] & _PF_KTHREAD:
                    out[int(name)] = st[:3]
        return out, vanished

    def _table():
        """{pid: (state, ppid, starttime)} for every process; raises OSError when /proc cannot be read."""
        return _table_scan()[0]

    def _kill_pid(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def _resume_process(pid):
        pass

    def _read_environ(pid):
        with open(f"/proc/{pid}/environ", "rb") as f:
            return f.read()

    def _same_user(pid, uid):
        """True when the real or effective uid of pid is uid (also when that cannot be read: conservative)."""
        try:
            with open(f"/proc/{pid}/status", "rb") as f:
                for line in f.read().decode("ascii", "replace").splitlines():
                    if line.startswith("Uid:"):
                        return str(uid) in line.split()[1:3]
        except (FileNotFoundError, ProcessLookupError):
            return False
        except OSError:
            return True
        return True

    def _cgroup(pid):
        """cgroup v2 path of pid ("0::<path>" line of /proc/<pid>/cgroup), or None."""
        try:
            with open(f"/proc/{pid}/cgroup", "rb") as f:
                for line in f.read().decode("utf-8", "replace").splitlines():
                    if line.startswith("0::"):
                        return line[3:].strip() or None
        except OSError:
            return None
        return None

    def _outside(cg, launch_cg):
        """True when cgroup cg is known to lie outside the subtree of launch_cg (never when either is unknown or the
        launch cgroup is the root)."""
        if not cg or not launch_cg or launch_cg == "/":
            return False
        return cg != launch_cg and not cg.startswith(launch_cg.rstrip("/") + "/")

    def _token_scan(token, since, table, launch_cg=None, read_environ=None, start_time=None):
        """({pid: start} of the running processes whose environment holds TOKEN_VAR=token, [pids of this user whose
        environment could not be read], {pids that exited during the pass}) among the processes of `table` started at
        or after `since` clock ticks. An unreadable process outside the launch cgroup subtree (launch_cg) is not
        counted (module docstring). "Exited during the pass" (Codex BC3-02): the environment read failed with
        ENOENT/ESRCH, or a token carrier no longer runs with its listed start time after its environment was read; a
        process it forked before exiting may be missing from `table`. A zombie started since `since` is reported too
        (it may have forked before exiting, after the listing); _stable_token_scan accepts it once a later pass lists
        the same zombie again. read_environ / start_time: injectable readers (tests); default the /proc readers."""
        read_environ = read_environ or _read_environ
        start_time = start_time or _start_time
        needle = f"{TOKEN_VAR}={token}".encode("ascii")
        me, uid = os.getpid(), os.getuid()
        found, unreadable, vanished = {}, [], set()
        for pid, (state, _, start) in table.items():
            if pid == me:
                continue
            if since is not None and int(start) < int(since):
                continue
            if state in ("Z", "X", "x"):
                vanished.add(pid)
                continue
            try:
                data = read_environ(pid)
            except (FileNotFoundError, ProcessLookupError):
                vanished.add(pid)
                continue
            except OSError:
                if _same_user(pid, uid) and not _outside(_cgroup(pid), launch_cg):
                    unreadable.append(pid)
                continue
            if not data:
                # Linux gives 0 bytes (no error) for an unreaped zombie and for a task in do_exit after exit_mm (its
                # stat may still say R/D): it may have forked before exiting, so the pass is repeated (BC3-02 fix 1).
                # Kernel threads are not in the table (_table_scan); a user process whose environment is really
                # empty makes every pass repeat, so the result is unconfirmed (conservative)
                vanished.add(pid)
                continue
            if needle in data.split(b"\0"):
                if start_time(pid) == start:
                    found[pid] = start
                else:
                    vanished.add(pid)
        return found, unreadable, vanished

    def _stable_token_scan(token, since, launch_cg=None, listing=None, read_environ=None, start_time=None,
                           passes=None):
        """Token scan over a stable process snapshot (Codex BC3-02): (found, unreadable, table, stable). A pass in
        which a listed process vanished (its stat or environment could not be read any more: ENOENT/ESRCH), a token
        carrier exited after its environment was read, or a zombie appeared that the previous pass had not listed,
        is repeated from a fresh listing: a process forked by the vanished one before it exited is listed by then.
        stable is False when no pass out of `passes` (default SCAN_PASSES) was free of such disappearances; the
        caller must then count the result as unconfirmed. listing / read_environ / start_time: injectable readers
        (tests); listing returns (table, vanished pids) like _table_scan."""
        listing = listing or _table_scan
        passes = SCAN_PASSES if passes is None else passes
        zombies_before = set()
        found, unreadable, table = {}, [], {}
        for _ in range(passes):
            table, gone = listing()
            found, unreadable, vanished = _token_scan(token, since, table, launch_cg, read_environ, start_time)
            zombies = {(pid, table[pid][2]) for pid in vanished if pid in table and table[pid][0] in ("Z", "X", "x")}
            churn = set(gone) | {pid for pid in vanished if pid not in table or table[pid][0] not in ("Z", "X", "x")}
            if not churn and zombies <= zombies_before:
                return found, unreadable, table, True
            zombies_before = zombies
        return found, unreadable, table, False

    def _boot_id():
        try:
            with open("/proc/sys/kernel/random/boot_id", "rb") as f:
                return f.read().decode("ascii", "replace").strip() or None
        except OSError:
            return None

    def _thread_ticks():
        """Start time (clock ticks since boot) of a thread created now: the same clock as the start times of the
        processes created after it."""
        box = {}

        def probe():
            try:
                with open(f"/proc/self/task/{threading.get_native_id()}/stat", "rb") as f:
                    data = f.read().decode("ascii", "replace")
                box["t"] = int(data[data.rindex(")") + 2:].split()[19])
            except (OSError, ValueError, IndexError) as e:
                box["e"] = e
        th = threading.Thread(target=probe)
        th.start()
        th.join()
        if "t" not in box:
            raise OSError(f"cannot read the current clock tick: {box.get('e')}")
        return box["t"]

    def _launch_marks():
        """Ownership marks of one run, recorded before Popen: token, launch_ticks (1 s margin before now), boot_id,
        cgroup (cgroup v2 path of the wrapper, inherited by the target)."""
        return {"token": secrets.token_hex(16),
                "launch_ticks": max(0, _thread_ticks() - os.sysconf("SC_CLK_TCK")), "boot_id": _boot_id(),
                "cgroup": _cgroup("self")}


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

    def __init__(self, root_pid, root_start, ctx, isolation, popen=None, registry=None, prior_children=(),
                 token=None, since=None, cgroup=None):
        self.root_pid, self.root_start, self.ctx, self.isolation, self.popen = root_pid, root_start, ctx, \
            isolation, popen
        self.token, self.since, self.cgroup = (token, since, cgroup) if os.name != "nt" else (None, None, None)
        if registry is None:
            registry = [(root_pid, root_start)] if root_pid is not None else []
        self.registry = collections.OrderedDict(registry)
        self.prior_children = set(prior_children)
        self.signals = []
        self.unconfirmed = False
        self.unreadable = []
        self.timed_out = False
        self.on_signal = None                         # called after a signal is recorded and BEFORE it is sent

    def _note_signal(self, text):
        self.signals.append(text)
        if self.on_signal is not None:
            self.on_signal()

    def root_alive(self):
        """Root still running: the Popen object (when we own it) or the process table, pid AND start time."""
        if self.popen is not None and self.popen.poll() is None:
            return True
        if self.root_pid is None:
            return False
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
            if start is not None and self.registry.get(pid) is None:     # new, or an entry without a start time
                self.registry[pid] = start
                changed = True
                if pid == self.root_pid and self.root_start is None and self.popen is None:
                    self.root_start = start
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
        if self.token:                                 # every process carrying the run token is ours
            # registration only (single pass): the verdict comes from verify(), which uses a stable snapshot
            found = _token_scan(self.token, self.since, table, self.cgroup)[0]
            seeds.update(found)
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
        text = f"SIGTERM {self.root_pid}"
        self._note_signal(text)
        try:
            os.kill(self.root_pid, signal.SIGTERM)
        except ProcessLookupError:
            self.signals.remove(text)                 # not sent: the root had already gone
            if self.on_signal is not None:
                self.on_signal()
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
            if first:
                if self.ctx is not None:
                    self._note_signal("TerminateJobObject")
                else:
                    name = "TerminateProcess" if os.name == "nt" else "SIGKILL"
                    self._note_signal(name + " " + " ".join(str(p) for p in alive))
                first = False
            try:
                _force_kill(self.ctx, alive)
            except OSError:
                pass
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
        if self.token:                                 # Linux: unregistered processes carrying the run token
            try:
                found, unreadable, _, stable = _stable_token_scan(self.token, self.since, self.cgroup)
            except OSError:
                found, unreadable, stable = {}, [], True
                self.unconfirmed = True
            if not stable:                             # the process set kept changing during the scan (BC3-02)
                self.unconfirmed = True
            alive += [p for p in found if p not in alive]
            if unreadable and self.popen is None:      # only once the wrapper (and its subreaper role) is gone
                self.unreadable = sorted(set(self.unreadable) | set(unreadable))
                self.unconfirmed = True
        return sorted(set(p for p in alive if p is not None))

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
                proc_path=None, on_line=None, proc_extra=None):
    """Run argv under the limits of LIMITS[kind] with full process-tree cleanup. See the module docstring.
    Lifecycle record (proc_path): written before Popen (phase "launching"), on Windows again before the suspended
    target is resumed (phase "pending_release", with the root identity), then from the start of supervision (phase
    "running") every save holds root_pid, root_start, registry, isolation, started_at, signals_sent and timed_out (and on
    Linux token, launch_ticks, boot_id); a signal is recorded (and the record saved) before it is sent, timed_out as
    soon as the time limit is reached. proc_extra: a dict owned by the caller whose items are added to every save (the
    record's own keys win); the caller may set keys in it from on_line and request a save by returning True from
    on_line. The save itself is done by the supervising thread at its next poll (within POLL seconds), never on the
    reader thread: the registry and the signal list are only ever touched by the supervising thread.
    Raises IsolationFail / OSError when the target never ran, SupervisionError when it had started (see the module
    docstring)."""
    lim = LIMITS[kind]
    try:
        ctx = _setup_isolation()
        marks = _launch_marks() if os.name != "nt" else {}
    except OSError as e:
        raise IsolationFail(f"ISOLATION FAIL: {_isolation_name()} unavailable: {e}; the target was not started")
    isolation = _isolation_name()
    started_at = _now()
    child_env = env
    if marks:                                         # the run token travels in the target's environment only
        child_env = dict(os.environ if env is None else env)
        child_env[TOKEN_VAR] = marks["token"]
    base = dict(proc_extra or {})
    # no signals_sent / timed_out before supervision starts (R13: unknown = no evidence); the wrapper's own identity
    # lets the author find a suspended orphan left by a crash between Popen and the job (Windows)
    base.update(isolation=isolation, started_at=started_at, wrapper_pid=os.getpid(),
                wrapper_start=_start_time(os.getpid()), **marks)

    def pre_save(**fields):
        if proc_path:
            _write_json(proc_path, dict(base, **fields))

    def not_started(err):                             # best effort: the record says that nothing ran
        try:
            pre_save(phase="not_started", ended_at=_now(), alive_after=[], cleanup_unconfirmed=False,
                     launch_error={"type": type(err).__name__, "errno": getattr(err, "errno", None)})
        except Exception:
            pass

    try:
        pre_save(phase="launching")                   # before the target can exist: a failure here starts nothing
    except BaseException:
        if ctx is not None:
            ctx.close()
        raise
    prior = _children_of_me()
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = _CREATE_SUSPENDED
    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=child_env, stdin=subprocess.PIPE if stdin_bytes is not None
                                else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)
    except BaseException as e:
        if ctx is not None:
            ctx.close()
        not_started(e)
        raise
    if ctx is not None:
        # Windows: the target is suspended; until ResumeThread it has not run a single instruction, so every failure
        # in this block is a launch failure (the target is killed while still suspended)
        try:
            try:
                ctx.assign(proc._handle)
            except OSError as e:
                raise IsolationFail(f"ISOLATION FAIL: job: {e}; the target was not started") from None
            root_start = _start_of_handle(int(proc._handle))
            pre_save(phase="pending_release", root_pid=proc.pid, root_start=root_start,
                     registry=[[proc.pid, root_start]])
            _resume_process(proc.pid)
        except BaseException as e:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            ctx.close()
            for pipe in (proc.stdout, proc.stderr, proc.stdin):
                if pipe is not None:
                    pipe.close()
            not_started(e)
            raise
    else:
        # Linux: Popen returned, so the target has exec'd and carries the run token; from here on every failure is
        # a supervision failure
        _NO_REAP.add(proc.pid)
        try:
            root_start = _start_time(proc.pid)
        except OSError:
            root_start = None                         # the Popen object and the run token still identify the run
    return _supervise(proc, ctx, isolation, root_start, prior, lim, stdin_bytes, stdout_path, stderr_path,
                      proc_path, on_line, proc_extra, started_at, marks)


def _supervise(proc, ctx, isolation, root_start, prior, lim, stdin_bytes, stdout_path, stderr_path, proc_path,
               on_line, proc_extra=None, started_at=None, marks=None):
    marks = marks or {}
    run = _Run(proc.pid, root_start, ctx, isolation, popen=proc, prior_children=prior, token=marks.get("token"),
               since=marks.get("launch_ticks"), cgroup=marks.get("cgroup"))
    started_at = started_at or _now()
    save_requested = threading.Event()               # set by the stdout reader (on_line), acted on by this thread

    def save(extra=None):
        if proc_path:
            save_requested.clear()
            rec = dict(proc_extra or {})
            rec.update(run.record())
            rec.update(marks)
            rec["phase"] = "running"
            rec["started_at"] = started_at
            rec["signals_sent"] = list(run.signals)
            rec["timed_out"] = run.timed_out
            rec.update(extra or {})
            _write_json(proc_path, rec)

    def save_quietly():                               # a failed save never prevents a signal from being sent
        try:
            save()
        except Exception:
            pass

    run.on_signal = save_quietly
    if on_line is not None:
        user_on_line = on_line

        def on_line(line):                            # runs on the stdout reader thread: only flags the save
            if user_on_line(line) is True:
                save_requested.set()

    out = err = None
    completed = False
    failure = None                                    # (exception, (alive, unconfirmed)) of a supervision failure
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
                run.timed_out = True
                save_quietly()
                break
            if now >= next_scan:
                if run.scan():
                    save()
                next_scan = now + SCAN_INTERVAL
            if save_requested.is_set():
                save()
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
    except Exception as exc:                          # supervision failed after the target had started
        failure = (exc, _emergency_stop(run, lim, save, exc))
    finally:
        if not completed and failure is None:         # KeyboardInterrupt, SystemExit ...: stop, then propagate
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
    if failure is not None:
        exc, (alive, unconfirmed) = failure
        raise _supervision_error(exc, proc, run, out, err, alive, unconfirmed) from exc
    if out is not None and out.error is not None:
        if isinstance(out.error, Exception):          # on_line failed: the run was stopped and verified normally
            raise _supervision_error(out.error, proc, run, out, err, res.killed_pids_alive,
                                     res.cleanup_unconfirmed) from out.error
        raise out.error
    return res


def _supervision_error(exc, proc, run, out, err, alive, unconfirmed):
    return SupervisionError(
        f"supervision of pid {proc.pid} failed after it had started: {exc.__class__.__name__}: {exc}; "
        f"the tree was force-stopped (alive after: {alive}, unconfirmed: {unconfirmed})",
        pid=proc.pid, root_start=run.root_start, isolation=run.isolation, rc=proc.poll(), timed_out=run.timed_out,
        signals_sent=list(run.signals), killed_pids_alive=alive, cleanup_unconfirmed=unconfirmed,
        stdout_bytes=len(out.buf) if out is not None else 0, stderr_bytes=len(err.buf) if err is not None else 0,
        stdout_over=bool(out is not None and out.over), stderr_over=bool(err is not None and err.over),
        cause_type=exc.__class__.__name__)


def _emergency_stop(run, lim, save, exc=None):
    """The normal path raised (bad output path, proc record write failure, KeyboardInterrupt ...): force-stop the
    whole tree and verify before the exception propagates; record ended_at/alive_after when possible. Returns
    (alive pids, unconfirmed); a failed verification counts as the root alive and unconfirmed."""
    alive, unconfirmed = None, True
    try:
        run.scan()
        run.forced(lim.kill_wait)
        alive = run.verify()
        unconfirmed = run.unconfirmed
    except BaseException:
        pass
    if alive is None:
        alive = [run.root_pid] if run.root_pid is not None else []
    try:
        save({"ended_at": _now(), "alive_after": alive, "cleanup_unconfirmed": unconfirmed, "aborted": True,
              "abort_error": exc.__class__.__name__ if exc is not None else "interrupted"})
    except BaseException:
        pass
    return alive, unconfirmed


def record_cleanup_failed(proc_record):
    """True when a lifecycle record itself says that its run's cleanup failed or could not be confirmed (KILL FAIL):
    alive_after not empty or cleanup_unconfirmed true. Recovery must stop on it."""
    return bool(proc_record.get("alive_after")) or proc_record.get("cleanup_unconfirmed") is True


def _ended_normally(rec):
    return "ended_at" in rec and rec.get("alive_after") == [] and rec.get("cleanup_unconfirmed") is False \
        and not rec.get("aborted")


def _other_boot(rec):
    """Linux: the record was written in another boot (then none of its processes can exist)."""
    if os.name == "nt" or not rec.get("boot_id"):
        return False
    now = _boot_id()
    return now is not None and now != rec["boot_id"]


def _record_view(rec):
    """(root_pid or None, entries {pid: start or None}, token or None, problem: True when the record cannot prove
    anything about its run)."""
    root = rec.get("root_pid")
    root = int(root) if root is not None else None
    entries = collections.OrderedDict()
    if root is not None:
        entries[root] = rec.get("root_start") or None
    for pid, start in rec.get("registry") or []:
        entries.setdefault(int(pid), start or None)
    token = rec.get("token") if rec.get("isolation") == "subreaper" else None
    problem = False
    if not token:
        # without a run token only the recorded identities can be checked: a missing root identity, or (Linux) a run
        # that did not end normally (unregistered orphans lost their subreaper with the wrapper) proves nothing
        if root is None or entries[root] is None:
            problem = True
        if rec.get("isolation") == "subreaper" and not _ended_normally(rec):
            problem = True
    elif root is None:
        # Codex BC3-01: a Linux record without the root identity ("launching": the wrapper died around Popen). The
        # child may still be between fork and exec, with the wrapper's environment and no run token yet; a token
        # scan that finds nothing cannot prove that the launch window is empty
        problem = True
    return root, entries, token, problem


def still_alive(proc_record, details=None):
    """(alive pids, unconfirmed) for a lifecycle record: the root and every registry entry, same pid AND same start
    time; on Linux also every process carrying the record's run token. The second value is True when the process
    table could not be read for some entry, an environment of this user could not be read, or the record cannot prove
    anything (no root identity; a Linux record without token of a run that did not end normally), or (Linux) the
    token scan saw no stable process snapshot within SCAN_PASSES passes.
    details: an optional dict that receives "unreadable" (pids whose environment could not be read)."""
    if proc_record.get("phase") == "not_started":
        return [], False
    if _other_boot(proc_record):
        return [], False
    root, entries, token, unconfirmed = _record_view(proc_record)
    alive = []
    _reap([(p, s) for p, s in entries.items() if s is not None])
    for pid, start in entries.items():
        if start is None:
            continue
        try:
            if _is_alive(pid, start):
                alive.append(pid)
        except OSError:
            unconfirmed = True
    if token:
        if os.name == "nt":
            unconfirmed = True
        else:
            try:
                found, unreadable, _, stable = _stable_token_scan(token, proc_record.get("launch_ticks"),
                                                                  proc_record.get("cgroup"))
                alive += [p for p in found if p not in alive]
                unconfirmed = unconfirmed or bool(unreadable) or not stable
                if details is not None:
                    details["unreadable"] = list(unreadable)
            except OSError:
                unconfirmed = True
    return alive, unconfirmed


def _gentle_top_carriers(run, token, proc_record, wait):
    """No root identity (a "launching" record): SIGTERM the top-level token carriers (whose parent does not carry the
    token; normally the root), recorded before sending, then wait like the gentle stage of run_limited."""
    try:
        found, _, table, stable = _stable_token_scan(token, proc_record.get("launch_ticks"), proc_record.get("cgroup"))
    except OSError:
        run.unconfirmed = True
        return
    if not stable:
        run.unconfirmed = True
    tops = sorted(p for p in found if table[p][1] not in found)
    sent = False
    for pid in tops:
        text = f"SIGTERM {pid}"
        run.signals.append(text)
        try:
            os.kill(pid, signal.SIGTERM)
            sent = True
        except ProcessLookupError:
            run.signals.remove(text)
    if sent:
        run._wait_gone(wait)


def cleanup(proc_record, kind):
    """The same two-stage cleanup as run_limited, for processes of an earlier run (from its lifecycle record); on
    Linux also every process carrying the record's run token."""
    lim = LIMITS[kind]
    root, entries, token, problem = _record_view(proc_record)
    if proc_record.get("phase") == "not_started" or _other_boot(proc_record):
        return Limited(rc=None, timed_out=False, stdout_over=False, stderr_over=False, stdout=b"", stderr=b"",
                       stdout_bytes=0, stderr_bytes=0, isolation=proc_record.get("isolation", ""))
    reg = [(p, s) for p, s in entries.items() if s is not None or p == root]
    run = _Run(root, entries.get(root) if root is not None else None, None, proc_record.get("isolation", ""),
               registry=reg, token=token, since=proc_record.get("launch_ticks"), cgroup=proc_record.get("cgroup"))
    if root is None and token and os.name != "nt":
        _gentle_top_carriers(run, token, proc_record, lim.term_wait)
    run.stop(lim, gentle=True)
    alive = run.verify()
    unconfirmed = run.unconfirmed or problem or bool(token and os.name == "nt")
    return Limited(rc=None, timed_out=False, stdout_over=False, stderr_over=False, stdout=b"", stderr=b"",
                   stdout_bytes=0, stderr_bytes=0, signals_sent=list(run.signals), killed_pids_alive=alive,
                   cleanup_unconfirmed=unconfirmed, registry=list(run.registry.items()),
                   isolation=run.isolation, unreadable=list(run.unreadable))
