#!/usr/bin/env python3
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Assert that all expected JSON array values exist in actual JSON array."
    )
    parser.add_argument("--expected", required=True, help="Expected JSON array")
    parser.add_argument("--actual", required=True, help="Actual JSON array")
    args = parser.parse_args()

    try:
        expected = json.loads(args.expected)
        actual = json.loads(args.actual)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON input: {exc}", file=sys.stderr)
        return 1

    if not isinstance(expected, list) or not isinstance(actual, list):
        print("Both --expected and --actual must be JSON arrays.", file=sys.stderr)
        return 1

    missing = [item for item in expected if item not in actual]
    if missing:
        print(f"Missing expected values: {', '.join(map(str, missing))}", file=sys.stderr)
        return 1

    print("Assertion passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
