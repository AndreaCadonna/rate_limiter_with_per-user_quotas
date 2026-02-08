# Specification Phase — Prompt

## Context
Phase 2 of 5. Receives the research document from Phase 1.

## Agent
Load `workflow/agents/spec-writer.agent.md`

## Skills
- `spec-document` — provides the output format, requirement conventions, and quality checklist

## Input
**Research document:** Read `docs/research.md` — this is your sole input. All domain knowledge comes from here.

**Project philosophy:** Read `PROJECT-PHILOSOPHY.md` for scope and quality constraints.

## Task
1. Read the research document thoroughly. Identify the core principle and recommended algorithm.
2. Define 3-5 functional requirements (REQ-RL-NNN) that directly demonstrate the core principle. Each with a concrete example.
3. Define negative requirements — what the system explicitly does NOT do.
4. Write at least 3 behavioral scenarios with specific input values, actions, and expected outputs.
5. Define the CLI interface: input format, output format, exit codes.
6. Build the requirement coverage matrix mapping every requirement to its validation scenarios.
7. Produce the specification following the `spec-document` skill format.

## Output
A single markdown file: `docs/specification.md` following the spec-document skill template.

## Exit Criteria
All items in the `spec-document` skill's quality checklist pass.

## Gate
User reviews the specification before proceeding to the design phase.
