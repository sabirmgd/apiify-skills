#!/usr/bin/env python3
"""Check whether Apiify can run in this environment."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys


failures: list[str] = []
warnings: list[str] = []


def ok(message: str) -> None:
    print(f"PASS {message}")


def warn(message: str) -> None:
    warnings.append(message)
    print(f"WARN {message}")


def fail(message: str) -> None:
    failures.append(message)
    print(f"FAIL {message}")


def check_python() -> None:
    version = sys.version_info
    if version >= (3, 10):
        ok(f"Python {version.major}.{version.minor}.{version.micro}")
    else:
        fail("Python 3.10+ is required")


def check_python_package(name: str) -> None:
    if importlib.util.find_spec(name):
        ok(f"Python package available: {name}")
    else:
        fail(f"Missing Python package: {name}")


def run_version(binary: str, args: list[str]) -> None:
    path = shutil.which(binary)
    if not path:
        fail(f"Missing executable: {binary}")
        return
    try:
        proc = subprocess.run(
            [binary, *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        fail(f"{binary} exists but could not run: {exc}")
        return

    first_line = (proc.stdout or "").strip().splitlines()
    detail = first_line[0] if first_line else path
    if proc.returncode == 0:
        ok(f"{binary}: {detail}")
    else:
        warn(f"{binary} returned exit {proc.returncode}: {detail}")


def main() -> None:
    check_python()
    check_python_package("requests")
    check_python_package("dotenv")
    run_version("agent-browser", ["--version"])

    if not shutil.which("npm"):
        warn("npm not found; bootstrap cannot install agent-browser through npm")
    else:
        run_version("npm", ["--version"])

    if failures:
        print()
        print("Apiify is not ready. Run:")
        print("  python3 scripts/bootstrap.py --user")
        raise SystemExit(1)

    if warnings:
        print()
        print("Apiify is usable, but warnings should be reviewed.")
    else:
        print()
        print("Apiify environment looks ready.")


if __name__ == "__main__":
    main()

