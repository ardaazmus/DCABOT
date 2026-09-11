"""Offline bootstrap only. There is no venue or strategy implementation."""

import argparse
import json
import sys
from pathlib import Path

from check_workspace import ROOT, active_python_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/offline.json")
    args = parser.parse_args()
    try:
        active_python_files(ROOT)
        if any("YEDEK_ESKI_PROJE" in Path(p).parts for p in sys.path):
            raise ValueError("Legacy path in interpreter search path")
        config_path = args.config.resolve()
        if "YEDEK_ESKI_PROJE" in config_path.parts:
            raise ValueError("Legacy runtime config is not allowed")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("Config must be a JSON object")
        sys.path.insert(0, str(ROOT / "src"))
        from dcabot.bootstrap import describe_bootstrap

        result = describe_bootstrap(config)
    except (OSError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
