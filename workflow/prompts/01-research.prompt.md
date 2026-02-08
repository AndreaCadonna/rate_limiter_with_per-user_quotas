# Research Phase — Prompt

## Context
Phase 1 of 5 in the Rate Limiter with Per-User Quotas project. This is the first phase — there are no upstream artifacts.

## Agent
Load `workflow/agents/researcher.agent.md`

## Skills
- `research-document` — provides the output format and quality checklist

## Input
**Project idea:** Build a rate limiter with per-user quotas. The system should limit how many requests individual users can make within configurable time windows, using a well-known rate limiting algorithm.

**Project philosophy:** Read `PROJECT-PHILOSOPHY.md` for scope, technology, and quality constraints.

## Task
1. Research rate limiting algorithms (token bucket, sliding window, fixed window, leaky bucket). Explain how each works with concrete numeric examples.
2. Research per-user quota tracking — how to maintain independent rate limits per user identity.
3. Compare the algorithms. Recommend one (with justification) that best demonstrates the core principle for an experiment-sized project.
4. Identify the core principle in 1-2 sentences.
5. Define scope boundaries: what's in, what's out, aligned with the project philosophy.
6. List assumptions and open questions for the spec phase.
7. Produce the research document following the `research-document` skill format.

## Output
A single markdown file: `docs/research.md` following the research-document skill template.

## Exit Criteria
All items in the `research-document` skill's quality checklist pass.

## Gate
User reviews the research document before proceeding to the specification phase.
