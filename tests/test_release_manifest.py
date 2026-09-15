import unittest

from release_manifest import check


class ReleaseManifestTests(unittest.TestCase):
    def test_tracked_release_manifest_is_complete_and_current(self):
        report = check()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["tracked_files"], report["manifest_entries"] + 1)


if __name__ == "__main__":
    unittest.main()
