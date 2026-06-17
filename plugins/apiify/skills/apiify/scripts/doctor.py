#!/usr/bin/env python3
"""Check whether Apiify can run in this environment."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys


EXPECTED_AGENT_BROWSER_VERSION = os.environ.get("APIIFY_AGENT_BROWSER_VERSION", "0.15.1")
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


def command_output(binary: str, args: list[str]) -> tuple[int, str] | None:
    path = shutil.which(binary)
    if not path:
        fail(f"Missing executable: {binary}")
        return None
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
        return None

    return proc.returncode, proc.stdout or ""


def run_version(binary: str, args: list[str]) -> None:
    result = command_output(binary, args)
    if result is None:
        return
    returncode, stdout = result
    first_line = stdout.strip().splitlines()
    detail = first_line[0] if first_line else binary
    if returncode == 0:
        ok(f"{binary}: {detail}")
    else:
        warn(f"{binary} returned exit {returncode}: {detail}")


def check_agent_browser() -> None:
    result = command_output("agent-browser", ["--version"])
    if result is None:
        return

    returncode, stdout = result
    detail = stdout.strip().splitlines()[0] if stdout.strip() else "agent-browser"
    if returncode != 0:
        fail(f"agent-browser returned exit {returncode}: {detail}")
        return

    installed_version = detail.split()[-1]
    if installed_version == EXPECTED_AGENT_BROWSER_VERSION:
        ok(f"agent-browser pinned version: {installed_version}")
        return

    fail(
        "agent-browser version mismatch: "
        f"expected {EXPECTED_AGENT_BROWSER_VERSION}, got {installed_version}. "
        "Run `python3 scripts/bootstrap.py --user`."
    )


def main() -> None:
    check_python()
    check_python_package("requests")
    check_python_package("dotenv")
    check_agent_browser()

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
