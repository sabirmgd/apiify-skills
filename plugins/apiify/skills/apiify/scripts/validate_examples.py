#!/usr/bin/env python3
"""Validate Apiify example artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from metadata_schema import validate as validate_metadata


ROW_KEYS = ("items", "results", "data", "posts", "rows")
REQUIRED_FILES = ("README.md", "metadata.json", "sample-output.redacted.json")
DISALLOWED_AUTH_TYPES = {"api_key", "bearer_token", "oauth", "optional_api_key", "optional_env_token"}
DISALLOWED_ENV_PARTS = ("API_KEY", "ACCESS_TOKEN", "BEARER", "CLIENT_SECRET", "REFRESH_TOKEN")


def default_examples_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "examples"


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def find_rows(payload: Any) -> list[Any] | None:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ROW_KEYS:
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
    return None


def validate_example(example_dir: Path) -> list[str]:
    errors: list[str] = []
    slug = example_dir.name

    for filename in REQUIRED_FILES:
        if not (example_dir / filename).is_file():
            errors.append(f"{slug}: missing {filename}")

    if errors:
        return errors

    metadata_path = example_dir / "metadata.json"
    sample_path = example_dir / "sample-output.redacted.json"
    readme_path = example_dir / "README.md"

    try:
        metadata = load_json(metadata_path)
    except Exception as exc:
        return [f"{slug}: metadata is not valid JSON: {exc}"]

    if not isinstance(metadata, dict):
        return [f"{slug}: metadata must be a JSON object"]

    for error in validate_metadata(metadata):
        errors.append(f"{slug}: {error}")

    if metadata.get("name") != slug:
        errors.append(f"{slug}: metadata name must match directory name")

    outputs = metadata.get("outputs")
    if isinstance(outputs, list):
        for output in outputs:
            if not isinstance(output, str) or not output:
                errors.append(f"{slug}: outputs must be non-empty strings")
    else:
        errors.append(f"{slug}: outputs must be a list")

    auth = metadata.get("auth")
    if isinstance(auth, dict):
        auth_type = str(auth.get("type", "")).lower()
        if auth_type in DISALLOWED_AUTH_TYPES:
            errors.append(f"{slug}: examples must not require API keys, bearer tokens, or OAuth")
        env = str(auth.get("env", ""))
        if any(part in env.upper() for part in DISALLOWED_ENV_PARTS):
            errors.append(f"{slug}: examples must not require credential env vars")

    try:
        sample = load_json(sample_path)
    except Exception as exc:
        return errors + [f"{slug}: sample output is not valid JSON: {exc}"]

    rows = find_rows(sample)
    if rows is None:
        errors.append(f"{slug}: sample output must include one of {', '.join(ROW_KEYS)}")
    elif not rows:
        errors.append(f"{slug}: sample output row list is empty")
    elif isinstance(outputs, list) and all(isinstance(row, dict) for row in rows):
        row_keys = set().union(*(row.keys() for row in rows))
        missing_outputs = [field for field in outputs if field not in row_keys]
        if missing_outputs:
            errors.append(
                f"{slug}: sample rows do not include outputs: {', '.join(missing_outputs)}"
            )

    readme = readme_path.read_text()
    expected_command = f"apiified/{slug}/script.py"
    if expected_command not in readme:
        errors.append(f"{slug}: README must include example command for {expected_command}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Apiify example folders.")
    parser.add_argument(
        "--examples-dir",
        default=str(default_examples_dir()),
        help="Examples directory. Defaults to plugins/apiify/examples.",
    )
    parser.add_argument(
        "--min-examples",
        type=int,
        default=10,
        help="Minimum number of complete example folders expected.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    examples_dir = Path(args.examples_dir)
    if not examples_dir.is_dir():
        raise SystemExit(f"Examples directory not found: {examples_dir}")

    example_dirs = sorted(path for path in examples_dir.iterdir() if path.is_dir())
    if len(example_dirs) < args.min_examples:
        raise SystemExit(
            f"Expected at least {args.min_examples} examples, found {len(example_dirs)}"
        )

    errors: list[str] = []
    for example_dir in example_dirs:
        errors.extend(validate_example(example_dir))

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        raise SystemExit(1)

    print(f"PASS validated {len(example_dirs)} Apiify examples")


if __name__ == "__main__":
    main()
