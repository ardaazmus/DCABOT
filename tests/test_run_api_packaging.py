import unittest
from unittest import mock

import run_api


class RunApiPackagingTests(unittest.TestCase):
    def test_command_pins_localhost_single_worker(self):
        command = run_api.build_command(8000)

        self.assertIn("dcabot.server.api:app", command)
        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")
        self.assertEqual(command[command.index("--port") + 1], "8000")
        self.assertNotIn("--workers", command)

    def test_invalid_port_rejected(self):
        for bad in (0, 65536, -1, "8000", True, None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                run_api.build_command(bad)

    def test_preflight_failure_blocks_start(self):
        with mock.patch.object(run_api, "check", return_value={"errors": ["boom"]}):
            with self.assertRaises(ValueError):
                run_api.preflight()
            self.assertEqual(run_api.main(["--port", "8129"]), 2)

    def test_preflight_success_starts_server_command(self):
        with (
            mock.patch.object(run_api, "check", return_value={"errors": []}),
            mock.patch.object(run_api.subprocess, "run") as run,
        ):
            run.return_value.returncode = 0
            self.assertEqual(run_api.main(["--port", "8129"]), 0)
            command = run.call_args[0][0]
            self.assertEqual(command[command.index("--port") + 1], "8129")
