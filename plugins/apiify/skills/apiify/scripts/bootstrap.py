#!/usr/bin/env python3
"""Install Apiify local runtime dependencies.

This script is intentionally conservative: it installs only the browser CLI and
small Python packages used by generated scripts. It does not collect or store
site credentials.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


PYTHON_PACKAGES = ["requests", "python-dotenv"]


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(cmd))
    subprocess.run(cmd, check=True, env=env)


def python_for_venv(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def install_python_packages(args: argparse.Namespace) -> None:
    if args.venv:
        venv_path = Path(args.venv).expanduser().resolve()
        if not python_for_venv(venv_path).exists():
            print(f"Creating virtualenv: {venv_path}")
            venv.create(venv_path, with_pip=True)
        py = str(python_for_venv(venv_path))
        run([py, "-m", "pip", "install", "--upgrade", "pip"])
        run([py, "-m", "pip", "install", *PYTHON_PACKAGES])
        print(f"Use this Python for generated scripts: {py}")
        return

    cmd = [sys.executable, "-m", "pip", "install"]
    if args.user:
        cmd.append("--user")
    cmd.extend(PYTHON_PACKAGES)
    run(cmd)


def install_agent_browser(args: argparse.Namespace) -> None:
    if args.skip_agent_browser:
        return

    if shutil.which("agent-browser"):
        print("agent-browser already installed")
    else:
        if not shutil.which("npm"):
            raise SystemExit(
                "agent-browser is missing and npm is not available. "
                "Install Node/npm or install agent-browser with Homebrew/Cargo."
            )
        run(["npm", "install", "-g", "agent-browser"])

    if not args.skip_browser_install:
        install_cmd = ["agent-browser", "install"]
        if args.with_deps:
            install_cmd.append("--with-deps")
        run(install_cmd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Apiify dependencies.")
    parser.add_argument(
        "--user",
        action="store_true",
        help="Install Python packages with pip --user when not using --venv.",
    )
    parser.add_argument(
        "--venv",
        help="Create/use a virtualenv at this path and install Python packages there.",
    )
    parser.add_argument(
        "--skip-agent-browser",
        action="store_true",
        help="Do not install the agent-browser CLI.",
    )
    parser.add_argument(
        "--skip-browser-install",
        action="store_true",
        help="Do not run agent-browser install.",
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help="Pass --with-deps to agent-browser install on Linux.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    install_python_packages(args)
    install_agent_browser(args)
    print("Apiify bootstrap complete.")


if __name__ == "__main__":
    main()

