# Fulfills: REQ-RL-005 (config input — configurable per-user rate limits)
"""Parse and validate JSON config and scenario files."""

from __future__ import annotations

import json
from pathlib import Path

from token_bucket import BucketConfig
from quota_tracker import QuotaConfig


def load_config(config_data: dict) -> QuotaConfig:
    """Parse the config section of a scenario file into a QuotaConfig.

    Validates required fields (default.capacity, default.refill_rate).
    Raises ValueError on malformed input.
    """
    if "default" not in config_data:
        raise ValueError("config must contain a 'default' section")

    default_data = config_data["default"]
    if "capacity" not in default_data or "refill_rate" not in default_data:
        raise ValueError("default config must contain 'capacity' and 'refill_rate'")

    default = BucketConfig(
        capacity=float(default_data["capacity"]),
        refill_rate=float(default_data["refill_rate"]),
    )

    users: dict[str, BucketConfig] = {}
    for user_id, user_data in config_data.get("users", {}).items():
        if "capacity" not in user_data or "refill_rate" not in user_data:
            raise ValueError(f"user '{user_id}' config must contain 'capacity' and 'refill_rate'")
        users[user_id] = BucketConfig(
            capacity=float(user_data["capacity"]),
            refill_rate=float(user_data["refill_rate"]),
        )

    return QuotaConfig(default=default, users=users)


def load_scenario(file_path: str) -> tuple[QuotaConfig, list[dict]]:
    """Read a JSON scenario file, parse config and requests.

    Returns (QuotaConfig, requests) where each request is {"user": str, "time": float}.
    Raises FileNotFoundError if missing, ValueError if malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"scenario file not found: {file_path}")

    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"malformed JSON in scenario file: {e}")

    if "config" not in data:
        raise ValueError("scenario file must contain a 'config' section")
    if "requests" not in data:
        raise ValueError("scenario file must contain a 'requests' section")

    config = load_config(data["config"])
    requests = data["requests"]

    if not isinstance(requests, list):
        raise ValueError("'requests' must be a list")

    return (config, requests)


def validate_request(request: dict) -> tuple[str, float]:
    """Validate a single request dict has 'user' (non-empty string) and 'time' (float).

    Returns (user, time). Raises ValueError on invalid input.
    """
    if "user" not in request:
        raise ValueError("request must contain 'user'")
    if "time" not in request:
        raise ValueError("request must contain 'time'")

    user = request["user"]
    if not isinstance(user, str) or not user:
        raise ValueError("user ID must be a non-empty string")

    return (user, float(request["time"]))
