# Design Phase — Prompt

## Context
Phase 3 of 5. Receives the specification from Phase 2.

## Agent
Load `workflow/agents/architect.agent.md`

## Skills
- `design-document` — provides the output format, design conventions, and quality checklist
- `git-flow` — provides branching and commit conventions for the implementation plan

## Input
**Specification:** Read `docs/specification.md` — this is your primary input.

**Research document:** Read `docs/research.md` — for algorithm details and domain context.

**Project philosophy:** Read `PROJECT-PHILOSOPHY.md` for technology and architecture constraints.

## Task
1. Choose a programming language and justify the choice (boring, minimal, standard-library-first).
2. List all external dependencies (ideally none). Justify each one.
3. Design the file structure (5-15 files). Every file has a purpose tied to a spec requirement.
4. Design each component: function signatures with types, data structures, and requirement traceability.
5. Map the data flow from CLI input to output.
6. Create the ordered implementation plan:
   - Each step gets a feature branch name
   - Each step lists which files it creates/modifies
   - Each step has a "Definition of Done" with a literal command and expected output
7. Plan the validation script structure and demo script structure.
8. Produce the design document following the `design-document` skill format.

## Output
A single markdown file: `docs/design.md` following the design-document skill template.

## Exit Criteria
All items in the `design-document` skill's quality checklist pass.

## Gate
User reviews the design before proceeding to the implementation phase.
