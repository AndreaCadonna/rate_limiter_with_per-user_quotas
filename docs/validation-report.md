# Rate Limiter with Per-User Quotas — Validation Report

## Environment
- **Date:** 2026-02-08
- **Language/Runtime:** Python 3.9.4
- **Setup:** Clean checkout of `develop` branch. No virtual environment needed — standard library only. All commands run from `rate-limiter/` directory.

## Validation Results

| Scenario | Requirement(s) | Result | Notes |
|----------|----------------|--------|-------|
| Scenario 1: Burst Then Exhaustion and Recovery | REQ-RL-001, REQ-RL-002, REQ-RL-003, REQ-RL-006 | PASS | All 7 responses match spec exactly. Burst allows 5, denies 6th with retry_after=1.0, recovers at t=1.0. |
| Scenario 2: Per-User Independence | REQ-RL-001, REQ-RL-002, REQ-RL-004, REQ-RL-006 | PASS | All 8 responses match spec exactly. Alice exhaustion has zero effect on Bob. Both refill independently at t=1.0. |
| Scenario 3: Different Rate Limits Per User | REQ-RL-001, REQ-RL-002, REQ-RL-004, REQ-RL-005, REQ-RL-006 | PASS | All 10 responses match spec exactly. premium_user (capacity=10) vs. free_user (capacity=5) operate independently with correct configs. |
| Scenario 4: Lazy Refill Capped at Capacity | REQ-RL-001, REQ-RL-003 | PASS | Both responses match spec exactly. 10-second gap refills to capacity (5), not beyond. |
| Scenario 5: Deny with Retry-After Timing | REQ-RL-001, REQ-RL-002, REQ-RL-003 | PASS | All 6 responses match spec exactly. retry_after=0.5 at t=0.0, retry_after=0.25 at t=0.25, ALLOW at t=0.5. |

### Additional Verifications

| Check | Result | Notes |
|-------|--------|-------|
| Exit code 0 on success | PASS | Scenario mode returns 0 for all valid scenario files. |
| Exit code 1 on empty user | PASS | `check --user "" --time 0.0` returns exit code 1 with error message. |
| Exit code 2 on missing file | PASS | `scenario --file nonexistent.json` returns exit code 2 with error message. |
| No background threads | PASS | Grep for thread/threading/async/Timer finds zero matches. |
| No file persistence | PASS | Grep for file write/pickle/sqlite/persist finds zero matches. |
| Standard library only | PASS | No external imports in any source file. |

## Requirement Coverage

| Requirement | Covered By | Status |
|------------|-----------|--------|
| REQ-RL-001: Token Consumption and Allow | Scenario 1 (5 ALLOW responses), Scenario 2, 3, 4 | Verified |
| REQ-RL-002: Deny on Insufficient Tokens | Scenario 1 (request 6), Scenario 2 (request 4), Scenario 3 (request 9), Scenario 5 (requests 4-5) | Verified |
| REQ-RL-003: Lazy Token Refill | Scenario 1 (t=1.0 recovery), Scenario 4 (t=10.0 cap), Scenario 5 (fractional refill at t=0.25, t=0.5) | Verified |
| REQ-RL-004: Independent Per-User Buckets | Scenario 2 (alice/bob), Scenario 3 (premium_user/free_user) | Verified |
| REQ-RL-005: Configurable Per-User Rates | Scenario 3 (premium_user capacity=10, refill_rate=5 vs. default capacity=5, refill_rate=1) | Verified |
| REQ-RL-006: First-Request Bucket Creation | Scenario 1 (alice first request at full capacity), Scenario 2 (alice and bob), Scenario 3 (premium_user and free_user) | Verified |

## Deviations Found

### DEV-001: `from __future__ import annotations` (documented in design)
- **Severity:** None
- **Description:** Runtime Python is 3.9.4; the spec assumes 3.10+. The `float | None` union syntax in type hints fails at runtime on 3.9. Adding `from __future__ import annotations` makes annotations lazy strings, enabling 3.10+ syntax. No behavioral change.
- **Files:** All `.py` files

### DEV-002: `demo.py` uses direct imports instead of subprocess calls (documented in design)
- **Severity:** None
- **Description:** The design specified subprocess calls for demo, but since state is in-memory and doesn't persist across process invocations, multi-request demos require direct imports to maintain bucket state within a single process. Demo 3 (tier differences) uses scenario mode which does work as a subprocess.
- **Files:** `demo.py`

### No undocumented deviations found.

## Demo Verification
- [x] Demo runs without errors
- [x] Demo uses different data than validation (diana/eve/frank/gold_user/basic_user vs. alice/bob/premium_user/free_user)
- [x] Demo narrates the core principle clearly (burst/recovery, per-user independence, tier differences)
- [x] A stranger could understand the core principle from the demo alone

## Verdict
**PASS**

All 5 behavioral scenarios from the specification pass with exact output match. All 6 requirements (REQ-RL-001 through REQ-RL-006) are covered by at least one passing scenario. Exit codes match the specification (0 for success, 1 for invalid input, 2 for file not found). Negative requirements verified (no threading, no persistence, no external dependencies). Two deviations found — both previously documented in the design document with valid rationale and zero behavioral impact. The demo runs cleanly, uses different data than validation, and narrates the core principle (token bucket with per-user quotas) through three independent demonstrations.
