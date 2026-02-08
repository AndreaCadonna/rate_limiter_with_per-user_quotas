# Rate Limiter with Per-User Quotas — Research Document

## Core Principle

**Token bucket algorithm with per-user quota tracking** — each user gets an independent token bucket that refills at a fixed rate and allows bursts up to a configurable capacity, enabling fine-grained control over how many requests individual users can make within any time period.

## Domain Context

### What problem does rate limiting solve?

Any system that accepts requests from users faces a fundamental question: how do you prevent one user (or a group of users) from consuming so many resources that the system degrades for everyone else? **Rate limiting** is the mechanism that answers this question. It controls the number of requests a user can make within a given time period, rejecting requests that exceed the limit.

### Key terms

- **Rate limit**: A rule that restricts how many requests a user can make in a given time period. Example: "100 requests per minute."
- **Quota**: The total number of requests a user is allowed within a time window. Quotas are per-user — each user has their own independent count.
- **Time window**: The period over which requests are counted. Can be fixed (aligned to clock boundaries like the top of each minute) or sliding (a rolling period relative to each request).
- **Request**: A single action a user attempts. In our experiment, a request is simply a function call with a user identifier.
- **Allowed / Denied**: The two possible outcomes when a user makes a request. Allowed means the request proceeds; denied (also called "throttled" or "rate-limited") means it is rejected.
- **Token**: An abstract unit of permission. In the token bucket algorithm, each token permits one request. Tokens are consumed on use and regenerate over time.
- **Bucket**: A container that holds tokens. Each user has their own bucket with a fixed maximum capacity.
- **Refill rate**: The speed at which tokens are added back to a bucket, expressed as tokens per time unit (e.g., 10 tokens/second).
- **Capacity** (also called "burst size"): The maximum number of tokens a bucket can hold. This determines the largest burst of requests a user can make at once.
- **Burst**: A rapid sequence of requests sent in a short time, potentially exceeding the steady-state refill rate. Bursts are allowed as long as tokens are available.
- **429 Too Many Requests**: The standard HTTP status code returned when a request is rate-limited.

### Why per-user?

A global rate limit (e.g., "the system handles 1000 requests/second total") doesn't protect individual users from each other. One aggressive user could consume the entire quota. **Per-user rate limiting** gives each user their own independent limit, so one user's behavior doesn't affect another's access.

## Key Concepts

### Token Bucket Algorithm

The token bucket is the most widely-used rate limiting algorithm, employed by AWS, Stripe, and GitHub. It works by analogy to a physical bucket filled with tokens:

- A bucket starts full of tokens (up to its capacity).
- Each request consumes one token.
- Tokens are added back at a constant refill rate.
- When the bucket is empty, requests are denied until tokens refill.
- Tokens cannot exceed the bucket's capacity — excess tokens are discarded.

The algorithm naturally handles bursts: if a user has been idle, tokens accumulate up to capacity, allowing a burst of rapid requests. Over time, the effective rate converges to the refill rate.

**Why it matters to the core principle:** Token bucket provides two independent controls — capacity (burst size) and refill rate (sustained throughput) — making it expressive enough to demonstrate meaningful rate limiting behavior while remaining simple to implement and understand.

### Per-User Quota Tracking

Per-user tracking means maintaining independent rate-limiting state for each user identity. The standard implementation pattern is a **hash map** (dictionary) keyed by user identifier, where each value contains the algorithm-specific state for that user.

```
user_state = {
    "user_alice": { capacity: 10, tokens: 7, refill_rate: 1, last_refill: ... },
    "user_bob":   { capacity: 10, tokens: 10, refill_rate: 1, last_refill: ... },
}
```

When a request arrives, the system looks up the user's state, applies the algorithm, and updates the state. Users who have never been seen get a fresh bucket at full capacity. This means:

- Alice's request rate has zero effect on Bob's available quota.
- Each user's bucket refills independently based on elapsed time since their last request.
- Different users can have different capacity and refill rate configurations (e.g., free-tier vs. premium-tier quotas).

### Lazy Refill (Time-Based Token Calculation)

Rather than running a background timer to add tokens continuously, the standard implementation uses **lazy refill**: tokens are calculated on demand when a request arrives.

1. Record the timestamp of the last refill.
2. When a new request arrives, calculate elapsed time since the last refill.
3. Compute tokens to add: `elapsed_time * refill_rate`.
4. Cap at capacity: `tokens = min(capacity, tokens + tokens_to_add)`.
5. Update the last refill timestamp.

This avoids background threads and timers entirely — the system only does work when requests arrive.

## Algorithm / Mechanism Analysis

### How the Token Bucket Algorithm Works Step by Step

**State per bucket:**

| Field | Type | Description |
|-------|------|-------------|
| `capacity` | integer | Maximum tokens the bucket can hold |
| `tokens` | float | Current available tokens |
| `refill_rate` | float | Tokens added per second |
| `last_refill` | float | Timestamp of last refill calculation |

**On each request:**

```
1. Calculate elapsed time:
     elapsed = current_time - last_refill

2. Calculate tokens to add:
     tokens_to_add = elapsed * refill_rate

3. Refill the bucket (capped at capacity):
     tokens = min(capacity, tokens + tokens_to_add)

4. Update the refill timestamp:
     last_refill = current_time

5. Check if a token is available:
     if tokens >= 1:
         tokens = tokens - 1
         → ALLOW the request
     else:
         → DENY the request
```

**Per-user dispatch:** Before running the algorithm, look up the user's bucket in the hash map. If none exists, create a new bucket at full capacity.

### Alternative Algorithms Considered

Four other rate-limiting algorithms were evaluated. Each has different trade-offs.

#### Fixed Window Counter

**How it works:** Divide time into fixed intervals (e.g., every 60 seconds aligned to the clock). Maintain a counter per window. Increment on each request; deny if counter reaches the limit. Reset counter when the window advances.

**Example:** Limit = 5 requests per 60-second window.
- 12:00:00–12:01:00 is one window. User makes 5 requests → all allowed, counter = 5.
- 6th request → denied.
- 12:01:00 → window resets, counter = 0. User can make 5 more.

**Critical flaw — boundary spike:** A user can send 5 requests at 12:00:59 and 5 more at 12:01:01, achieving 10 requests in 2 seconds despite a "5 per minute" limit. The algorithm has no memory across window boundaries.

**Verdict:** Too simplistic for our experiment. The boundary problem makes it a poor demonstration of robust rate limiting.

#### Sliding Window Log

**How it works:** Store the timestamp of every request in a sorted list. On each new request, remove all timestamps older than `current_time - window_size`, then count remaining entries. If count < limit, allow and add the new timestamp; otherwise deny.

**Example:** Limit = 5 per 60 seconds. Request log: `[12:00:10, 12:00:25, 12:00:40, 12:00:55, 12:01:05]`. New request at 12:01:15 → remove entries before 12:00:15 → `[12:00:25, 12:00:40, 12:00:55, 12:01:05]` → count = 4 < 5 → allow.

**Strength:** Perfectly accurate with no boundary problems.
**Weakness:** Memory grows linearly with request volume — must store every timestamp. At 100 requests/minute per user across 10,000 users, that's 1 million timestamps in memory. Not practical at scale, and the memory overhead obscures the core concept.

**Verdict:** Accurate but the memory cost is disproportionate to the insight gained. Poor fit for an experiment focused on clarity.

#### Sliding Window Counter

**How it works:** A hybrid of fixed window and sliding window. Track request counts for the current and previous fixed windows. Estimate the sliding window count using weighted interpolation:

```
weight = 1 - (elapsed_time_in_current_window / window_size)
sliding_count = (previous_window_count * weight) + current_window_count
```

**Example:** Limit = 10 per 60 seconds. Previous window had 8 requests. Current window (15 seconds in) has 3 requests. Weight = 1 - (15/60) = 0.75. Sliding count = (8 * 0.75) + 3 = 9. Since 9 < 10 → allow.

**Strength:** Memory-efficient (only 2 counters per user), eliminates boundary spikes, ~99.997% accuracy in production (per Cloudflare's analysis).
**Weakness:** It's an approximation — assumes requests are evenly distributed within each window.

**Verdict:** Excellent production algorithm, but the weighted interpolation adds complexity without adding proportional insight for an experiment. The approximation nature makes it harder to explain and validate with exact expected outputs.

#### Leaky Bucket

**How it works:** Two variants exist.
- *Queue-based:* Incoming requests enter a FIFO queue. Requests "leak" (get processed) at a constant rate. If the queue is full, new requests are rejected.
- *Counter-based:* Similar to token bucket but inverted — tracks a "water level" that increases with each request and decreases over time.

**Example (counter-based):** Capacity = 5, leak rate = 1/second. Current level = 3. Request arrives → level would become 4 ≤ 5 → allow. If level were 5 → deny.

**Strength:** Guarantees perfectly smooth output rate.
**Weakness:** Cannot handle legitimate bursts — all spikes are flattened. The queue-based variant requires a background thread. The counter-based variant is essentially token bucket with inverted logic, adding little new insight.

**Verdict:** The queue variant adds unnecessary complexity (background threads). The counter variant is too similar to token bucket to justify as a separate choice. Burst suppression is a feature for production systems protecting downstream services, not a useful property for an experiment.

### Algorithm Comparison

| Property | Token Bucket | Fixed Window | Sliding Log | Sliding Counter | Leaky Bucket |
|----------|:---:|:---:|:---:|:---:|:---:|
| Memory per user | 4 values | 2 values | N timestamps | 3 values | 4 values |
| Accuracy | Exact | Poor (boundaries) | Perfect | ~99.997% | Exact |
| Handles bursts | Yes | Poorly | Yes | Yes | No |
| Implementation complexity | Low | Very low | Medium | Medium | Medium-High |
| Educational clarity | High | Low | Medium | Medium | Low |

### Recommendation: Token Bucket

The token bucket algorithm is the best fit for this experiment because:

1. **Clarity.** The mental model (bucket, tokens, refill) is intuitive and easy to explain with concrete examples.
2. **Two meaningful parameters.** Capacity and refill rate provide independent controls that can be varied in demonstrations.
3. **Burst behavior is visible.** Unlike leaky bucket (which hides bursts) or fixed window (which has boundary artifacts), token bucket's burst handling is deterministic and demonstrable.
4. **Minimal state.** Only 4 values per user (capacity, tokens, refill_rate, last_refill), making per-user tracking straightforward.
5. **No background processes.** Lazy refill means no timers, no threads, no concurrency complexity.
6. **Industry standard.** Used by AWS, Stripe, GitHub — validates that we're demonstrating a real pattern.

## Concrete Examples

### Example 1: Basic Rate Limiting with Refill

**Setup:** User "alice" has a bucket with capacity = 5, refill_rate = 1 token/second.

| Time (s) | Action | Tokens Before | Refill | Tokens After Refill | Consumed | Tokens After | Result |
|--------:|--------|------:|------:|------:|------:|------:|--------|
| 0.0 | (init) | — | — | 5.0 | — | 5.0 | — |
| 0.0 | request | 5.0 | 0.0 | 5.0 | 1 | 4.0 | ALLOW |
| 0.5 | request | 4.0 | 0.5 | 4.5 | 1 | 3.5 | ALLOW |
| 1.0 | request | 3.5 | 0.5 | 4.0 | 1 | 3.0 | ALLOW |
| 1.5 | request | 3.0 | 0.5 | 3.5 | 1 | 2.5 | ALLOW |
| 2.0 | request | 2.5 | 0.5 | 3.0 | 1 | 2.0 | ALLOW |
| 2.5 | request | 2.0 | 0.5 | 2.5 | 1 | 1.5 | ALLOW |
| 3.0 | request | 1.5 | 0.5 | 2.0 | 1 | 1.0 | ALLOW |
| 3.5 | request | 1.0 | 0.5 | 1.5 | 1 | 0.5 | ALLOW |
| 4.0 | request | 0.5 | 0.5 | 1.0 | 1 | 0.0 | ALLOW |
| 4.5 | request | 0.0 | 0.5 | 0.5 | 0 | 0.5 | DENY |
| 5.5 | request | 0.5 | 1.0 | 1.5 | 1 | 0.5 | ALLOW |

**Key observations:**
- The bucket starts full (5 tokens), allowing an initial burst.
- At t=4.5s, the 0.5 refilled tokens aren't enough for a full request → denied.
- After waiting 1 more second (t=5.5), enough tokens have accumulated → allowed again.
- The sustained rate converges to the refill rate (1 request/second).

### Example 2: Per-User Independence

**Setup:** Two users sharing the same system, each with capacity = 3, refill_rate = 1 token/second.

| Time (s) | User | Tokens Before | Refill | Tokens After | Result |
|--------:|------|------:|------:|------:|--------|
| 0.0 | alice | 3.0 | 0.0 | 2.0 | ALLOW |
| 0.0 | alice | 2.0 | 0.0 | 1.0 | ALLOW |
| 0.0 | alice | 1.0 | 0.0 | 0.0 | ALLOW |
| 0.0 | alice | 0.0 | 0.0 | 0.0 | DENY |
| 0.0 | bob | 3.0 | 0.0 | 2.0 | ALLOW |
| 1.0 | alice | 0.0 | 1.0 | 0.0 | ALLOW |
| 1.0 | bob | 2.0 | 1.0 | 2.0 | ALLOW |

**Key observations:**
- Alice exhausts her bucket at t=0. Bob is unaffected — his bucket is still full.
- Alice's denial has no impact on Bob's ability to make requests.
- At t=1.0, Alice's bucket has refilled 1 token, so she can make one more request.
- Each user's state is completely independent.

### Example 3: Burst Then Steady State

**Setup:** User "charlie" has capacity = 10, refill_rate = 2 tokens/second. Charlie sends 10 requests instantly, then 1 request every 0.5 seconds.

| Time (s) | Tokens Before | Refill | Tokens After | Result | Note |
|--------:|------:|------:|------:|--------|------|
| 0.0 | 10.0 | 0.0 | 9.0 | ALLOW | Burst start |
| 0.0 | 9.0 | 0.0 | 8.0 | ALLOW | |
| 0.0 | 8.0 | 0.0 | 7.0 | ALLOW | |
| 0.0 | 7.0 | 0.0 | 6.0 | ALLOW | |
| 0.0 | 6.0 | 0.0 | 5.0 | ALLOW | |
| 0.0 | 5.0 | 0.0 | 4.0 | ALLOW | |
| 0.0 | 4.0 | 0.0 | 3.0 | ALLOW | |
| 0.0 | 3.0 | 0.0 | 2.0 | ALLOW | |
| 0.0 | 2.0 | 0.0 | 1.0 | ALLOW | |
| 0.0 | 1.0 | 0.0 | 0.0 | ALLOW | Burst end (10 consumed) |
| 0.5 | 0.0 | 1.0 | 0.0 | ALLOW | Steady state begins |
| 1.0 | 0.0 | 1.0 | 0.0 | ALLOW | Sustainable at refill rate |
| 1.5 | 0.0 | 1.0 | 0.0 | ALLOW | |
| 2.0 | 0.0 | 1.0 | 0.0 | ALLOW | |

**Key observations:**
- The full capacity allows a burst of 10 instant requests.
- After the burst, the system transitions to steady state at the refill rate.
- At 1 request per 0.5s with a refill rate of 2/s, the user gets 1 token refilled per request — exactly sustainable.
- If the user tried 3 requests per second, they'd be denied every third request (only 2 tokens refill per second).

## Scope Boundaries

### In Scope

- **Token bucket algorithm implementation** — the core rate-limiting mechanism with lazy refill.
- **Per-user quota tracking** — independent buckets per user identity, managed via a hash map.
- **Configurable parameters** — capacity and refill rate, settable per user or with defaults.
- **Request allow/deny decisions** — the system accepts a user ID and returns whether the request is allowed or denied.
- **Remaining quota information** — report remaining tokens and time until next token on each request.
- **CLI interface** — command-line tool to exercise the rate limiter with structured output (JSON).
- **Behavioral validation** — automated scenarios that prove the algorithm works as specified.
- **Narrated demo** — a script that walks through the system's capabilities with real-looking data.

### Out of Scope

- **Other algorithms** — no fixed window, sliding window, or leaky bucket implementations. One algorithm demonstrated well beats four demonstrated poorly.
- **Persistence** — all state is in-memory. No database, no file-based storage. The experiment ends when the process exits.
- **Distributed rate limiting** — no Redis, no shared state across processes. Single-process, single-machine.
- **HTTP server or REST API** — the interface is CLI, not a web server. No need for a server to demonstrate the algorithm.
- **Authentication / authorization** — user identity is a plain string passed as input. No API keys, no auth tokens.
- **Concurrency / thread safety** — single-threaded execution. No locks, no atomic operations.
- **Memory cleanup / TTL** — no eviction of inactive user buckets. The experiment runs short-lived scenarios, not long-running servers.
- **Monitoring, metrics, logging frameworks** — no structured logging, no dashboards. Output is the interface.
- **Multiple rate limit tiers** — the spec may define different configurations per user, but there's no dynamic tier system or billing integration.
- **Request queuing** — denied requests are immediately rejected, not queued for later processing.

## Assumptions

- **Single-threaded execution.** The rate limiter runs in a single thread. No concurrent access to bucket state. This simplifies the implementation significantly and is appropriate for a CLI experiment.
- **Controllable time.** For testing and demonstration, we need to control "current time" rather than relying on real wall-clock time. This means the implementation should accept a time source that can be injected (a function or parameter), not hard-code `time.time()`.
- **User IDs are strings.** No validation of user identity. Any non-empty string is a valid user ID.
- **One token per request.** Each request costs exactly one token. No variable-cost requests.
- **Python 3.10+ as implementation language.** Standard library only. Python is well-suited for clarity-focused experiments.
- **In-memory state only.** All bucket state lives in a Python dictionary. No external storage.
- **Small user counts.** Demonstration scenarios involve 2-5 users, not thousands. Memory and performance are non-concerns.

## Open Questions

- **Should different users have different rate limits?** The algorithm supports it (each bucket can have independent capacity/refill_rate), but should the spec require it? This would demonstrate per-user configurability at the cost of slightly more complex setup. *Recommendation: yes, include at least two tiers (e.g., "free" and "premium") to showcase per-user configurability.*
- **What output format should the CLI use?** JSON is machine-readable and easy to validate. Plain text is more human-readable for the demo. *Recommendation: JSON for the rate limiter's programmatic output, with the demo script providing human-friendly narration around it.*
- **Should the system report "retry after" information?** When a request is denied, it's useful to know how long until the next token is available. This adds a small amount of implementation work but makes the system more demonstrable. *Recommendation: yes, include it — it's a natural property of the token bucket (time = 1 / refill_rate when tokens = 0).*
- **How should time be injected for testing?** Options: (a) pass a timestamp with each request, (b) use a clock object/function that can be swapped, (c) use a global time offset. *Recommendation: pass a callable time source to the rate limiter constructor, defaulting to `time.time`. Simple and explicit.*
