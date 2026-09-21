"""Launch the local API pinned to a single worker. (Faz 4 packaging.)

Single entrypoint for running the server: workspace preflight first, then
uvicorn with localhost binding and exactly one worker. There is deliberately
no flag to raise the worker count: in-memory state forbids multi-worker.
"""

import subprocess
import sys
from pathlib import Path

from check_workspace import ROOT, check


def build_command(port: int) -> list[str]:
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("Port must be an integer 1..65535")
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "dcabot.server.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]


def preflight() -> None:
    report = check()
    if report["errors"]:
        raise ValueError(f"Workspace preflight failed: {report['errors']}")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    try:
        command = build_command(args.port)
        preflight()
    except ValueError as exc:
        print(f"Cannot start API: {exc}", file=sys.stderr)
        return 2
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(ROOT / "src") + (
        f";{env['PYTHONPATH']}" if env.get("PYTHONPATH") else ""
    )
    completed = subprocess.run(command, cwd=ROOT, env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
