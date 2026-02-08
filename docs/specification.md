# Rate Limiter with Per-User Quotas — Specification

## Core Principle

**Token bucket algorithm with per-user quota tracking** — each user gets an independent token bucket that refills at a fixed rate and allows bursts up to a configurable capacity, enabling fine-grained control over how many requests individual users can make within any time period.

## System Overview

The system is a command-line rate limiter that decides whether a user's request is allowed or denied based on a token bucket algorithm. It accepts a user identifier and returns a structured JSON response containing the allow/deny decision, remaining tokens, and retry information. Each user has an independent bucket with configurable capacity and refill rate. Buckets are created on first use at full capacity and refill lazily — tokens are calculated on demand when a request arrives, not via background timers. All state is in-memory and does not persist across process invocations.

## Requirements

### Token Bucket Algorithm

#### REQ-RL-001: Token Consumption and Allow Decision

The system shall consume one token from the user's bucket and return an ALLOW decision when the user has at least one token available after refill calculation.

**Example:** User "alice" has a bucket with capacity=5, refill_rate=1/s. At t=0.0 the bucket is full (5 tokens). A request at t=0.0 consumes 1 token → ALLOW, 4 tokens remaining.

#### REQ-RL-002: Deny Decision on Insufficient Tokens

The system shall return a DENY decision without consuming any tokens when the user has fewer than one token available after refill calculation. The response shall include a `retry_after` field indicating the number of seconds until the next full token becomes available, calculated as `(1 - current_tokens) / refill_rate`.

**Example:** User "alice" has capacity=5, refill_rate=1/s. After exhausting all tokens, a request arrives when tokens=0.5. Since 0.5 < 1, the request is denied. `retry_after` = (1 - 0.5) / 1 = 0.5 seconds.

#### REQ-RL-003: Lazy Token Refill

The system shall calculate token refill on each request using elapsed time since the last refill: `tokens = min(capacity, tokens + elapsed * refill_rate)`. The system shall NOT use background timers or threads for refill.

**Example:** User "alice" has capacity=5, refill_rate=1/s. At t=0.0 she has 3.0 tokens. At t=2.5, elapsed=2.5s, tokens_to_add=2.5, new tokens = min(5, 3.0 + 2.5) = 5.0. The bucket is full again.

### Per-User Quota Tracking

#### REQ-RL-004: Independent Per-User Buckets

The system shall maintain an independent token bucket for each unique user identifier. One user's requests shall have zero effect on another user's token count or rate limit decisions.

**Example:** Users "alice" and "bob" each have capacity=3, refill_rate=1/s. Alice makes 3 requests at t=0.0, exhausting her bucket. Bob then makes a request at t=0.0 → ALLOW with 2 tokens remaining. Alice's exhaustion does not affect Bob.

#### REQ-RL-005: Configurable Per-User Rate Limits

The system shall support different capacity and refill_rate values for different users. Users not explicitly configured shall receive default values. The system shall accept user-specific configurations via a JSON configuration input.

**Example:** Configuration defines "alice" with capacity=10, refill_rate=2/s (premium tier) and a default of capacity=5, refill_rate=1/s. User "alice" gets a 10-token bucket. User "bob" (not configured) gets the default 5-token bucket.

### Bucket Initialization

#### REQ-RL-006: First-Request Bucket Creation

The system shall create a new bucket at full capacity on a user's first request. The bucket shall use the user-specific configuration if one exists, or the default configuration otherwise.

**Example:** User "charlie" has no prior requests. On first request, the system creates a bucket with the default capacity (5 tokens) at full capacity. The request consumes 1 token → ALLOW, 4 tokens remaining.

## Negative Requirements

- The system shall NOT persist state across process invocations. All bucket state exists only in memory for the duration of the process.
- The system shall NOT use background threads, timers, or async processes. All computation happens synchronously within the request path.
- The system shall NOT implement any rate limiting algorithm other than token bucket.
- The system shall NOT validate or authenticate user identifiers. Any non-empty string is accepted as a valid user ID.
- The system shall NOT queue denied requests for later processing. Denied requests receive an immediate DENY response.
- The system shall NOT support variable token costs. Each request costs exactly one token.
- The system shall NOT evict or clean up inactive user buckets.

## Behavioral Scenarios

### Scenario 1: Burst Then Exhaustion and Recovery

**Given:** User "alice" with capacity=5, refill_rate=1/s. Bucket starts full at t=0.0.

**When:** Alice sends 6 requests at the following times:

| # | Time (s) | Expected Result | Expected Remaining |
|---|--------:|-----------------|-------------------:|
| 1 | 0.0 | ALLOW | 4.0 |
| 2 | 0.0 | ALLOW | 3.0 |
| 3 | 0.0 | ALLOW | 2.0 |
| 4 | 0.0 | ALLOW | 1.0 |
| 5 | 0.0 | ALLOW | 0.0 |
| 6 | 0.0 | DENY | 0.0 |

**Then:** The first 5 requests are allowed (burst capacity), the 6th is denied with `retry_after`=1.0 (since tokens=0.0, retry_after = (1 - 0) / 1 = 1.0s).

**When (continued):** Alice sends 1 request at t=1.0.

**Then:** Refill adds 1.0 token. Request consumes 1 → ALLOW, 0.0 remaining. This proves recovery after exhaustion.

### Scenario 2: Per-User Independence

**Given:** Users "alice" and "bob" each with capacity=3, refill_rate=1/s. Both buckets start full at t=0.0.

**When:**

| # | Time (s) | User | Expected Result | Expected Remaining |
|---|--------:|------|-----------------|-------------------:|
| 1 | 0.0 | alice | ALLOW | 2.0 |
| 2 | 0.0 | alice | ALLOW | 1.0 |
| 3 | 0.0 | alice | ALLOW | 0.0 |
| 4 | 0.0 | alice | DENY | 0.0 |
| 5 | 0.0 | bob | ALLOW | 2.0 |
| 6 | 0.0 | bob | ALLOW | 1.0 |
| 7 | 1.0 | alice | ALLOW | 0.0 |
| 8 | 1.0 | bob | ALLOW | 1.0 |

**Then:** Alice exhausts her bucket and is denied (request 4). Bob is completely unaffected — his first request (request 5) gets a full bucket. At t=1.0 both refill independently: Alice gets 1 token (from 0), Bob gets 1 token (from 1.0, capped by consumption).

### Scenario 3: Different Rate Limits Per User

**Given:** User "premium_user" configured with capacity=10, refill_rate=5/s. User "free_user" uses defaults: capacity=5, refill_rate=1/s. Both buckets start full at t=0.0.

**When:**

| # | Time (s) | User | Expected Result | Expected Remaining |
|---|--------:|------|-----------------|-------------------:|
| 1 | 0.0 | premium_user | ALLOW | 9.0 |
| 2 | 0.0 | premium_user | ALLOW | 8.0 |
| 3 | 0.0 | premium_user | ALLOW | 7.0 |
| 4 | 0.0 | free_user | ALLOW | 4.0 |
| 5 | 0.0 | free_user | ALLOW | 3.0 |
| 6 | 0.0 | free_user | ALLOW | 2.0 |
| 7 | 0.0 | free_user | ALLOW | 1.0 |
| 8 | 0.0 | free_user | ALLOW | 0.0 |
| 9 | 0.0 | free_user | DENY | 0.0 |
| 10 | 0.0 | premium_user | ALLOW | 6.0 |

**Then:** premium_user has made 4 requests and still has 6 tokens left. free_user is denied after 5 requests. premium_user's higher capacity is unaffected by free_user's exhaustion. free_user's `retry_after`=1.0s (refill_rate=1/s).

### Scenario 4: Lazy Refill Capped at Capacity

**Given:** User "alice" with capacity=5, refill_rate=1/s. Bucket starts full at t=0.0.

**When:** Alice sends 1 request at t=0.0 (→ 4.0 tokens remaining), then waits until t=10.0 and sends another request.

| # | Time (s) | Expected Tokens Before Request | Expected Refill | Expected Tokens After Refill | Expected Result | Expected Remaining |
|---|--------:|------:|------:|------:|-----------------|-------------------:|
| 1 | 0.0 | 5.0 | 0.0 | 5.0 | ALLOW | 4.0 |
| 2 | 10.0 | 4.0 | 10.0 | 5.0 (capped) | ALLOW | 4.0 |

**Then:** After 10 seconds of inactivity, the refill would add 10 tokens (10s × 1/s), but the bucket caps at capacity=5. The system does not accumulate tokens beyond capacity. Alice has 5.0 tokens before the request, 4.0 after.

### Scenario 5: Deny with Retry-After Timing

**Given:** User "alice" with capacity=3, refill_rate=2/s. Bucket starts full at t=0.0.

**When:**

| # | Time (s) | Expected Result | Expected Remaining | retry_after |
|---|--------:|-----------------|-------------------:|------------:|
| 1 | 0.0 | ALLOW | 2.0 | — |
| 2 | 0.0 | ALLOW | 1.0 | — |
| 3 | 0.0 | ALLOW | 0.0 | — |
| 4 | 0.0 | DENY | 0.0 | 0.5 |
| 5 | 0.25 | DENY | 0.5 | 0.25 |
| 6 | 0.5 | ALLOW | 0.0 | — |

**Then:** At t=0.0 with 0 tokens and refill_rate=2/s, retry_after = (1 - 0) / 2 = 0.5s. At t=0.25, tokens refill to 0.5, retry_after = (1 - 0.5) / 2 = 0.25s. At t=0.5, tokens refill to 1.0, which is enough → ALLOW.

## Interface Definition

### Input Format

The system shall accept commands via command-line arguments in the following formats:

**Check a request:**
```
python rate_limiter.py check --user <user_id> [--time <timestamp>]
```

- `--user` (required): Non-empty string identifying the user.
- `--time` (optional): Float timestamp in seconds. Defaults to current wall-clock time. Enables deterministic testing.

**Run a scenario from a file:**
```
python rate_limiter.py scenario --file <path>
```

The scenario file shall be a JSON file with the following structure:
```json
{
  "config": {
    "default": { "capacity": 5, "refill_rate": 1.0 },
    "users": {
      "premium_user": { "capacity": 10, "refill_rate": 5.0 }
    }
  },
  "requests": [
    { "user": "alice", "time": 0.0 },
    { "user": "alice", "time": 0.0 },
    { "user": "bob", "time": 0.5 }
  ]
}
```

### Output Format

Each request shall produce a single JSON line to stdout:

**Allowed response:**
```json
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 4.0}
```

**Denied response:**
```json
{"user": "alice", "time": 4.5, "decision": "DENY", "remaining": 0.5, "retry_after": 0.5}
```

Field definitions:
- `user` (string): The user identifier from the request.
- `time` (float): The timestamp of the request.
- `decision` (string): Either `"ALLOW"` or `"DENY"`.
- `remaining` (float): Tokens remaining after the decision.
- `retry_after` (float, DENY only): Seconds until the next full token is available.

When running in `scenario` mode, output shall be one JSON line per request, in the same order as the input requests.

### Exit Codes

| Code | Meaning |
|-----:|---------|
| 0 | All requests processed successfully (regardless of ALLOW/DENY outcomes) |
| 1 | Invalid input (missing required arguments, malformed JSON, empty user ID) |
| 2 | File not found (scenario file does not exist) |

## Assumptions

- **Single-threaded execution.** No concurrent access to bucket state.
- **Controllable time.** The `--time` flag enables deterministic scenarios. When omitted, the system uses wall-clock time.
- **User IDs are strings.** Any non-empty string is a valid user ID. Empty strings are rejected with exit code 1.
- **One token per request.** Each request costs exactly one token.
- **Python 3.10+ as implementation language.** Standard library only.
- **In-memory state only.** Bucket state lives in a Python dictionary. Lost on process exit.
- **Small user counts.** Scenarios involve 2-5 users. No optimization for large user populations.
- **Floating-point token counts.** Token values are floats to support fractional refills. Output values are rounded to 2 decimal places for display.

## Requirement Coverage Matrix

| Requirement | Scenario(s) | What Is Verified |
|------------|-------------|------------------|
| REQ-RL-001: Token Consumption and Allow | Scenario 1, 2, 3, 4 | Tokens decrease by 1 on each allowed request |
| REQ-RL-002: Deny on Insufficient Tokens | Scenario 1, 2, 3, 5 | Request denied when tokens < 1; retry_after is accurate |
| REQ-RL-003: Lazy Token Refill | Scenario 1, 4, 5 | Tokens calculated from elapsed time; capped at capacity |
| REQ-RL-004: Independent Per-User Buckets | Scenario 2, 3 | One user's exhaustion does not affect another |
| REQ-RL-005: Configurable Per-User Rates | Scenario 3 | Different users get different capacity/refill_rate |
| REQ-RL-006: First-Request Bucket Creation | Scenario 1, 2, 3 | First request creates bucket at full capacity |
