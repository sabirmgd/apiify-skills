#!/usr/bin/env python3
"""Export Apiify JSON output to CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


COMMON_ITEM_KEYS = ("items", "results", "data", "posts", "rows")


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open() as handle:
        return json.load(handle)


def find_rows(payload: Any, key: str | None) -> list[Any]:
    if key:
        current = payload
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                raise SystemExit(f"Key path not found: {key}")
            current = current[part]
        if not isinstance(current, list):
            raise SystemExit(f"Key path is not a list: {key}")
        return current

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for candidate in COMMON_ITEM_KEYS:
            value = payload.get(candidate)
            if isinstance(value, list):
                return value
    raise SystemExit("Could not find a row list. Pass --key items.path")


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, child in value.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten(child, child_key))
        return out
    if isinstance(value, list):
        return {prefix: json.dumps(value, ensure_ascii=False)}
    return {prefix: value}


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_csv(rows: list[Any], output: str | None, fields: list[str] | None) -> None:
    flat_rows = [flatten(row) if isinstance(row, dict) else {"value": row} for row in rows]
    if fields:
        header = fields
    else:
        seen: set[str] = set()
        header = []
        for row in flat_rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    header.append(key)

    handle = Path(output).open("w", newline="") if output else sys.stdout
    close = output is not None
    try:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in flat_rows:
            writer.writerow({key: stringify(row.get(key)) for key in header})
    finally:
        if close:
            handle.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Apiify JSON to CSV.")
    parser.add_argument("json_path", help="JSON file path, or - for stdin")
    parser.add_argument("--output", "-o", help="CSV output path. Defaults to stdout.")
    parser.add_argument(
        "--key",
        help="Dot-path to the list of rows. Defaults to items/results/data/posts/rows.",
    )
    parser.add_argument(
        "--fields",
        help="Comma-separated field list. Defaults to all discovered flattened fields.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_json(args.json_path)
    rows = find_rows(payload, args.key)
    fields = [field.strip() for field in args.fields.split(",")] if args.fields else None
    write_csv(rows, args.output, fields)


if __name__ == "__main__":
    main()

