# Fulfills: REQ-RL-004 (independent per-user buckets)
# Fulfills: REQ-RL-005 (configurable per-user rate limits)
# Fulfills: REQ-RL-006 (first-request bucket creation at full capacity)
"""Per-user bucket registry: lookup, create, and configure independent token buckets."""

from __future__ import annotations

from dataclasses import dataclass, field

from token_bucket import BucketConfig, TokenBucket, create_bucket, try_consume


@dataclass
class QuotaConfig:
    default: BucketConfig
    users: dict[str, BucketConfig]


@dataclass
class QuotaTracker:
    config: QuotaConfig
    buckets: dict[str, TokenBucket] = field(default_factory=dict)


def create_tracker(config: QuotaConfig) -> QuotaTracker:
    """Create a new tracker with the given config and an empty bucket registry."""
    return QuotaTracker(config=config)


def check_request(tracker: QuotaTracker, user: str, now: float) -> tuple[bool, float, float | None]:
    """Look up or create the user's bucket, then try to consume a token.

    Uses user-specific config if present, otherwise the default config.
    """
    if user not in tracker.buckets:
        config = tracker.config.users.get(user, tracker.config.default)
        tracker.buckets[user] = create_bucket(config, now)
    return try_consume(tracker.buckets[user], now)
