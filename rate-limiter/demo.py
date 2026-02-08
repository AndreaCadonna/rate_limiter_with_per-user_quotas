# Fulfills: Project philosophy demo requirement
"""Narrated demo: walk through rate limiter capabilities with different data than validation."""

from __future__ import annotations

import json
import sys

from token_bucket import BucketConfig
from quota_tracker import QuotaConfig, create_tracker, check_request
from rate_limiter import format_response


def narrate(message: str) -> None:
    """Print a narration line to stderr (keeps stdout clean for JSON if piped)."""
    print(message, file=sys.stderr)


def demo_burst_and_recovery() -> None:
    """Show a single user making requests until denied, then recovering."""
    narrate("=" * 60)
    narrate("DEMO 1: Burst and Exhaustion with Recovery")
    narrate("=" * 60)
    narrate("")
    narrate("User 'diana' has a bucket (capacity=5, refill_rate=1/s).")
    narrate("She sends 6 rapid requests at t=0, then one more at t=2.")
    narrate("")

    config = QuotaConfig(default=BucketConfig(capacity=5, refill_rate=1.0), users={})
    tracker = create_tracker(config)

    for i in range(6):
        allowed, remaining, retry_after = check_request(tracker, "diana", 0.0)
        decision = "ALLOW" if allowed else "DENY"
        resp = format_response("diana", 0.0, decision, remaining, retry_after)
        narrate(f"  Request {i + 1} at t=0.0: {json.dumps(resp)}")

    narrate("")
    narrate("Diana is denied. She waits 2 seconds for tokens to refill...")
    narrate("")

    allowed, remaining, retry_after = check_request(tracker, "diana", 2.0)
    decision = "ALLOW" if allowed else "DENY"
    resp = format_response("diana", 2.0, decision, remaining, retry_after)
    narrate(f"  Request 7 at t=2.0: {json.dumps(resp)}")

    narrate("")
    narrate("Recovery confirmed: after waiting, diana can make requests again.")
    narrate("")


def demo_user_independence() -> None:
    """Show two users with independent buckets."""
    narrate("=" * 60)
    narrate("DEMO 2: Per-User Independence")
    narrate("=" * 60)
    narrate("")
    narrate("Users 'eve' and 'frank' each get independent buckets.")
    narrate("Eve exhausts hers; frank should be completely unaffected.")
    narrate("")

    config = QuotaConfig(default=BucketConfig(capacity=5, refill_rate=1.0), users={})
    tracker = create_tracker(config)

    for i in range(5):
        allowed, remaining, retry_after = check_request(tracker, "eve", 0.0)
        decision = "ALLOW" if allowed else "DENY"
        resp = format_response("eve", 0.0, decision, remaining, retry_after)
        narrate(f"  Eve request {i + 1}: {json.dumps(resp)}")

    allowed, remaining, retry_after = check_request(tracker, "eve", 0.0)
    decision = "ALLOW" if allowed else "DENY"
    resp = format_response("eve", 0.0, decision, remaining, retry_after)
    narrate(f"  Eve request 6 (denied): {json.dumps(resp)}")

    narrate("")
    narrate("Eve is exhausted. Now frank makes his first request:")
    narrate("")

    allowed, remaining, retry_after = check_request(tracker, "frank", 0.0)
    decision = "ALLOW" if allowed else "DENY"
    resp = format_response("frank", 0.0, decision, remaining, retry_after)
    narrate(f"  Frank request 1: {json.dumps(resp)}")

    narrate("")
    narrate("Frank has a full bucket despite eve being exhausted.")
    narrate("")


def demo_tier_differences() -> None:
    """Show premium vs. free tier with different limits."""
    narrate("=" * 60)
    narrate("DEMO 3: Premium vs. Free Tier")
    narrate("=" * 60)
    narrate("")
    narrate("Config: 'gold_user' gets capacity=8, refill_rate=4/s (premium).")
    narrate("        Default users get capacity=4, refill_rate=1/s (free).")
    narrate("")

    config = QuotaConfig(
        default=BucketConfig(capacity=4, refill_rate=1.0),
        users={"gold_user": BucketConfig(capacity=8, refill_rate=4.0)},
    )
    tracker = create_tracker(config)

    requests = [
        ("gold_user", 0.0),
        ("gold_user", 0.0),
        ("gold_user", 0.0),
        ("gold_user", 0.0),
        ("gold_user", 0.0),
        ("basic_user", 0.0),
        ("basic_user", 0.0),
        ("basic_user", 0.0),
        ("basic_user", 0.0),
        ("basic_user", 0.0),
    ]

    for i, (user, t) in enumerate(requests):
        allowed, remaining, retry_after = check_request(tracker, user, t)
        decision = "ALLOW" if allowed else "DENY"
        resp = format_response(user, t, decision, remaining, retry_after)
        narrate(f"  Request {i + 1}: {json.dumps(resp)}")

    narrate("")
    narrate("Gold user made 5 requests and still has 3 tokens left.")
    narrate("Basic user is denied after 4 requests (lower capacity).")
    narrate("")


def main() -> None:
    """Run the demo sequence with narration."""
    narrate("")
    narrate("Rate Limiter with Per-User Quotas -- Demo")
    narrate("=" * 60)
    narrate("")

    demo_burst_and_recovery()
    demo_user_independence()
    demo_tier_differences()

    narrate("=" * 60)
    narrate("Demo complete.")
    narrate("")


if __name__ == "__main__":
    main()
