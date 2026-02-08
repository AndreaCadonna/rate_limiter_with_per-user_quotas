# Implementation Phase — Prompt

## Context
Phase 4 of 5. Receives the design document from Phase 3.

## Agent
Load `workflow/agents/developer.agent.md`

## Skills
- `code-quality` — provides coding standards and conventions
- `git-flow` — provides branching and commit conventions

## Input
**Design document:** Read `docs/design.md` — this is your blueprint. Follow it exactly.

**Specification:** Read `docs/specification.md` — for requirement IDs and behavioral expectations.

## Task
1. Set up the git branching structure: ensure `develop` branch exists from `main`.
2. Follow the implementation plan in `docs/design.md` step by step, in order:
   a. Create the feature branch specified for this step
   b. Implement the code as designed (file structure, function signatures, data structures)
   c. Add file-level comments referencing spec requirements (Fulfills: REQ-RL-NNN)
   d. Run the "Definition of Done" command — do not proceed until it passes
   e. Self-review: run code, check against design, check against spec, remove artifacts
   f. Commit with conventional commit message, push to remote
   g. Open a pull request to `develop` via `gh pr create`. STOP and wait for user review and merge confirmation before starting the next step.
   h. After merge is confirmed, pull develop locally and delete the feature branch.
3. Log any deviations in the deviation log section of `docs/design.md`.
4. After all steps complete, open a pull request from `develop` to `main`. STOP and wait for user review and merge confirmation.

## Output
- Working code in the repository, committed and pushed
- Updated `docs/design.md` with deviation log (if any deviations occurred)

## Exit Criteria
- Every implementation step's "Definition of Done" passes
- All code committed and pushed
- No dead code, debug artifacts, or TODO comments
- All items in the `code-quality` skill's quality checklist pass

## Gate
User reviews the code before proceeding to the validation phase.
