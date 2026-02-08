# Rate Limiter with Per-User Quotas — Technical Design

## Core Principle

**Token bucket algorithm with per-user quota tracking** — each user gets an independent token bucket that refills at a fixed rate and allows bursts up to a configurable capacity, enabling fine-grained control over how many requests individual users can make within any time period.

## Technology Choice

**Language:** Python 3.10+
**Justification:** The spec explicitly assumes Python 3.10+. Python is boring, widely known, has a rich standard library, and its readability makes the algorithm's behavior self-evident. Type hints (available since 3.10 with `|` union syntax) provide documentation without a framework.

**Dependencies:** None — standard library only.

Modules used from the standard library:
- `json` — parsing config/scenario files, formatting output
- `argparse` — CLI argument parsing
- `sys` — exit codes, stdout
- `time` — wall-clock fallback when `--time` is omitted
- `dataclasses` — lightweight data structures without boilerplate
- `pathlib` — file path handling for scenario files

All are part of the Python standard library. No `pip install` required.

## File Structure

```
rate-limiter/
├── rate_limiter.py       ← entry point: CLI parsing, command dispatch, output
├── token_bucket.py       ← single token bucket: refill logic, consume, deny
├── quota_tracker.py      ← per-user bucket registry: lookup, create, configure
├── config_loader.py      ← parse and validate JSON config and scenario files
├── scenarios/
│   ├── scenario_1.json   ← burst then exhaustion and recovery
│   ├── scenario_2.json   ← per-user independence
│   ├── scenario_3.json   ← different rate limits per user
│   ├── scenario_4.json   ← lazy refill capped at capacity
│   └── scenario_5.json   ← deny with retry-after timing
├── validate.py           ← automated validation: run scenarios, compare output
└── demo.py               ← narrated demo: walk through capabilities with output
```

**File count:** 10 (within 5-15 range). Two levels of nesting (scenarios/ directory only).

## Component Design

### rate_limiter.py — Entry Point

**Purpose:** Parse CLI arguments, dispatch to check or scenario mode, format and print JSON output.
**Fulfills:** REQ-RL-001 (output format), REQ-RL-002 (output format with retry_after), REQ-RL-005 (config loading)

**Functions:**

- `main() -> None` — Entry point. Parses arguments, dispatches to the appropriate command, handles exit codes.
- `run_check(user: str, time_val: float | None, config: dict) -> dict` — Process a single check request. Returns the response dict.
- `run_scenario(file_path: str) -> list[dict]` — Load a scenario file, process all requests in order, return list of response dicts.
- `format_response(user: str, time_val: float, decision: str, remaining: float, retry_after: float | None) -> dict` — Build the JSON-serializable response dict. Rounds `remaining` and `retry_after` to 2 decimal places.
- `parse_args(argv: list[str] | None = None) -> argparse.Namespace` — Parse and validate CLI arguments. Returns parsed namespace.

**Exit codes:**
- `0` — success (all requests processed)
- `1` — invalid input (missing args, malformed JSON, empty user)
- `2` — file not found (scenario file missing)

### token_bucket.py — Token Bucket Algorithm

**Purpose:** Implement the token bucket algorithm for a single bucket: lazy refill, consume, and deny with retry_after calculation.
**Fulfills:** REQ-RL-001, REQ-RL-002, REQ-RL-003, REQ-RL-006

**Data Structures:**

```python
@dataclass
class BucketConfig:
    capacity: float       # maximum tokens the bucket can hold
    refill_rate: float    # tokens added per second

@dataclass
class TokenBucket:
    config: BucketConfig
    tokens: float         # current available tokens
    last_refill: float    # timestamp of last refill calculation
```

**Functions:**

- `create_bucket(config: BucketConfig, now: float) -> TokenBucket` — Create a new bucket at full capacity with `last_refill` set to `now`. Fulfills REQ-RL-006.
- `try_consume(bucket: TokenBucket, now: float) -> tuple[bool, float, float | None]` — Refill tokens based on elapsed time, then attempt to consume one token. Returns `(allowed, remaining, retry_after)`. `retry_after` is `None` when allowed. Fulfills REQ-RL-001, REQ-RL-002, REQ-RL-003.
- `_refill(bucket: TokenBucket, now: float) -> None` — Calculate elapsed time since `last_refill`, add `elapsed * refill_rate` tokens capped at capacity, update `last_refill`. Mutates bucket in place. Fulfills REQ-RL-003.

**Algorithm detail for `try_consume`:**

```
1. _refill(bucket, now)
2. if bucket.tokens >= 1.0:
       bucket.tokens -= 1.0
       return (True, bucket.tokens, None)
   else:
       retry_after = (1.0 - bucket.tokens) / bucket.config.refill_rate
       return (False, bucket.tokens, retry_after)
```

### quota_tracker.py — Per-User Bucket Registry

**Purpose:** Maintain independent token buckets per user. Look up existing buckets or create new ones on first request. Apply per-user or default configuration.
**Fulfills:** REQ-RL-004, REQ-RL-005, REQ-RL-006

**Data Structures:**

```python
@dataclass
class QuotaConfig:
    default: BucketConfig                    # default config for unconfigured users
    users: dict[str, BucketConfig]           # per-user overrides (may be empty)
```

**Functions:**

- `create_tracker(config: QuotaConfig) -> QuotaTracker` — Create a new tracker with the given config and an empty bucket registry.
- `check_request(tracker: QuotaTracker, user: str, now: float) -> tuple[bool, float, float | None]` — Look up or create the user's bucket, call `try_consume`, return the result. Fulfills REQ-RL-004, REQ-RL-005, REQ-RL-006.

**Class:**

```python
@dataclass
class QuotaTracker:
    config: QuotaConfig
    buckets: dict[str, TokenBucket]  # user_id -> TokenBucket
```

The `check_request` function:
1. If `user` not in `buckets`: look up config (`users[user]` if present, else `default`), call `create_bucket`, store it.
2. Call `try_consume(buckets[user], now)` and return the result.

### config_loader.py — Configuration and Scenario Parser

**Purpose:** Parse JSON configuration and scenario files. Validate structure and return typed data.
**Fulfills:** REQ-RL-005 (config input), Interface Definition (scenario file format)

**Functions:**

- `load_config(config_data: dict) -> QuotaConfig` — Parse the `"config"` section of a scenario file into a `QuotaConfig`. Validates required fields (`default.capacity`, `default.refill_rate`). Raises `ValueError` on malformed input.
- `load_scenario(file_path: str) -> tuple[QuotaConfig, list[dict]]` — Read a JSON scenario file, parse config and requests. Returns `(QuotaConfig, requests)` where each request is `{"user": str, "time": float}`. Raises `FileNotFoundError` if missing, `ValueError` if malformed.
- `validate_request(request: dict) -> tuple[str, float]` — Validate a single request dict has `"user"` (non-empty string) and `"time"` (float). Returns `(user, time)`. Raises `ValueError` on invalid input.

### validate.py — Automated Validation Script

**Purpose:** Run all 5 spec scenarios, compare actual output to expected output, report pass/fail per scenario.
**Fulfills:** Behavioral Scenarios 1-5 from specification

**Functions:**

- `main() -> None` — Run all scenarios, print results, exit 0 if all pass, exit 1 if any fail.
- `run_scenario_file(file_path: str) -> list[dict]` — Execute `rate_limiter.py scenario --file <path>` as a subprocess, capture stdout, parse JSON lines.
- `compare_results(actual: list[dict], expected: list[dict], scenario_name: str) -> bool` — Compare each response field. Uses tolerance of 0.01 for float comparisons. Print mismatches.

**Expected outputs are hardcoded** in `validate.py` based on the spec's scenario tables. The scenario JSON files provide input; the validation script knows what output to expect.

### demo.py — Narrated Demo Script

**Purpose:** Walk through the rate limiter's capabilities with narrated output. Uses different data than validation to prove generalization.
**Fulfills:** Project philosophy demo requirement

**Functions:**

- `main() -> None` — Run the demo sequence with printed narration between outputs.
- `run_check(args: list[str]) -> str` — Execute `rate_limiter.py check` with given args, return output.
- `narrate(message: str) -> None` — Print a narration line to stderr (keeps stdout clean for JSON if piped).

**Demo sequence:**
1. Show a single user making requests until denied, then recovering.
2. Show two users with independent buckets.
3. Show premium vs. free tier with different limits.

### scenarios/*.json — Scenario Data Files

**Purpose:** Input files for the 5 behavioral scenarios from the spec. Each contains a config section and a list of timestamped requests.

All 5 files follow the same structure defined in the spec's Interface Definition:
```json
{
  "config": {
    "default": { "capacity": <float>, "refill_rate": <float> },
    "users": { "<user_id>": { "capacity": <float>, "refill_rate": <float> } }
  },
  "requests": [
    { "user": "<user_id>", "time": <float> },
    ...
  ]
}
```

## Data Flow

```
CLI input
  │
  ├── "check --user alice --time 0.0"
  │     │
  │     ▼
  │   parse_args()  →  (command="check", user="alice", time=0.0)
  │     │
  │     ▼
  │   QuotaTracker with default config (no scenario file for single check)
  │     │
  │     ▼
  │   check_request(tracker, "alice", 0.0)
  │     │
  │     ├── bucket not found → create_bucket(default_config, 0.0) → full bucket
  │     │
  │     ▼
  │   try_consume(bucket, 0.0)
  │     │
  │     ├── _refill(bucket, 0.0) → tokens updated with elapsed time
  │     ├── tokens >= 1.0? → yes: consume → (True, 4.0, None)
  │     │                  → no:  deny   → (False, 0.5, 0.5)
  │     │
  │     ▼
  │   format_response("alice", 0.0, "ALLOW", 4.0, None)
  │     │
  │     ▼
  │   print JSON to stdout → exit 0
  │
  └── "scenario --file scenario_1.json"
        │
        ▼
      load_scenario("scenario_1.json")  →  (QuotaConfig, [requests...])
        │
        ▼
      create_tracker(config)
        │
        ▼
      for each request in order:
        │
        ├── validate_request(request) → (user, time)
        ├── check_request(tracker, user, time)
        ├── format_response(...)
        └── print JSON line to stdout
        │
        ▼
      exit 0
```

**Traceability through the pipeline:**
- CLI args → `parse_args()` validates user is non-empty (spec: empty strings rejected with exit 1)
- Config → `load_config()` validates structure, builds `QuotaConfig` (REQ-RL-005)
- Per-user dispatch → `check_request()` in QuotaTracker handles lookup/create (REQ-RL-004, REQ-RL-006)
- Algorithm → `try_consume()` implements refill + consume/deny (REQ-RL-001, REQ-RL-002, REQ-RL-003)
- Output → `format_response()` builds JSON with all required fields, rounds floats to 2 decimal places

## Implementation Plan

### Step 1: Token Bucket Core

**Branch:** `feat/token-bucket`
**Files:** `token_bucket.py`
**What:** Implement `BucketConfig`, `TokenBucket`, `create_bucket`, `_refill`, and `try_consume`. This is the core algorithm — everything else builds on it.

**Definition of Done:**
```bash
python -c "
from token_bucket import BucketConfig, create_bucket, try_consume
cfg = BucketConfig(capacity=5, refill_rate=1.0)
b = create_bucket(cfg, 0.0)
print(try_consume(b, 0.0))   # (True, 4.0, None)
print(try_consume(b, 0.0))   # (True, 3.0, None)
print(try_consume(b, 0.0))   # (True, 2.0, None)
print(try_consume(b, 0.0))   # (True, 1.0, None)
print(try_consume(b, 0.0))   # (True, 0.0, None)
print(try_consume(b, 0.0))   # (False, 0.0, 1.0)
print(try_consume(b, 1.0))   # (True, 0.0, None)
"
```

Expected output:
```
(True, 4.0, None)
(True, 3.0, None)
(True, 2.0, None)
(True, 1.0, None)
(True, 0.0, None)
(False, 0.0, 1.0)
(True, 0.0, None)
```

### Step 2: Per-User Quota Tracker

**Branch:** `feat/quota-tracker`
**Files:** `quota_tracker.py`
**What:** Implement `QuotaConfig`, `QuotaTracker`, `create_tracker`, and `check_request`. Depends on `token_bucket.py` from Step 1.

**Definition of Done:**
```bash
python -c "
from token_bucket import BucketConfig
from quota_tracker import QuotaConfig, create_tracker, check_request
cfg = QuotaConfig(
    default=BucketConfig(capacity=3, refill_rate=1.0),
    users={}
)
t = create_tracker(cfg)
print(check_request(t, 'alice', 0.0))  # (True, 2.0, None)
print(check_request(t, 'alice', 0.0))  # (True, 1.0, None)
print(check_request(t, 'alice', 0.0))  # (True, 0.0, None)
print(check_request(t, 'alice', 0.0))  # (False, 0.0, 1.0)
print(check_request(t, 'bob', 0.0))    # (True, 2.0, None) — independent
"
```

Expected output:
```
(True, 2.0, None)
(True, 1.0, None)
(True, 0.0, None)
(False, 0.0, 1.0)
(True, 2.0, None)
```

### Step 3: Config Loader

**Branch:** `feat/config-loader`
**Files:** `config_loader.py`
**What:** Implement `load_config`, `load_scenario`, and `validate_request`. Parses JSON into typed structures.

**Definition of Done:**
```bash
python -c "
from config_loader import load_config, validate_request
from token_bucket import BucketConfig
cfg_data = {
    'default': {'capacity': 5, 'refill_rate': 1.0},
    'users': {'premium': {'capacity': 10, 'refill_rate': 5.0}}
}
cfg = load_config(cfg_data)
print(cfg.default.capacity, cfg.default.refill_rate)  # 5 1.0
print(cfg.users['premium'].capacity)                    # 10
user, time = validate_request({'user': 'alice', 'time': 0.5})
print(user, time)                                        # alice 0.5
"
```

Expected output:
```
5 1.0
10
alice 0.5
```

### Step 4: CLI Entry Point

**Branch:** `feat/cli`
**Files:** `rate_limiter.py`
**What:** Implement `main`, `parse_args`, `run_check`, `run_scenario`, and `format_response`. Wire all components together.

**Definition of Done — single check:**
```bash
python rate_limiter.py check --user alice --time 0.0
```

Expected output:
```json
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 4.0}
```

**Definition of Done — error handling:**
```bash
python rate_limiter.py check --user "" --time 0.0; echo "exit: $?"
```

Expected output:
```
Error: user ID must be a non-empty string
exit: 1
```

### Step 5: Scenario Files

**Branch:** `feat/scenarios`
**Files:** `scenarios/scenario_1.json` through `scenarios/scenario_5.json`
**What:** Create all 5 scenario files matching the spec's behavioral scenarios exactly.

**Definition of Done:**
```bash
python rate_limiter.py scenario --file scenarios/scenario_1.json
```

Expected output (Scenario 1 — burst then exhaustion and recovery):
```json
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 4.0}
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 3.0}
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 2.0}
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 1.0}
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 0.0}
{"user": "alice", "time": 0.0, "decision": "DENY", "remaining": 0.0, "retry_after": 1.0}
{"user": "alice", "time": 1.0, "decision": "ALLOW", "remaining": 0.0}
```

### Step 6: Validation Script

**Branch:** `feat/validation`
**Files:** `validate.py`
**What:** Implement the automated validation script that runs all 5 scenarios and compares output to expected values from the spec.

**Definition of Done:**
```bash
python validate.py
```

Expected output:
```
Scenario 1: Burst Then Exhaustion and Recovery ... PASS
Scenario 2: Per-User Independence ................. PASS
Scenario 3: Different Rate Limits Per User ........ PASS
Scenario 4: Lazy Refill Capped at Capacity ........ PASS
Scenario 5: Deny with Retry-After Timing .......... PASS

All 5 scenarios passed.
```

### Step 7: Demo Script

**Branch:** `feat/demo`
**Files:** `demo.py`
**What:** Implement the narrated demo that walks through the system's capabilities using different data than the validation scenarios.

**Definition of Done:**
```bash
python demo.py
```

Expected: narrated output showing (1) burst and exhaustion with recovery, (2) per-user independence, (3) premium vs. free tier differences. Each section has narration text explaining what is being demonstrated, followed by actual rate limiter output.

## Deviation Log

Empty at design time — populated during implementation.
