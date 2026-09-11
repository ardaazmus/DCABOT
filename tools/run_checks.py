"""Run only the new project's tests, without discovering the backup."""

import sys
import unittest
from pathlib import Path

from check_workspace import ROOT, check


def main() -> int:
    report = check()
    if report["errors"]:
        print(report, file=sys.stderr)
        return 1
    if any("YEDEK_ESKI_PROJE" in Path(p).parts for p in sys.path):
        print("Legacy path in interpreter search path", file=sys.stderr)
        return 1
    sys.path.insert(0, str(ROOT / "src"))
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_*.py"
    )
    return not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()


if __name__ == "__main__":
    raise SystemExit(main())
