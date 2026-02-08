# Fulfills: REQ-RL-001 (token consumption and allow decision)
# Fulfills: REQ-RL-002 (deny decision with retry_after calculation)
# Fulfills: REQ-RL-003 (lazy token refill capped at capacity)
# Fulfills: REQ-RL-006 (first-request bucket creation at full capacity)
"""Token bucket algorithm for a single bucket: lazy refill, consume, and deny."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BucketConfig:
    capacity: float
    refill_rate: float


@dataclass
class TokenBucket:
    config: BucketConfig
    tokens: float
    last_refill: float


def create_bucket(config: BucketConfig, now: float) -> TokenBucket:
    """Create a new bucket at full capacity with last_refill set to now."""
    return TokenBucket(config=config, tokens=config.capacity, last_refill=now)


def _refill(bucket: TokenBucket, now: float) -> None:
    """Add tokens based on elapsed time, capped at capacity. Mutates bucket in place."""
    elapsed = now - bucket.last_refill
    if elapsed > 0:
        bucket.tokens = min(bucket.config.capacity, bucket.tokens + elapsed * bucket.config.refill_rate)
        bucket.last_refill = now


def try_consume(bucket: TokenBucket, now: float) -> tuple[bool, float, float | None]:
    """Refill tokens, then attempt to consume one token.

    Returns (allowed, remaining, retry_after).
    retry_after is None when allowed.
    """
    _refill(bucket, now)
    if bucket.tokens >= 1.0:
        bucket.tokens -= 1.0
        return (True, bucket.tokens, None)
    else:
        retry_after = (1.0 - bucket.tokens) / bucket.config.refill_rate
        return (False, bucket.tokens, retry_after)
