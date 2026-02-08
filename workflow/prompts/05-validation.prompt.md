# Validation Phase — Prompt

## Context
Phase 5 of 5. Receives the working code from Phase 4.

## Agent
Load `workflow/agents/qa-engineer.agent.md`

## Skills
- `validation-report` — provides the validation script structure, demo script structure, report format, and quality checklist
- `git-flow` — provides conventions for the validation branch and final merge

## Input
**Specification:** Read `docs/specification.md` — this is your source of truth. Work from the spec, not the code.

**Design document:** Read `docs/design.md` — for setup instructions and expected file structure.

**Working code:** The implemented system in the repository.

## Task
1. Create feature branch `feat/validation`.
2. Set up a clean environment following the design document's setup instructions.
3. Write `validate.sh`:
   - One test per behavioral scenario from the spec
   - Each test runs the system with specific input and compares output to expected values
   - Reports pass/fail per scenario, summary at end
   - Exit code 0 if all pass, 1 if any fail
4. Run `validate.sh` and record all results.
5. Write `demo.sh`:
   - Uses different data than validation
   - Narrated: explains what's happening and why at each step
   - Tells the story of the core principle
   - Runnable by a stranger
6. Run `demo.sh` and verify it works.
7. Check every requirement in the spec's coverage matrix — confirm each is covered by a passing scenario.
8. Document any deviations between spec and implementation.
9. Produce the validation report following the `validation-report` skill format.
10. Commit validation scripts and report on the feature branch. Open a pull request to `develop` via `gh pr create`. STOP and wait for user review and merge confirmation.
11. If PASS: after merge is confirmed, open a pull request from `develop` to `main`. STOP and wait for user review and merge confirmation. After merge, tag as `v1.0.0`.

## Output
- `validate.sh` — automated validation script
- `demo.sh` — narrated demo script
- `docs/validation-report.md` — the validation report with verdict

## Exit Criteria
All items in the `validation-report` skill's quality checklist pass.

## Gate
User reviews the validation report and accepts or rejects the verdict.
