---
name: plan
description: "Plan mode: write an actionable markdown plan to .hermes/plans/, no execution. Supports Implementation Plans (code-level TDD) and Project Architecture Plans (system design, stack, phased delivery)."
version: 2.1.0
author: Hermes Agent (writing-craft adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow, design, documentation, architecture]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Plan Mode

Use this skill when the user wants a plan instead of execution.

## Core behavior

For this turn, you are planning only.

- Do not implement code.
- Do not edit project files except the plan markdown file.
- Do not run mutating terminal commands, commit, push, or perform external actions.
- You may inspect the repo or other context with read-only commands/tools when needed.
- Your deliverable is a markdown plan saved under `.hermes/plans/` (for code-level implementation plans) or wherever the user specifies (for project architecture plans — the user may want it in a specific project folder).

## Save location

Save the plan with `write_file` under:
- `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`

Treat that as relative to the active working directory / backend workspace. Hermes file tools are backend-aware, so using this relative path keeps the plan with the workspace on local, docker, ssh, modal, and daytona backends.

If the runtime provides a specific target path, use that exact path.
If not, create a sensible timestamped filename yourself under `.hermes/plans/`.

For **Project Architecture Plans**, the user may explicitly request a different path (e.g., inside a project's docs/ or a note-taking folder). Honour that.

## Interaction style

- If the request is clear enough, write the plan directly.
- If no explicit instruction accompanies `/plan`, infer the task from the current conversation context.
- If it is genuinely underspecified, ask a brief clarifying question instead of guessing.
- After saving the plan, reply briefly with what you planned and the saved path.

---

## Choosing the Right Plan Type

| If the user asks for… | Use… |
|---|---|
| "how to implement X", "steps to build Y", code-level breakdown | **Implementation Plan** (code-focused, TDD, bite-sized tasks) |
| "what to build", system design, architecture, stack recommendations, phased rollout | **Project Architecture Plan** (design-focused, component breakdown, options) |

---

# Type A: Implementation Plan

The rest of this section describes the craft of authoring a *good* implementation plan — the content that goes inside the markdown file when the user wants code-level, actionable steps.

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When a Full Implementation Plan Helps

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Merged Skills

> This skill now absorbs `writing-plans` (archived). The Implementation Plan
> content below was originally duplicated in both skills. This single skill
> is the canonical source. See `references/writing-plans-original.md` for the
> legacy content (identical to what's inline below).

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**

---

# Type B: Project Architecture Plan

Use this when the user asks for system design, architecture, "what to build", stack recommendations, or a phased rollout strategy — not code-level steps.

## Overview

A Project Architecture Plan answers the question **"what should I build?"** rather than **"how do I implement it?"**. It's a strategic design document that the user (or a future implementation plan) uses as a blueprint.

**Core principle:** A good architecture plan makes design decisions obvious. It gives the reader confidence to proceed.

## When to Use

- User asks "how should I build X?" without wanting code yet
- User wants to evaluate options before committing to a stack
- User needs a phased delivery roadmap
- User wants to understand architecture tradeoffs
- User describes a problem and wants a system design

## Document Structure

A good Project Architecture Plan includes these sections (adapt to context):

### 1. Concept Overview

A brief summary of what the system does. One-liner + 2-3 sentence description.

```
## Concept Overview

A [type of system] that solves [problem]. 
Components: [list of major parts].
```

### 2. Architecture Diagram

Use ASCII diagrams for the data flow. Show components as boxes, arrows as data flow.

```
┌──────────┐     ┌──────────┐
│  Client  │────►│  API     │
└──────────┘     └────┬─────┘
                      │
               ┌──────▼──────┐
               │  Storage    │
               └─────────────┘
```

Label each component and the protocol/format between them.

### 3. Component Breakdown

For each major component, describe:
- **What it does** (one sentence)
- **Key files/modules** (file paths if known)
- **How it connects** to other components

Use a table for endpoints or routes when applicable.

| Component | Responsibility | Tech |
|---|---|---|
| API | CRUD over storage, search | Hono |
| Frontend | UI rendering, editing | React + Vite |

### 4. Data Model / File Structure

Show the on-disk or in-DB layout. For file-based systems, show a tree.

```
project/
├── foo/
│   └── bar.txt
└── baz.md
```

For databases, include schema SQL or table definitions.

### 5. Stack Recommendations

Use a table with tool, version/option, and rationale.

| Tool | Choice | Why |
|---|---|---|
| Runtime | Node.js 20 LTS | Already installed |
| API | Hono | Fast, typed, lightweight |

Explain *why* each choice — "already installed", "best DX for this use case", "only option with X feature".

### 6. Phased Delivery Plan

Break the project into phases ordered by dependency:

```
🟢 Phase 1: MVP — [core functionality]
- [ ] Task A
- [ ] Task B

🟡 Phase 2: [next capability]
- [ ] Task C

🔵 Phase 3: [polish / extras]
- [ ] Task D
```

Each phase should be independently usable (vertical slice where possible).

### 7. Risks & Mitigations

Use a table:

| Risk | Mitigation |
|---|---|
| Concurrency: two writers conflict | Atomic writes (temp + rename) |
| Search gets slow at scale | Add SQLite FTS5 index |

### 8. Bonus Ideas (Post-MVP)

A bullet list of enhancements for later. This gives the user a roadmap beyond the plan.

### 9. Links & Resources

URLs to docs, libraries, and inspiration.

## Writing Style

- **Be opinionated.** Recommend one stack, don't list 5 options unless the user asked for comparison. "Use Hono" > "You could use Express, Hono, Fastify, or Koa".
- **Explain why.** Every recommendation needs a one-sentence rationale.
- **No code.** Project Architecture Plans contain no implementation code. SQL schemas are fine. Config files are fine. But no `def function():`.
- **Use tables** for comparisons, routes, and stacks.
- **Use ASCII diagrams** for architecture — they force clarity about data flow.
- **Save where the user says.** If they want it in a notes folder or project docs, honour that.

## Remember

```
Opinionated choices with rationale
ASCII architecture diagrams
Component breakdown tables
Phased delivery (vertical slices)
Risks table
No implementation code
```

**A good architecture plan makes design decisions obvious.**
