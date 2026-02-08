# Fulfills: REQ-RL-001 (output format for allowed requests)
# Fulfills: REQ-RL-002 (output format with retry_after for denied requests)
# Fulfills: REQ-RL-005 (config loading via scenario files)
"""Entry point: CLI parsing, command dispatch, and JSON output formatting."""

from __future__ import annotations

import argparse
import json
import sys
import time

from token_bucket import BucketConfig
from quota_tracker import QuotaConfig, create_tracker, check_request
from config_loader import load_config, load_scenario, validate_request


def format_response(user: str, time_val: float, decision: str, remaining: float, retry_after: float | None) -> dict:
    """Build a JSON-serializable response dict.

    Rounds remaining and retry_after to 2 decimal places.
    """
    response = {
        "user": user,
        "time": time_val,
        "decision": decision,
        "remaining": round(remaining, 2),
    }
    if retry_after is not None:
        response["retry_after"] = round(retry_after, 2)
    return response


def run_check(user: str, time_val: float | None, config: dict) -> dict:
    """Process a single check request. Returns the response dict."""
    quota_config = load_config(config)
    tracker = create_tracker(quota_config)

    now = time_val if time_val is not None else time.time()
    allowed, remaining, retry_after = check_request(tracker, user, now)
    decision = "ALLOW" if allowed else "DENY"

    return format_response(user, now, decision, remaining, retry_after)


def run_scenario(file_path: str) -> list[dict]:
    """Load a scenario file, process all requests in order, return list of response dicts."""
    config, requests = load_scenario(file_path)
    tracker = create_tracker(config)
    results = []

    for req in requests:
        user, req_time = validate_request(req)
        allowed, remaining, retry_after = check_request(tracker, user, req_time)
        decision = "ALLOW" if allowed else "DENY"
        results.append(format_response(user, req_time, decision, remaining, retry_after))

    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse and validate CLI arguments. Returns parsed namespace."""
    parser = argparse.ArgumentParser(description="Rate limiter with per-user quotas")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Check a single request")
    check_parser.add_argument("--user", required=True, help="User identifier")
    check_parser.add_argument("--time", type=float, default=None, help="Timestamp in seconds")

    scenario_parser = subparsers.add_parser("scenario", help="Run a scenario from a file")
    scenario_parser.add_argument("--file", required=True, dest="file_path", help="Path to scenario JSON file")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    return args


def main() -> None:
    """Entry point. Parses arguments, dispatches to the appropriate command, handles exit codes."""
    args = parse_args()

    if args.command == "check":
        if not args.user:
            print("Error: user ID must be a non-empty string", file=sys.stderr)
            sys.exit(1)

        default_config = {"default": {"capacity": 5, "refill_rate": 1.0}, "users": {}}
        result = run_check(args.user, args.time, default_config)
        print(json.dumps(result))

    elif args.command == "scenario":
        try:
            results = run_scenario(args.file_path)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        for result in results:
            print(json.dumps(result))


if __name__ == "__main__":
    main()
