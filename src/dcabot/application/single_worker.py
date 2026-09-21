"""Single-worker enforcement for the local API process.

The API keeps mutable in-memory state (sessions, jobs, executions), so two
workers would silently diverge. The guard holds an OS-level exclusive,
non-blocking lock on a lock file for the process lifetime; a second worker
fails fast instead of running with a split brain. The OS releases the lock
on process death, so no stale lock can block a restart.
"""

import json
import os
from pathlib import Path
from typing import BinaryIO

try:
    import fcntl

    _HAVE_FCNTL = True
except ImportError:  # Windows
    fcntl = None  # type: ignore[assignment]
    _HAVE_FCNTL = False

try:
    import msvcrt

    _HAVE_MSVCRT = True
except ImportError:  # POSIX
    msvcrt = None  # type: ignore[assignment]
    _HAVE_MSVCRT = False


class SingleWorkerBusy(ValueError):
    """Raised when another live process already holds the worker lock."""

    def __init__(self, holder_pid: int | None):
        self.holder_pid = holder_pid
        super().__init__(
            f"Another API worker already holds the lock (pid={holder_pid}); "
            "multi-worker deployment is out of scope"
        )


def pid_path_for(lock_path: Path) -> Path:
    return lock_path.with_suffix(".pid")


def _read_holder_pid(lock_path: Path) -> int | None:
    try:
        payload = json.loads(pid_path_for(lock_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    pid = payload.get("pid") if isinstance(payload, dict) else None
    return pid if isinstance(pid, int) and pid > 0 else None


class SingleWorkerGuard:
    """Hold the single-worker lock from acquire() until release()/close."""

    def __init__(self, lock_path: Path | str):
        path = Path(lock_path)
        if "YEDEK_ESKI_PROJE" in path.resolve().parts or any(
            p.is_symlink() or p.is_junction() for p in (path, *path.parents)
        ):
            raise ValueError("Worker lock must not use backup or linked paths")
        self._path = path
        self._handle: BinaryIO | None = None

    @property
    def path(self) -> Path:
        return self._path

    def acquire(self) -> "SingleWorkerGuard":
        if self._handle is not None:
            return self
        self._path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self._path, "a+b")
        try:
            if _HAVE_FCNTL:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif _HAVE_MSVCRT:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:  # pragma: no cover - every supported platform has one
                raise SingleWorkerBusy(_read_holder_pid(self._path))
        except OSError:
            handle.close()
            raise SingleWorkerBusy(_read_holder_pid(self._path)) from None
        pid_path_for(self._path).write_text(
            json.dumps({"pid": os.getpid()}), encoding="utf-8"
        )
        self._handle = handle
        return self

    def release(self) -> None:
        handle, self._handle = self._handle, None
        if handle is None:
            return
        # Remove the pid marker BEFORE unlocking: a concurrent acquirer can
        # only proceed after our unlock, so it never loses its own marker.
        try:
            pid_path_for(self._path).unlink(missing_ok=True)
        except OSError:
            pass
        try:
            if _HAVE_FCNTL:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif _HAVE_MSVCRT:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            handle.close()

    def __enter__(self) -> "SingleWorkerGuard":
        return self.acquire()

    def __exit__(self, *_: object) -> None:
        self.release()
