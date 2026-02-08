# Fulfills: Behavioral Scenarios 1-5 from specification
"""Automated validation: run all 5 spec scenarios, compare output to expected values."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCENARIOS = [
    {
        "name": "Scenario 1: Burst Then Exhaustion and Recovery",
        "file": "scenarios/scenario_1.json",
        "expected": [
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 4.0},
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 3.0},
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 2.0},
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 1.0},
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 0.0},
            {"user": "alice", "time": 0.0, "decision": "DENY", "remaining": 0.0, "retry_after": 1.0},
            {"user": "alice", "time": 1.0, "decision": "ALLOW", "remaining": 0.0},
        ],
    },
    {
        "name": "Scenario 2: Per-User Independence",
        "file": "scenarios/scenario_2.json",
        "expected": [
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 2.0},
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 1.0},
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 0.0},
            {"user": "alice", "time": 0.0, "decision": "DENY", "remaining": 0.0, "retry_after": 1.0},
            {"user": "bob", "time": 0.0, "decision": "ALLOW", "remaining": 2.0},
            {"user": "bob", "time": 0.0, "decision": "ALLOW", "remaining": 1.0},
            {"user": "alice", "time": 1.0, "decision": "ALLOW", "remaining": 0.0},
            {"user": "bob", "time": 1.0, "decision": "ALLOW", "remaining": 1.0},
        ],
    },
    {
        "name": "Scenario 3: Different Rate Limits Per User",
        "file": "scenarios/scenario_3.json",
        "expected": [
            {"user": "premium_user", "time": 0.0, "decision": "ALLOW", "remaining": 9.0},
            {"user": "premium_user", "time": 0.0, "decision": "ALLOW", "remaining": 8.0},
            {"user": "premium_user", "time": 0.0, "decision": "ALLOW", "remaining": 7.0},
            {"user": "free_user", "time": 0.0, "decision": "ALLOW", "remaining": 4.0},
            {"user": "free_user", "time": 0.0, "decision": "ALLOW", "remaining": 3.0},
            {"user": "free_user", "time": 0.0, "decision": "ALLOW", "remaining": 2.0},
            {"user": "free_user", "time": 0.0, "decision": "ALLOW", "remaining": 1.0},
            {"user": "free_user", "time": 0.0, "decision": "ALLOW", "remaining": 0.0},
            {"user": "free_user", "time": 0.0, "decision": "DENY", "remaining": 0.0, "retry_after": 1.0},
            {"user": "premium_user", "time": 0.0, "decision": "ALLOW", "remaining": 6.0},
        ],
    },
    {
        "name": "Scenario 4: Lazy Refill Capped at Capacity",
        "file": "scenarios/scenario_4.json",
        "expected": [
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 4.0},
            {"user": "alice", "time": 10.0, "decision": "ALLOW", "remaining": 4.0},
        ],
    },
    {
        "name": "Scenario 5: Deny with Retry-After Timing",
        "file": "scenarios/scenario_5.json",
        "expected": [
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 2.0},
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 1.0},
            {"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 0.0},
            {"user": "alice", "time": 0.0, "decision": "DENY", "remaining": 0.0, "retry_after": 0.5},
            {"user": "alice", "time": 0.25, "decision": "DENY", "remaining": 0.5, "retry_after": 0.25},
            {"user": "alice", "time": 0.5, "decision": "ALLOW", "remaining": 0.0},
        ],
    },
]

TOLERANCE = 0.01


def run_scenario_file(file_path: str) -> list[dict]:
    """Execute rate_limiter.py scenario, capture stdout, parse JSON lines."""
    script_dir = Path(__file__).parent
    result = subprocess.run(
        [sys.executable, str(script_dir / "rate_limiter.py"), "scenario", "--file", file_path],
        capture_output=True,
        text=True,
        cwd=str(script_dir),
    )
    if result.returncode != 0:
        raise RuntimeError(f"rate_limiter.py exited with code {result.returncode}: {result.stderr}")
    lines = result.stdout.strip().split("\n")
    return [json.loads(line) for line in lines if line.strip()]


def compare_results(actual: list[dict], expected: list[dict], scenario_name: str) -> bool:
    """Compare each response field. Uses tolerance for float comparisons. Print mismatches."""
    if len(actual) != len(expected):
        print(f"  MISMATCH: expected {len(expected)} responses, got {len(actual)}")
        return False

    passed = True
    for i, (act, exp) in enumerate(zip(actual, expected)):
        for key in exp:
            if key not in act:
                print(f"  Request {i + 1}: missing field '{key}'")
                passed = False
                continue
            if isinstance(exp[key], float):
                if abs(act[key] - exp[key]) > TOLERANCE:
                    print(f"  Request {i + 1}: {key} = {act[key]}, expected {exp[key]}")
                    passed = False
            elif act[key] != exp[key]:
                print(f"  Request {i + 1}: {key} = {act[key]!r}, expected {exp[key]!r}")
                passed = False

        # Check for unexpected retry_after in ALLOW responses
        if exp.get("decision") == "ALLOW" and "retry_after" in act:
            print(f"  Request {i + 1}: unexpected retry_after in ALLOW response")
            passed = False

    return passed


def main() -> None:
    """Run all scenarios, print results, exit 0 if all pass, exit 1 if any fail."""
    all_passed = True

    for scenario in SCENARIOS:
        name = scenario["name"]
        file_path = scenario["file"]
        expected = scenario["expected"]

        try:
            actual = run_scenario_file(file_path)
            passed = compare_results(actual, expected, name)
        except Exception as e:
            print(f"{name} ... FAIL")
            print(f"  ERROR: {e}")
            all_passed = False
            continue

        if passed:
            print(f"{name} ... PASS")
        else:
            print(f"{name} ... FAIL")
            all_passed = False

    print()
    if all_passed:
        print(f"All {len(SCENARIOS)} scenarios passed.")
    else:
        print("Some scenarios FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
