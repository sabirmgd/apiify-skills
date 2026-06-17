#!/usr/bin/env python3
"""Validate the minimum Apiify metadata contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "name": str,
    "source": str,
    "approach": str,
    "runtime_tier": int,
    "description": str,
    "inputs": list,
    "outputs": list,
    "auth": dict,
    "verification_command": str,
    "verification_result": str,
    "known_risks": list,
}


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in payload:
            errors.append(f"missing required field: {field}")
            continue
        if not isinstance(payload[field], expected_type):
            errors.append(
                f"{field} must be {expected_type.__name__}, got {type(payload[field]).__name__}"
            )

    tier = payload.get("runtime_tier")
    if isinstance(tier, int) and tier not in {1, 2, 3, 4}:
        errors.append("runtime_tier must be one of 1, 2, 3, 4")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Apiify metadata.json.")
    parser.add_argument("metadata_path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.metadata_path)
    with path.open() as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit("metadata must be a JSON object")

    errors = validate(payload)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        raise SystemExit(1)
    print(f"PASS metadata valid: {path}")


if __name__ == "__main__":
    main()

