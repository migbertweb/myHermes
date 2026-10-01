---
name: design-impeccable
description: >
  Use when the user wants to design, redesign, shape, critique, audit, polish,
  refine, harden, onboard, optimize, adapt, animate, colorize, distill, clarify,
  typeset, layout, bolder, quieter, delight, overdrive, or otherwise improve a
  frontend interface for a brand or product surface.
  Covers websites, landing pages, dashboards, product UI, app shells, components,
  settings, empty states, onboarding, responsive behavior, and especially
  Anti-Pattern detection / anti-slop cleanup inspired by `impeccable`.
  Not for backend-only or non-UI tasks.
version: 1.2.0
---

# Design Impeccable

Frontend design skill focused on production-ready UI, anti-pattern detection,
and consistent project-wide design context.

Workflow priority:
1. Init flow: gather product/design context, write `PRODUCT.md` and `DESIGN.md`.
2. Command flow: `/impeccable <command> [target]`.
3. Deterministic verification: detector scan on changed UI files/paths.
Implied route hints to prefer:
- “redo/fix this ...”
- “make/polish ...”
- “design/create/build a ...”

## Setup flow

- ALWAYS read `reference/register.md` to choose brand vs product register.
- ALWAYS read at least one existing project file: `src/styles.css`, `tailwind.config.*`,
  `src/app/globals.css`, `src/theme/*`, `DESIGN.md`, etc.
- When missing design system / brand colors, run:
  `node ~/.hermes/skills/software-development/design-impeccable/scripts/palette.mjs`
  and use its seed to compose palette in OKLCH.
- Treat `PRODUCT.md` and `DESIGN.md` as authoritative context when present.

## Commands

| command | behavior |
|---------|----------|
| `init` | Gather product/design context; write `PRODUCT.md` and `DESIGN.md` when allowed |
| `craft` | Shape then build with live browser iteration |
| `shape` | Plan UX/UI before writing code |
| `critique` | UX design review: hierarchy, clarity, emotional resonance |
| `audit` | Technical quality: a11y, perf, responsive, contrast — see `references/audit.md` for full workflow |
| `polish` | Final pass, design system alignment, shipping readiness |
| `distill` | Strip to essence |
| `bolder / quieter` | Increase or decrease visual intensity |
| `harden` | Errors, i18n, overflow, edge cases |
| `onboard` | First-run flows, empty states, activation paths |
| `animate` | Purposeful motion respecting reduced motion |
| `colorize` | Strategic color work |
| `typeset` | Font choices, hierarchy, sizing |
| `layout` | Layout, spacing, visual rhythm |
| `delight` | Moments of joy |
| `overdrive` | Technically extraordinary effects |
| `clarify` | UX copy clarity |
| `adapt` | Responsive / device adaptations |
| `optimize` | Performance improvements |
| `live` | Visual variant mode: iterate in browser |
| `detect` | Run deterministic anti-pattern detection on paths |
| `pin` | Create standalone shortcuts like `/audit` from common commands |
| `hooks` | Toggle/review post-edit detector hook: status, reset, ignore-rule, ignore-file, ignore-value |

Routing:
- `reference/register.md` sets brand vs product register per task.
- Load `reference/<command>.md` when the user invokes `/impeccable <command> [target]`.
- If intent clearly maps to one command but wording differs, route as that command.
- If ambiguous, ask once between likely candidates.
- If no command matches, apply general rules + register reference.
- Pin/unpin: `node ~/.hermes/skills/software-development/design-impeccable/scripts/pin.mjs pin|unpin <command>`.
- Recommended entry points: `init`, `craft`, `shape`, `audit`, `polish`, `detect`.
- Real case study: `references/workapp-agent-audit.md` — 14 componentes, 2 críticos + 4 medios, 6 PRs a 0 anti-patrones.

## Anti-Patterns (core)

Do not produce:
- Overused fonts as defaults: Arial, Inter, system-ui without brand reason
- Gray body text on colored backgrounds
- Pure black/white used as primary ink or surface
- Card soup: cards inside cards
- Bounce/elastic easing
- Display heading letter-spacing < -0.04em

## Deterministic detector

Use `npx` based detection when available:
- `npx impeccable detect <paths>`
- `npx impeccable detects --json .` for machine-readable output

## PDF generation with jsPDF (lessons from workapp-agent)

- **Import**: `import autoTable from 'jspdf-autotable'` (named), NOT `import 'jspdf-autotable'` (side-effect — Vite tree-shakes it)
- **Colors**: Always hex strings `'#333333'` — arrays `[51,51,51]` break `encodeColorString` in jsPDF 4.x
- **Tables**: Remove `columnStyles`, use `margin: { left, right }` for alignment. Let autoTable auto-size columns.
- **Totals**: Use `foot` rows in autoTable, never separate `doc.text()` below the table
- **Logo**: Load async via `new Image()` → canvas → `toDataURL()` → `doc.addImage()`. Cache in closure (`_logoDataUrl`)
- **Fonts**: Load via `<link>` in `index.html`, never `@import` in CSS (PostCSS ordering error)
- **Compact mode**: `cellPadding: 3`, `fontSize: 7`, section gaps ≤5mm for single-page budget PDFs
- **Spacing**: client section title→content gap ≥5mm, value rows ≥5mm, inter-table gap ≥6mm

## Automation hooks

Optional project-local hook after UI edits:
- See `reference/hooks.md`
- Hook invokes detector and surfaces findings as reminders.
- Uses `gate`/`unlock` for approval state; `status` reports activity.
- Settings: reload manifest hook after install/update.

## General rules

- Verify contrast: body >= 4.5:1; large text >= 3:1.
- Cap body line length at 65–75 ch.
- Hero/display heading clamp max <= 6rem.
- Use semantic z-index scale.
- Every animation needs `@media (prefers-reduced-motion: reduce)` path.

## Post-audit fix workflow

After an `audit` run produces findings, apply fixes following the priority order below. Load `references/audit.md` for the full step-by-step audit procedure.

### Priority order
1. **Críticos primero**: accesibilidad (`prefers-reduced-motion`), performance (`transition: width → transform`), touch targets insuficientes
2. **Medios después**: overused fonts, contraste marginal, gradientes AI-slop
3. **Bajos al final**: mejoras cosméticas sin impacto funcional

### PR discipline
- One fix per branch, one fix per PR — never batch multiple findings
- Commit convention: `fix:` prefix, squash merge into main
- Run `npm run build` before every commit
- Re-run `npx -y impeccable detect <path>` after each merge to confirm improvement
- Report only merged results, never aspirational
