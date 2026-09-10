from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
ENTRIES_DIR = ROOT / "entries"
SCHEMA_FILE = ROOT / "schemas" / "resource.schema.json"


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> int:
    with SCHEMA_FILE.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)
    seen_ids: set[str] = set()
    failures = 0

    files = sorted(ENTRIES_DIR.glob("*.yml")) + sorted(
        ENTRIES_DIR.glob("*.yaml")
    )

    if not files:
        print("No resource entries found.")
        return 1

    for file in files:
        print(f"\nChecking {file.relative_to(ROOT)}")

        try:
            with file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as exc:
            print(f"  ERROR: invalid YAML: {exc}")
            failures += 1
            continue

        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

        if errors:
            for error in errors:
                path = ".".join(str(part) for part in error.path)
                location = f"{path}: " if path else ""
                print(f"  ERROR: {location}{error.message}")
            failures += 1
            continue

        resource_id = data["id"]

        if resource_id in seen_ids:
            print(f"  ERROR: duplicate id: {resource_id}")
            failures += 1
        else:
            seen_ids.add(resource_id)

        if not valid_url(data["upstream_url"]):
            print("  ERROR: upstream_url must be a valid HTTP(S) URL")
            failures += 1

        if not data["name"].strip():
            print("  ERROR: name cannot be empty")
            failures += 1

        print("  OK")

    print("\n-----------------------------")

    if failures:
        print(f"Validation failed with {failures} issue(s).")
        return 1

    print(f"Validation passed for {len(files)} resource(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())