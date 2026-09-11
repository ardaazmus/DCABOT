"""Check actual scaffold boundaries; no simulated trading success claims."""

import tempfile
import unittest
from pathlib import Path

from dcabot.bootstrap import describe_bootstrap
from check_workspace import active_python_files


class BootstrapTests(unittest.TestCase):
    def test_offline_core_never_enables_live_trading(self):
        result = describe_bootstrap({"mode": "offline"})
        self.assertEqual(result["stage"], "OFFLINE_CORE")
        self.assertFalse(result["trading_enabled"])
        self.assertTrue(result["strategy_implemented"])

    def test_other_modes_cannot_enable_trading(self):
        for mode in ("testnet", "mainnet", "read_only", "OFFLINE", None, True):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                describe_bootstrap({"mode": mode})

    def test_unrecognized_fields_are_rejected(self):
        for config in (
            {},
            {"mode": "offline", "api_key": "fixture"},
            {"mode": "offline", "trading_enabled": True},
        ):
            with self.subTest(config=config), self.assertRaises(ValueError):
                describe_bootstrap(config)

    def test_file_discovery_does_not_visit_backup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("src", "tests", "tools", "YEDEK_ESKI_PROJE"):
                (root / name).mkdir()
            (root / "src/current.py").write_text("x = 1")
            (root / "YEDEK_ESKI_PROJE/test_poison.py").write_text(
                "raise RuntimeError('legacy executed')"
            )
            self.assertEqual(
                [p.relative_to(root).as_posix() for p in active_python_files(root)],
                ["src/current.py"],
            )

    def test_active_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("src", "tests", "tools", "YEDEK_ESKI_PROJE"):
                (root / name).mkdir()
            try:
                (root / "src/legacy").symlink_to(
                    root / "YEDEK_ESKI_PROJE", target_is_directory=True
                )
            except OSError:
                self.skipTest("Symlink creation not available on this host")
            with self.assertRaises(ValueError):
                active_python_files(root)
