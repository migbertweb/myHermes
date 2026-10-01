---
name: multi-agent-kanban-orchestration
description: Use when designing specialized sub-agent teams for Kanban.
---

# Multi-Agent Orchestration (Kanban Team)

Use when designing, configuring, or deploying specialized sub-agent teams (Manager, Devs, QA, Researchers) for long-term project work (Kanban/Sprint).

## Core Architecture
- **The Manager:** Orchestrates, assigns tickets, and makes final "go/no-go" decisions.
- **The Devs (Frontend/Backend):** Implement features based on tickets.
- **The Researcher:** Validates feasibility and chooses tools.
- **The QA:** Independent validator. **Hard Rule: No agent verifies their own work.**

## QA Agent Integration (The "Fresh Eyes" Pattern)
To avoid confirmation bias, the QA agent must be a distinct entity from the developers and researchers.

### QA Identity & Setup
- **Persona:** "The Hostile User". Cold, evidence-driven, and focused on breaking the app.
- **Identity File:** Use a `soul.md` (with `MEMORY_FIELDS`) to ensure consistent personality and boundaries across sessions.
- **Verification Toolset:** Must include `browser`, `vision`, and `terminal`.

### QA Workflow
1. **Systematic Dogfooding:** Use the `dogfood` skill for exploratory QA, checking browser consoles for JS errors after every interaction.
2. **Adversarial Testing:** Use the `adversarial-ux-test` skill to simulate hostile personas.
3. **The Filter:** Apply the pragmatisme filter (RED/YELLOW/WHITE/GREEN) to separate noise from real defects.
4. **The Verdict:** Output must be a structured report (template `verdict.md`) containing:
   - Verdict (PASS/FAIL/PASS WITH RESERVATIONS).
   - Evidence table: URL, Severity, Category, and Screenshot (MEDIA:).
   - Repro steps + Expected vs Actual.

## Pitfalls
- **Confirmation Bias:** Never let a Dev or Researcher perform the final QA.
- **Vague Reports:** Avoid "it feels slow" or "looks weird". Every report requires a screenshot and a console log.
- **Auto-Approval:** The QA agent votes; only the Manager decides to move the ticket to `done`.

## Templates & References
- `templates/verdict.md`: Standardized QA report format.
- `agent/soul.md`: Example of a high-fidelity agent identity file.
