# The Builder's Guide to Agentic Workflows

How to design, assemble, and run AI-agent-driven software projects using the **Agent / Prompt / Skill** separation of concerns.

---

## Who This Guide Is For

You have a project idea and want AI agents to build it. You need to decide: what files do I create, what goes in each, and how do I assemble them into a working pipeline? This guide walks you through that process from zero to running workflow.

---

## Part 1 — The Mental Model

### Three Primitives, Three Questions

Every piece of context you give an LLM falls into exactly one of three categories:

| Primitive | Question It Answers | Changes Between... | Analogy |
|-----------|--------------------|--------------------|---------|
| **Agent** | WHO is doing this? | Rarely — reusable across projects | A job description |
| **Skill** | HOW should it be done? | Sometimes — shared across phases | A training manual |
| **Prompt** | WHAT do I need right now? | Every task — unique per instance | A work order |

### The Assembly Rule

For any task, you assemble exactly **one agent + one prompt + one or more skills**:

```
┌─────────────────────────────────────────────┐
│ CONTEXT WINDOW                              │
│                                             │
│  Agent    → shapes thinking and behavior    │
│  Skill(s) → provides knowledge and formats  │
│  Prompt   → defines the specific task       │
│                                             │
└─────────────────────────────────────────────┘
```

### The Scoping Rule

**Load only what the current task needs.** An agent performing a research task does not need the git-flow skill. A developer writing code does not need the validation report format. Every file in context that isn't relevant to the current task is noise that dilutes attention.

Ask: "If I removed this file from context, would the output quality drop?" If no, remove it.

---

## Part 2 — What Goes in Each File

### Agent Files (`.agent.md`)

An agent defines a **thinking style**, not a task.

**Include:**
- Identity — role name, one-line description
- Mission — single sentence purpose
- Operating context — pipeline position, what it receives, what it produces
- Behavioral rules — HOW to think, prioritize, make decisions (numbered, 5-15 rules)
- Decision framework — ordered priorities for resolving ambiguity
- Anti-patterns — explicit "do NOT do this" list
- Self-review protocol — 3-5 meta-checks the agent runs on its own output

**Exclude:**
- Output format templates (→ skill)
- Domain conventions (→ skill)
- Task-specific steps (→ prompt)
- Quality checklists for specific deliverables (→ skill)

**Size target:** 50-90 lines. If it's longer, you're probably embedding skills or prompt logic.

**Reusability test:** Could this agent receive a different prompt and still behave consistently? A "Developer" agent should work whether the prompt says "implement from scratch" or "fix this bug" or "add this feature."

### Skill Files (`.skill.md`)

A skill defines **reusable knowledge** — conventions, formats, techniques.

**Include:**
- Purpose — what this skill helps you do (one sentence)
- When to use — what triggers loading this skill
- Conventions — numbered rules, standards, patterns
- Output template — exact structure/skeleton of deliverables (if applicable)
- Quality checklist — self-review criteria in checkbox format

**Exclude:**
- Identity or behavioral personality (→ agent)
- Task-specific instructions or steps (→ prompt)
- Input data or placeholders (→ prompt)

**Size target:** 70-270 lines depending on complexity. Format-heavy skills (document templates) are longer. Convention-only skills (code quality) are shorter.

**Reusability test:** Could multiple agents in different phases use this skill? `git-flow.skill.md` is used by the architect (planning), developer (executing), and QA engineer (auditing).

### Prompt Files (`.prompt.md`)

A prompt defines **one specific task** with its concrete inputs.

**Include:**
- Context — what phase, what pipeline, what the goal is
- Skills — which skill files to load (by name, with reason)
- Input — placeholders for upstream artifacts or user data
- Task — ordered steps for this specific task
- Output — what to produce (reference the skill for format details)
- Exit criteria — when the task is done (reference the skill's quality checklist)

**Exclude:**
- Output format skeleton (→ skill)
- Domain conventions (→ skill)
- Behavioral rules (→ agent)
- Quality checklists (→ skill)

**Size target:** 40-110 lines. The prompt is the lightest file. If it's long, you're embedding skill content.

**Uniqueness test:** Is this prompt consumed once for one specific task instance? Prompts are disposable — you fill in the placeholders, send it, and it's done.

---

## Part 3 — Universal Principles

These apply to every project, regardless of size or domain. They are hard-won lessons from running agentic workflows.

### 3.1 Spec-Driven Development

**Every project benefits from defining behavior before writing code.** Even a tiny experiment.

Why: LLM agents are eager to start coding. Without a spec, they invent requirements as they go, resulting in inconsistent behavior and untestable output. A spec — even a lightweight one — creates a contract.

Minimum viable spec:
- What the system does (3-5 "The system shall..." statements)
- Example inputs and expected outputs (2-3 concrete scenarios)
- What the system does NOT do

This takes 10 minutes to write and saves hours of debugging inconsistent agent output.

### 3.2 Git Discipline

**Every project that produces code should use git with disciplined practices.**

Non-negotiable basics:
- **Branch per task.** Never commit directly to main or develop.
- **Small, atomic commits.** One logical change per commit. Every commit leaves code runnable.
- **Conventional commit messages.** `type(scope): subject` — parseable, searchable, meaningful.
- **Push after every commit.** The remote is backup and audit trail. Agent sessions can crash.
- **Merge with `--no-ff`.** Preserve the feature branch history in the log.

Why this matters for agents specifically: LLM agents can lose context, crash mid-session, or produce subtly broken code. Git discipline means you can always roll back to the last known good state, understand what changed between working and broken, and resume from where the agent left off.

### 3.3 Code Review Before Committing

**The agent should review its own code before committing.**

This is not a full code review process — it's a self-check gate:

1. **Run the code.** Does it execute without errors?
2. **Check against the design.** Do function signatures, types, and file structure match?
3. **Check against the spec.** Does the behavior match what was specified?
4. **Remove artifacts.** No debug prints, no commented-out code, no TODOs.
5. **Stage intentionally.** `git diff --staged` before committing. Know what you're committing.

Build this into your developer agent's behavioral rules, not as a separate phase.

### 3.4 Incremental Verification

**Every implementation step should produce a verifiable result.**

The "Definition of Done" pattern: every task ends with a literal command and its expected output. The agent runs this before moving on. This catches drift early — before broken code compounds across steps.

Bad: "Step 3: Implement the search engine."
Good: "Step 3: Implement query tokenization and index lookup. Definition of done: `python main.py search 'hello world'` → `Found 2 results: doc1.txt, doc3.txt`"

### 3.5 Deviation Logging

**Every difference from the plan must be documented, no matter how small.**

When an agent deviates — adds a helper function, changes a return type, uses a different library — it must log: what the plan said, what it did instead, why, and what's affected.

This is the safety net. When something breaks downstream, the deviation log is where you look first.

### 3.6 Traceability

**You should be able to trace any piece of code back to the requirement that demanded it.**

The chain: requirement → design component → implementation step → commit → code file. If you can't trace a piece of code back to a requirement, it's either unnecessary or under-specified.

For small projects, this can be lightweight: comments in code referencing requirement IDs, commit messages with `Fulfills: REQ-XX-NNN`. For large projects, use coverage tables.

### 3.7 Independent Validation

**The agent that writes the code should not be the only agent that judges it.**

Self-assessment is always optimistic. A separate validation step — different agent, different prompt, same spec — catches the gaps between "I think this works" and "this actually works."

Even for small projects: at minimum, write an automated script that runs spec scenarios end-to-end.

---

## Part 4 — How to Design Your Workflow

### Step 1 — Define the Process

Before creating any files, answer these questions:

**What am I building?**
- New system from scratch → full pipeline (research → spec → design → implement → validate)
- Adding feature to existing system → partial pipeline (spec update → design update → implement → validate)
- Fixing a bug → minimal pipeline (validate → implement → validate)
- Exploring a concept → compressed pipeline (research+spec → implement → demo)

**How complex is it?**
- Simple (1-3 files, single concept) → 2-3 phases, can combine agent roles
- Medium (5-15 files, multiple components) → 4-5 phases, dedicated agents
- Large (15+ files, multiple subsystems) → full pipeline, possibly with sub-phases

**What phases do I need?**

| Phase | Always Needed? | Skip When... |
|-------|---------------|-------------|
| Research | No | You already understand the domain deeply |
| Specification | **Yes** | Never skip — even a minimal spec helps |
| Design | No | Project is small enough that design is obvious (1-3 files) |
| Implementation | **Yes** | You're not producing code |
| Validation | Strongly recommended | The deliverable is a document, not software |

### Step 2 — Identify Agent Personalities

For each phase in your process, define the agent:

**Ask:** What role would a human fill for this phase?

| If the phase involves... | The agent is a... | Key behavioral trait |
|--------------------------|------------------|---------------------|
| Understanding a domain | Researcher | Curiosity + scope discipline |
| Defining behaviors | Spec Writer | Precision + completeness |
| Making technical decisions | Architect | Simplicity bias + thoroughness |
| Writing code | Developer | Fidelity + discipline |
| Verifying correctness | QA Engineer | Independence + evidence-based judgment |
| Reviewing code/docs | Reviewer | Constructiveness + attention to detail |
| Writing documentation | Technical Writer | Clarity + audience awareness |

**Can I combine agents?** Yes, for small projects:
- Researcher + Spec Writer → "Analyst" (understands domain AND writes precise requirements)
- Architect + Developer → "Builder" (makes decisions AND writes code — be careful, this reduces the plan-then-execute discipline)
- QA + Demo Builder → "Validator" (verifies AND demonstrates)

**Rules for combining:**
- Never combine Producer + Reviewer of the same artifact. The developer should not validate their own code.
- Only combine when the behavioral rules don't conflict. A researcher's "explore broadly" conflicts with a developer's "follow the plan exactly."

### Step 3 — Identify Skills Needed

**Start from the outputs, work backwards:**

For each artifact your pipeline produces, ask:
1. Does this artifact have a specific format? → **Document format skill**
2. Does producing this artifact require domain conventions? → **Convention skill**
3. Does producing this artifact require technical standards? → **Quality skill**

**Common skill patterns:**

| Output Type | Skills Needed |
|------------|--------------|
| Research document | Document format skill |
| Specification | Document format skill |
| Technical design | Document format skill + git planning conventions |
| Working code | Code quality skill + git execution conventions |
| Validation report | Report format skill + validation technique skill |
| Any code output | Git flow skill (always) |

**The skill catalog question:** Before creating a new skill, check if an existing one covers it. Skills should be reused across projects where the conventions are the same. If your git conventions don't change between projects, use the same git-flow skill.

### Step 4 — Design the Prompts

For each phase, define the task:

1. **What inputs does this phase receive?** (upstream artifacts, user data, configuration)
2. **What steps does the agent follow?** (ordered, specific, unambiguous)
3. **What does this phase produce?** (reference the skill for format)
4. **When is this phase done?** (reference the skill's quality checklist)

**Keep prompts thin.** The prompt says WHAT to do. The skill says HOW to format it. The agent says HOW to think about it. If you find yourself writing format templates or behavioral rules in the prompt, extract them.

### Step 5 — Define the Handoffs

For each phase transition, define:
- What artifact passes from phase N to phase N+1
- What the receiving agent needs to verify before starting
- What the user reviews at the gate (if anything)

**The handoff test:** If you gave the output artifact to a brand new agent instance with zero conversation history, plus the relevant agent.md and skill files, could it execute the next phase? If not, the artifact is incomplete.

---

## Part 5 — Project Setup Procedure

### For a New Project

```
1. Read this guide (you're doing this now)

2. Answer the Step 1-5 questions from Part 4

3. Create your project workflow directory:
   project-name/
   ├── workflow/
   │   ├── agents/     ← one .agent.md per role
   │   ├── prompts/    ← one .prompt.md per phase
   │   └── skills/     ← one .skill.md per knowledge domain
   └── [project files will go here]

4. Write or copy your agent files
   - Start from existing agents if the role matches
   - Customize behavioral rules for your project context

5. Write or copy your skill files
   - Reuse existing skills where conventions match
   - Create new skills only for project-specific conventions

6. Write your prompt files
   - One per phase
   - Reference skills by name
   - Include input placeholders

7. Create the remote git repository

8. Run Phase 0 (or whichever phase you're starting from)
```

### Framework-Specific Directory Layouts

The generic `workflow/` directory is where you **author and maintain** your files. But for an agentic framework to actually discover and load them, the files must be placed where the framework looks. Below is the mapping for each supported framework.

**Key insight:** All three frameworks now support the **Agent Skills open standard** (SKILL.md with YAML frontmatter). Skills are portable across tools. Instructions and agents differ per framework but the underlying content is the same — you're just placing it where each tool expects to find it.

#### Claude Code

Claude Code uses a `.claude/` directory at the project root, plus a `CLAUDE.md` file for always-loaded instructions. It also reads `CLAUDE.md` files in parent directories recursively and loads nested `CLAUDE.md` files on demand when accessing subdirectories.

```
project-name/
├── CLAUDE.md                          ← main project instructions (always loaded)
├── .claude/
│   ├── CLAUDE.md                      ← alternative location for main instructions
│   ├── rules/                         ← auto-loaded rule files (same priority as CLAUDE.md)
│   │   ├── code-style.md
│   │   ├── git-conventions.md
│   │   └── testing.md
│   └── skills/                        ← project skills (loaded on demand)
│       ├── git-flow/
│       │   └── SKILL.md
│       ├── code-quality/
│       │   └── SKILL.md
│       └── spec-document/
│           └── SKILL.md
├── workflow/                           ← your authoring source (not loaded by Claude Code)
│   ├── agents/
│   ├── prompts/
│   └── skills/
└── [project files]
```

**How our primitives map to Claude Code:**

| Our Primitive | Claude Code Mechanism | Where to Place |
|---------------|----------------------|----------------|
| **Agent** | `CLAUDE.md` or `.claude/rules/*.md` | Merge agent behavioral rules into `CLAUDE.md` or split into rule files. These are always loaded at session start. |
| **Skill** | `.claude/skills/<name>/SKILL.md` | One directory per skill. SKILL.md needs YAML frontmatter (`name` and `description`). Claude loads them on demand when relevant. |
| **Prompt** | User message (paste) or `/slash-command` | Prompts are given directly in the conversation. You can also create a skill with `invocation: user` to make it a `/command`. |

**Loading behavior:**
- `CLAUDE.md` and `.claude/rules/` files are loaded **automatically at session start** — keep them concise.
- `.claude/skills/` are loaded **on demand** when the task matches the skill description — safe to have many.
- Claude Code recurses upward from cwd, reading any `CLAUDE.md` it finds (useful for monorepos).
- Personal preferences go in `~/.claude/CLAUDE.md` (loaded for all projects).
- Personal skills go in `~/.claude/skills/` (available across all projects).

**Practical setup:**

```bash
# Initialize CLAUDE.md
cd project-name
claude  # then run /init to auto-generate CLAUDE.md

# Add skills
mkdir -p .claude/skills/git-flow
# Copy and adapt your skill content into SKILL.md with frontmatter:
# ---
# name: git-flow
# description: Git branching, commit conventions, and merge strategy.
#   Use when creating branches, writing commits, or merging.
# ---
# [skill content here]

# Add rules (always loaded)
mkdir -p .claude/rules
# Split agent behavioral rules into focused rule files
```

---

#### GitHub Copilot CLI

Copilot CLI reads from `.github/` for instructions, and `.github/skills/` or `.claude/skills/` for skills. It also supports `AGENTS.md` files at the repo root and in subdirectories.

```
project-name/
├── AGENTS.md                           ← primary agent instructions (always loaded)
├── .github/
│   ├── copilot-instructions.md         ← repo-wide instructions (always loaded)
│   ├── instructions/                   ← path-specific instructions
│   │   ├── code-style.instructions.md
│   │   └── testing.instructions.md
│   ├── skills/                         ← project skills (loaded on demand)
│   │   ├── git-flow/
│   │   │   └── SKILL.md
│   │   ├── code-quality/
│   │   │   └── SKILL.md
│   │   └── spec-document/
│   │       └── SKILL.md
│   ├── prompts/                        ← reusable prompt files (VS Code / IDE only)
│   │   ├── research.prompt.md
│   │   └── validate.prompt.md
│   └── agents/                         ← custom agent profiles
│       ├── researcher.agent.md
│       ├── developer.agent.md
│       └── qa-engineer.agent.md
├── workflow/                            ← your authoring source
│   ├── agents/
│   ├── prompts/
│   └── skills/
└── [project files]
```

**How our primitives map to Copilot CLI:**

| Our Primitive | Copilot CLI Mechanism | Where to Place |
|---------------|----------------------|----------------|
| **Agent** | `AGENTS.md` (root or subdirectory), or `.github/agents/<name>.agent.md` | `AGENTS.md` is always loaded. Custom agents in `.github/agents/` can be invoked with `@agent-name`. |
| **Skill** | `.github/skills/<name>/SKILL.md` | Same open standard as Claude Code. SKILL.md with YAML frontmatter. Loaded on demand. Also reads `.claude/skills/` for backward compatibility. |
| **Prompt** | User message (paste), or `.github/prompts/<name>.prompt.md` (VS Code/IDE) | Prompt files can be invoked with `/prompt-name` in VS Code. In CLI, paste the prompt content directly. |

**Loading behavior:**
- `.github/copilot-instructions.md` is loaded **automatically** for every request — keep it concise.
- `AGENTS.md` at repo root is treated as **primary instructions** (high priority).
- `AGENTS.md` in subdirectories are treated as **additional instructions** (lower priority, nearest takes precedence).
- `.github/instructions/*.instructions.md` files can use `applyTo` YAML frontmatter to target specific file patterns.
- `.github/skills/` skills are loaded **on demand** when relevant.
- Personal instructions go in `$HOME/.copilot/copilot-instructions.md`.
- Copilot CLI also reads `CLAUDE.md` and `GEMINI.md` at repo root.

**Practical setup:**

```bash
cd project-name
mkdir -p .github/skills .github/instructions .github/agents

# Repo-wide instructions (always loaded)
# Merge your universal agent rules + project overview here
cat > .github/copilot-instructions.md << 'EOF'
# Project conventions
- Use conventional commits: type(scope): subject
- Branch from develop, merge with --no-ff
- Follow spec-driven development
EOF

# Path-specific instructions (loaded when working on matching files)
cat > .github/instructions/code-style.instructions.md << 'EOF'
---
applyTo: "**/*.py"
---
Follow PEP 8. Prefer explicit over implicit.
EOF

# Skills (same SKILL.md format as Claude Code)
mkdir -p .github/skills/git-flow
# Copy SKILL.md with frontmatter
```

---

#### OpenAI Codex CLI

Codex reads `AGENTS.md` files hierarchically from the repo root down to the current working directory. It supports `.agents/skills/` for skills and `.codex/config.toml` for configuration.

```
project-name/
├── AGENTS.md                           ← primary project instructions (always loaded)
├── .agents/
│   └── skills/                         ← project skills (loaded on demand)
│       ├── git-flow/
│       │   └── SKILL.md
│       ├── code-quality/
│       │   └── SKILL.md
│       └── spec-document/
│           └── SKILL.md
├── .codex/
│   └── config.toml                     ← project-level Codex configuration
├── workflow/                            ← your authoring source
│   ├── agents/
│   ├── prompts/
│   └── skills/
└── [project files]
```

**How our primitives map to Codex CLI:**

| Our Primitive | Codex Mechanism | Where to Place |
|---------------|----------------|----------------|
| **Agent** | `AGENTS.md` (root, subdirectories, or `AGENTS.override.md`) | Codex walks from repo root to cwd, loading one file per directory. Root = primary, deeper = more specific. |
| **Skill** | `.agents/skills/<name>/SKILL.md` | Same open standard. SKILL.md with YAML frontmatter. Codex loads them on demand or via explicit `$skill-name` invocation. |
| **Prompt** | User message (paste or pipe via `codex exec`) | Codex has no native prompt-file mechanism. Paste prompt content directly, or use `codex exec "prompt text"` for non-interactive mode. |

**Loading behavior:**
- `AGENTS.md` discovery is **hierarchical**: Codex walks from repo root to cwd, including one file per directory (checks `AGENTS.override.md` first, then `AGENTS.md`).
- Files closer to cwd appear later in the combined prompt and **override** earlier guidance.
- Combined instructions are capped at `project_doc_max_bytes` (default 32 KiB) — keep them concise.
- `.agents/skills/` skills are loaded **on demand** when relevant to the task, or explicitly via `$skill-name`.
- Global defaults go in `~/.codex/AGENTS.md` (loaded for all projects).
- Global skills go in `~/.codex/skills/`.
- Use `AGENTS.override.md` for temporary overrides without editing the base file.

**Practical setup:**

```bash
cd project-name
mkdir -p .agents/skills

# Primary instructions (always loaded)
cat > AGENTS.md << 'EOF'
# Project Conventions
- Use conventional commits: type(scope): subject
- Branch from develop, merge with --no-ff
- Follow spec-driven development
- Run tests before committing
EOF

# Skills (same SKILL.md format)
mkdir -p .agents/skills/git-flow
# Copy SKILL.md with frontmatter

# Optional: increase instruction size limit
mkdir -p .codex
cat > .codex/config.toml << 'EOF'
project_doc_max_bytes = 65536
EOF
```

---

#### Cross-Framework Compatibility

Since all three tools support the Agent Skills open standard, you can maintain **one set of skill files** and make them available to whichever tool you use:

```
project-name/
├── CLAUDE.md                      ← Claude Code reads this
├── AGENTS.md                      ← Copilot CLI + Codex read this
├── .github/
│   ├── copilot-instructions.md    ← Copilot-specific instructions
│   └── skills/ ──────────┐
├── .claude/                │       symlink or copy
│   └── skills/ ───────────┤
├── .agents/                │
│   └── skills/ ───────────┘       ← all point to same SKILL.md files
├── workflow/                       ← authoring source (framework-agnostic)
│   ├── agents/
│   ├── prompts/
│   └── skills/
└── [project files]
```

**Strategy:** Author in `workflow/`. Deploy to framework directories. You can use symlinks, a copy script, or just maintain the framework directories directly if you only use one tool.

**What content goes where (summary):**

| Content Type | Claude Code | Copilot CLI | Codex |
|-------------|-------------|-------------|-------|
| Always-loaded rules | `CLAUDE.md` or `.claude/rules/` | `.github/copilot-instructions.md` + `AGENTS.md` | `AGENTS.md` |
| Agent personality | `CLAUDE.md` | `AGENTS.md` or `.github/agents/*.agent.md` | `AGENTS.md` |
| Skills (on demand) | `.claude/skills/*/SKILL.md` | `.github/skills/*/SKILL.md` | `.agents/skills/*/SKILL.md` |
| Prompts | Paste in chat or `/command` | Paste or `.github/prompts/*.prompt.md` | Paste or `codex exec` |
| Personal global | `~/.claude/CLAUDE.md` | `$HOME/.copilot/copilot-instructions.md` | `~/.codex/AGENTS.md` |
| Personal skills | `~/.claude/skills/` | `~/.copilot/skills/` | `~/.codex/skills/` |

**Critical note on always-loaded files:** These are injected into **every** request. Our agent files are designed to be loaded per-phase, not all at once. When merging agent content into always-loaded files (`CLAUDE.md`, `AGENTS.md`), include only the **universal rules** that apply to all phases — not phase-specific behavioral rules. Keep phase-specific agent personality in skills or paste it with the prompt.

---

### Reusing Files Across Projects

**Almost always reusable as-is:**
- `git-flow.skill.md` — unless your git conventions change
- `code-quality.skill.md` — unless your coding standards change

**Reusable with minor edits:**
- Agent files — behavioral rules are generally stable; adjust operating context
- Document format skills — section structure may vary per project type

**Always project-specific:**
- Prompt files — inputs and steps are unique per task instance
- Specialized skills — domain-specific conventions

### Keeping Context Minimal

**The 4-file rule of thumb:** For any single agent task, aim for no more than:
- 1 agent file
- 1 prompt file (with pasted upstream artifacts)
- 2 skill files

If you need more than 2 skills for a single task, consider whether some skill content should be merged or whether the task should be split.

**Signs you're overloading context:**
- Agent file > 100 lines → extract skills
- Prompt file > 120 lines → extract format templates to skills
- More than 3 skills loaded for one task → merge related skills or split the task
- Agent starts ignoring rules from early in context → context is too large, prioritize

---

## Part 6 — Scaling Patterns

### Tiny Project (1-3 files, single concept)

```
Phases:  Spec → Implement → Validate
Agents:  Analyst (spec+research combined), Builder, Validator
Skills:  code-quality, git-flow, one lightweight spec format
Prompts: 3 (one per phase)
```

Skip formal research. Write a minimal spec in the prompt itself. Combine architect + developer.

### Standard Project (5-15 files, multiple components)

```
Phases:  Research → Spec → Design → Implement → Validate
Agents:  Researcher, Spec Writer, Architect, Developer, QA Engineer
Skills:  All document formats + git-flow + code-quality
Prompts: 5 (one per phase)
```

This is the default. Use the full separation.

### Large Project (15+ files, subsystems)

```
Phases:  Research → Spec → Design → [Implement subsystem A → Implement subsystem B → ...] → Integrate → Validate
Agents:  Researcher, Spec Writer, Architect, Developer (multiple instances), Integrator, QA Engineer
Skills:  All standard + possibly domain-specific skills
Prompts: 5+ (implementation may have multiple prompts, one per subsystem)
```

Split implementation into sub-tasks, each with its own feature branch. The design phase produces a more detailed implementation plan with clear subsystem boundaries.

### Adding a Feature to an Existing Project

```
Phases:  Spec (update) → Design (update) → Implement → Validate
Agents:  Spec Writer, Architect, Developer, QA Engineer
Skills:  Same as the original project
Prompts: 4 — each includes the EXISTING spec/design as context + the change description
```

Start from the existing artifacts. The spec writer adds requirements. The architect adds components/steps. The developer implements only the new work.

### Bug Fix

```
Phases:  Validate (reproduce) → Implement (fix) → Validate (verify)
Agents:  QA Engineer, Developer, QA Engineer
Skills:  code-quality, git-flow, validation-report
Prompts: 3 — first validate to confirm the bug, then fix, then re-validate
```

Minimal pipeline. Skip research, spec, and design. Start from the failing scenario.

---

## Part 7 — Process Checklist

Use this for every project:

### Before Starting
- [ ] Defined the phases needed for this project
- [ ] Identified agent roles (one per phase, or combined for small projects)
- [ ] Identified skills needed (format skills + convention skills)
- [ ] Created the workflow directory structure
- [ ] Created the remote git repository

### Per Phase
- [ ] Assembled context: agent + skills + prompt with filled inputs
- [ ] Verified the prompt references only needed skills (no extras)
- [ ] Ran the phase
- [ ] Reviewed output against the skill's quality checklist
- [ ] Confirmed at the gate before proceeding

### For Implementation Phases
- [ ] Git repository initialized with main + develop branches
- [ ] Each task executed on a feature branch
- [ ] Each commit is atomic, runnable, and follows conventional commits
- [ ] Code reviewed (self-review) before each commit
- [ ] Each step verified with its "Definition of Done" command
- [ ] All deviations from design logged
- [ ] Feature branches merged with `--no-ff` and cleaned up
- [ ] All commits pushed to remote

### For Validation Phases
- [ ] Environment set up from scratch (clean, no inherited state)
- [ ] Every spec scenario tested automatically
- [ ] Every requirement covered in the coverage matrix
- [ ] Demo uses different data from validation
- [ ] Verdict is evidence-based with specific scenario citations
- [ ] Git finalized (main merge + tag if passing, or documented why not)

### After Completion
- [ ] All artifacts committed and pushed
- [ ] Validation report reviewed
- [ ] Verdict accepted or iteration needed
- [ ] Remote repository reflects final state

---

## Part 8 — Quick-Start Templates

### Minimal Agent Template

```markdown
# [Role Name] — Agent

## Identity
**Role**: [Name]
**Produces**: [artifact] consumed by [next phase]

## Mission
[One sentence.]

## Behavioral Rules
1. [Most important rule]
2. [Second most important]
3. [...]

## Decision Framework
1. [First priority when ambiguous]
2. [Second priority]

## Anti-Patterns
- Do not [common mistake 1]
- Do not [common mistake 2]
```

### Minimal Skill Template

```markdown
# [Skill Name] — Skill

## Purpose
[One sentence.]

## Conventions
1. [Rule 1]
2. [Rule 2]

## Output Template (if applicable)
[Skeleton/format]

## Quality Checklist
- [ ] [Check 1]
- [ ] [Check 2]
```

### Minimal Prompt Template

```markdown
# [Phase Name] — Prompt

## Skills
- `[skill].skill.md` — [why needed]

## Input
[Placeholders]

## Task
1. [Step 1]
2. [Step 2]

## Output
[What to produce — reference skill for format]
```

---

## Appendix — Decision Trees

### "Do I Need a Separate Agent for This?"

```
Is this phase a different ROLE than the previous one?
├── Yes → New agent
└── No → Same agent
    └── But do the behavioral rules CONFLICT?
        ├── Yes → New agent (even if same role name)
        └── No → Same agent, different prompt
```

### "Is This a Skill or Part of the Agent?"

```
Is this knowledge reusable by other agents or phases?
├── Yes → Skill
└── No → Is it about HOW to think (behavior)?
    ├── Yes → Agent
    └── No → Is it about WHAT to do right now?
        ├── Yes → Prompt
        └── No → Probably not needed
```

### "Is This a Skill or Part of the Prompt?"

```
Will this exact content be used again in another task?
├── Yes → Skill
└── No → Is it an output format template?
    ├── Yes → Skill (even if single-use — keeps the prompt clean)
    └── No → Prompt
```

### "Should I Create a New Skill or Extend an Existing One?"

```
Does the existing skill's "When to Use" cover this case?
├── Yes → Extend
└── No → Is there >50% overlap with the existing skill?
    ├── Yes → Extend with a new section
    └── No → New skill
```
