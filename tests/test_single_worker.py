import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_workspace import ROOT
from dcabot.application.single_worker import (
    SingleWorkerBusy,
    SingleWorkerGuard,
)


def _read_holder(lock: Path) -> int | None:
    try:
        return int(json.loads(lock.with_suffix(".pid").read_text(encoding="utf-8"))["pid"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


class SingleWorkerGuardTests(unittest.TestCase):
    def test_acquire_records_holder_and_release_allows_reacquire(self):
        with tempfile.TemporaryDirectory() as td:
            lock = Path(td) / "api.lock"
            with SingleWorkerGuard(lock):
                self.assertEqual(_read_holder(lock), os.getpid())
            with SingleWorkerGuard(lock):
                self.assertEqual(_read_holder(lock), os.getpid())

    def test_second_process_is_rejected_while_first_holds(self):
        script = (
            "import sys\n"
            "from pathlib import Path\n"
            "from dcabot.application.single_worker import SingleWorkerGuard, SingleWorkerBusy\n"
            "try:\n"
            "    SingleWorkerGuard(Path(sys.argv[1])).acquire()\n"
            "except SingleWorkerBusy as exc:\n"
            "    print(exc.holder_pid)\n"
            "    raise SystemExit(3)"
        )
        with tempfile.TemporaryDirectory() as td:
            lock = Path(td) / "api.lock"
            with SingleWorkerGuard(lock):
                env = dict(os.environ)
                env["PYTHONPATH"] = str(ROOT / "src")
                result = subprocess.run(
                    [sys.executable, "-c", script, str(lock)],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 3, result.stderr)
                self.assertEqual(result.stdout.strip(), str(os.getpid()))

    def test_stale_pid_marker_without_live_holder_is_taken_over(self):
        with tempfile.TemporaryDirectory() as td:
            lock = Path(td) / "api.lock"
            lock.with_suffix(".pid").write_text(
                json.dumps({"pid": 999999999}), encoding="utf-8"
            )
            with SingleWorkerGuard(lock):
                self.assertEqual(_read_holder(lock), os.getpid())

    def test_backup_or_linked_lock_path_rejected(self):
        with self.assertRaises(ValueError):
            SingleWorkerGuard(ROOT / "YEDEK_ESKI_PROJE" / "api.lock")
