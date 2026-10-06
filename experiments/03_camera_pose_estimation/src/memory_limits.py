"""Windows Job Object process-memory limits for tracking workers."""

import ctypes
import os


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_uint64)
        for name in (
            "ReadOperationCount",
            "WriteOperationCount",
            "OtherOperationCount",
            "ReadTransferCount",
            "WriteTransferCount",
            "OtherTransferCount",
        )
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _AssociateCompletionPort(ctypes.Structure):
    _fields_ = [("CompletionKey", ctypes.c_void_p), ("CompletionPort", ctypes.c_void_p)]


class WindowsProcessMemoryLimit:
    """A Windows Job Object with a hard per-process commit limit."""

    PROCESS_MEMORY_LIMIT = 0x100
    KILL_ON_JOB_CLOSE = 0x2000
    EXTENDED_LIMIT_INFORMATION = 9
    ASSOCIATE_COMPLETION_PORT_INFORMATION = 7
    PROCESS_MEMORY_LIMIT_MESSAGE = 9
    WAIT_TIMEOUT = 258

    def __init__(self, process_handle: int, limit_bytes: int) -> None:
        if os.name != "nt":
            raise OSError("Tracking resource limits require Windows Job Objects")
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.CreateJobObjectW.restype = ctypes.c_void_p
        self._kernel32.SetInformationJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
        ]
        self._kernel32.AssignProcessToJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        self._kernel32.QueryInformationJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        self._kernel32.CreateIoCompletionPort.restype = ctypes.c_void_p
        self._kernel32.CreateIoCompletionPort.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_uint32,
        ]
        self._kernel32.SetInformationJobObject.restype = ctypes.c_int
        self._kernel32.GetQueuedCompletionStatus.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_uint32,
        ]
        self._kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        self.completion_port = self._kernel32.CreateIoCompletionPort(
            ctypes.c_void_p(-1), None, 0, 1
        )
        if not self.completion_port:
            raise ctypes.WinError(ctypes.get_last_error())
        self.memory_limit_hit = False
        self.handle = self._kernel32.CreateJobObjectW(None, None)
        if not self.handle:
            self._kernel32.CloseHandle(self.completion_port)
            self.completion_port = None
            raise ctypes.WinError(ctypes.get_last_error())
        limits = _ExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = (
            self.PROCESS_MEMORY_LIMIT | self.KILL_ON_JOB_CLOSE
        )
        limits.ProcessMemoryLimit = limit_bytes
        success = self._kernel32.SetInformationJobObject(
            self.handle,
            self.EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        )
        if not success:
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())
        association = _AssociateCompletionPort(ctypes.c_void_p(1), self.completion_port)
        if not self._kernel32.SetInformationJobObject(
            self.handle,
            self.ASSOCIATE_COMPLETION_PORT_INFORMATION,
            ctypes.byref(association),
            ctypes.sizeof(association),
        ):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())
        if not self._kernel32.AssignProcessToJobObject(
            self.handle, ctypes.c_void_p(process_handle)
        ):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())

    def peak_process_memory(self) -> int | None:
        limits = _ExtendedLimitInformation()
        success = self._kernel32.QueryInformationJobObject(
            self.handle,
            self.EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
            None,
        )
        if not success:
            return None
        return int(limits.PeakProcessMemoryUsed)

    def poll_memory_limit(self) -> bool:
        """Read pending Job Object memory-limit messages without blocking."""
        bytes_transferred = ctypes.c_uint32()
        completion_key = ctypes.c_size_t()
        overlapped = ctypes.c_void_p()
        while self._kernel32.GetQueuedCompletionStatus(
            self.completion_port,
            ctypes.byref(bytes_transferred),
            ctypes.byref(completion_key),
            ctypes.byref(overlapped),
            0,
        ):
            if bytes_transferred.value == self.PROCESS_MEMORY_LIMIT_MESSAGE:
                self.memory_limit_hit = True
        error = ctypes.get_last_error()
        if error not in {0, self.WAIT_TIMEOUT}:
            raise ctypes.WinError(error)
        return self.memory_limit_hit

    def process_memory_limit(self) -> int | None:
        """Return the process limit configured on this exact Job Object."""
        limits = _ExtendedLimitInformation()
        success = self._kernel32.QueryInformationJobObject(
            self.handle,
            self.EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
            None,
        )
        if not success:
            raise ctypes.WinError(ctypes.get_last_error())
        if not limits.BasicLimitInformation.LimitFlags & self.PROCESS_MEMORY_LIMIT:
            return None
        return int(limits.ProcessMemoryLimit)

    @classmethod
    def current_process_memory_info(cls) -> tuple[int, int] | None:
        """Return the current Job Object process limit and peak commit bytes."""
        if os.name != "nt":
            return None
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        kernel32.IsProcessInJob.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
        ]
        in_job = ctypes.c_int()
        if (
            not kernel32.IsProcessInJob(
                kernel32.GetCurrentProcess(), None, ctypes.byref(in_job)
            )
            or not in_job.value
        ):
            return None
        kernel32.QueryInformationJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        limits = _ExtendedLimitInformation()
        if not kernel32.QueryInformationJobObject(
            None,
            cls.EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
            None,
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        flags = limits.BasicLimitInformation.LimitFlags
        if not flags & cls.PROCESS_MEMORY_LIMIT:
            return None
        return int(limits.ProcessMemoryLimit), int(limits.PeakProcessMemoryUsed)

    @classmethod
    def current_process_memory_limit(cls) -> int | None:
        """Return the current process Job Object limit, if one is applied."""
        info = cls.current_process_memory_info()
        return None if info is None else info[0]

    @classmethod
    def is_current_process_in_job(cls) -> bool:
        """Return whether the current process belongs to a Windows Job Object."""
        if os.name != "nt":
            return False
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        kernel32.IsProcessInJob.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
        ]
        in_job = ctypes.c_int()
        if not kernel32.IsProcessInJob(
            kernel32.GetCurrentProcess(), None, ctypes.byref(in_job)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return bool(in_job.value)

    def close(self) -> None:
        if getattr(self, "handle", None):
            self._kernel32.CloseHandle(self.handle)
            self.handle = None
        if getattr(self, "completion_port", None):
            self._kernel32.CloseHandle(self.completion_port)
            self.completion_port = None
