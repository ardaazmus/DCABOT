"""DCABOT_DATA_DIR moves every piece of mutable state (e2e isolation).

Found 2026-09-24: e2e runs wrote real backups, archived bots and kill-switch
toggles into the operator's data/ folder; after 25 backups a paginated list
made a backup test fail on every run. Paths are fixed at import, so each
case runs in a fresh interpreter.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = """
import json
from dcabot.server import api
print(json.dumps({name: str(getattr(api, name)) for name in (
    "DATA_DIR", "BACKUPS_DIR", "BOTS_V2_PATH", "KLINE_CACHE_PATH", "KILL_SWITCH_PATH",
    "HISTORICAL_RUNS_PATH", "DATASET_CACHE_DIR", "WORKER_LOCK_PATH", "TESTNET_DCA_SESSIONS_PATH", "DEALS_DIR")}))
"""


def _probe(data_dir: str | None) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    env.pop("DCABOT_DATA_DIR", None)
    if data_dir is not None:
        env["DCABOT_DATA_DIR"] = data_dir
    return subprocess.run([sys.executable, "-c", PROBE], capture_output=True, text=True, env=env, cwd=ROOT, timeout=120)


class DataDirOverrideTests(unittest.TestCase):
    def test_every_state_path_moves_under_the_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _probe(tmp)
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            paths = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertEqual(Path(paths.pop("DATA_DIR")), Path(tmp))
            for name, value in paths.items():
                with self.subTest(name=name):
                    self.assertTrue(Path(value).is_relative_to(Path(tmp)), value)

    def test_default_is_the_repository_data_folder(self):
        result = _probe(None)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertEqual(Path(json.loads(result.stdout.strip().splitlines()[-1])["DATA_DIR"]), ROOT / "data")

    def test_relative_override_is_rejected(self):
        result = _probe("relative/data")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DCABOT_DATA_DIR must be an absolute path", result.stderr)


if __name__ == "__main__":
    unittest.main()
