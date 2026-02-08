# Rate Limiter with Per-User Quotas

A software experiment demonstrating **token bucket rate limiting with per-user quota tracking**. Each user gets an independent token bucket that refills at a configurable rate and allows bursts up to a set capacity — enabling fine-grained control over per-user request rates.

This is not a product or library. It is a focused experiment built to answer one question: *can per-user rate limiting with independent, configurable token buckets be implemented correctly using lazy refill and no background threads?* The answer, validated across 5 behavioral scenarios, is yes.

## How It Works

The system is a command-line tool. You give it a user identifier, and it returns a JSON response: ALLOW (with remaining tokens) or DENY (with a `retry_after` value in seconds).

Each user has an independent bucket defined by two parameters:
- **capacity** — maximum tokens (burst size)
- **refill_rate** — tokens restored per second

Buckets are created on first use at full capacity. Token refill is **lazy** — calculated on demand when a request arrives, not via background timers. All state lives in-memory and does not persist across process invocations.

## Project Structure

```
rate-limiter/
  token_bucket.py       Core algorithm: token bucket with lazy refill
  quota_tracker.py      Per-user bucket registry and request checking
  config_loader.py      JSON config and scenario file parsing
  rate_limiter.py       CLI entry point (check and scenario commands)
  validate.py           Automated behavioral validation (5 scenarios)
  demo.py               Narrated demo with independent sample data
  scenarios/            Scenario JSON files matching the specification

docs/
  research.md           Domain research on rate limiting algorithms
  specification.md      Behavioral spec with requirements and scenarios
  design.md             Technical design with signatures and data flow
  validation-report.md  QA validation results and coverage matrix
```

For full details on requirements, design decisions, and validation results, see the files in `docs/`.

## Setup

**Prerequisites:** Python 3.9+

No dependencies to install — the project uses the Python standard library only.

```bash
git clone https://github.com/AndreaCadonna/rate_limiter_with_per-user_quotas.git
cd rate_limiter_with_per-user_quotas/rate-limiter
```

## Usage

### Single request check

```bash
python rate_limiter.py check --user alice --time 0.0
```

Output:
```json
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 4.0}
```

### Run a scenario from file

Scenario files define a config and a sequence of requests. The system processes them in order, maintaining state across requests within the same run.

```bash
python rate_limiter.py scenario --file scenarios/scenario_1.json
```

Output (one JSON object per line):
```json
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 4.0}
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 3.0}
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 2.0}
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 1.0}
{"user": "alice", "time": 0.0, "decision": "ALLOW", "remaining": 0.0}
{"user": "alice", "time": 0.0, "decision": "DENY", "remaining": 0.0, "retry_after": 1.0}
{"user": "alice", "time": 1.0, "decision": "ALLOW", "remaining": 0.0}
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid input (empty user, bad scenario format) |
| 2 | File not found |

## Validation

Run the automated validation script to verify all 5 behavioral scenarios from the specification:

```bash
python validate.py
```

All scenarios must pass for the experiment to be considered correct. See [`docs/validation-report.md`](docs/validation-report.md) for the full results and requirement coverage matrix.

## Demo

Run the narrated demo to see the core principle in action:

```bash
python demo.py
```

The demo walks through three independent demonstrations using different data than validation:
1. **Burst and recovery** — a user exhausts their bucket, waits, and regains access
2. **Per-user independence** — one user's exhaustion has zero effect on another
3. **Tier differences** — premium vs. free users with different capacity and refill rates

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/research.md`](docs/research.md) | Domain research on rate limiting algorithms and patterns |
| [`docs/specification.md`](docs/specification.md) | Behavioral specification with 6 requirements and 5 scenarios |
| [`docs/design.md`](docs/design.md) | Technical design with file structure, function signatures, and data flow |
| [`docs/validation-report.md`](docs/validation-report.md) | Validation results, requirement coverage, and deviations |
| [`PROJECT-PHILOSOPHY.md`](PROJECT-PHILOSOPHY.md) | Project philosophy governing scope, technology, and quality decisions |
