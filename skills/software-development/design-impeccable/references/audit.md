# Audit

Technical quality scan: deterministic detector + manual product-register review.

## Flow

1. Run the deterministic detector first:
   ```bash
   npx impeccable detect <paths> --json 2>&1
   ```
   This catches 46 rule-based issues (overused-font, layout-transition, contrast problems, etc.) with zero LLM cost.

2. Read at least one representative component file and the main CSS/theme file.

3. Classify findings by severity:
   - 🔴 **Critical**: a11y violations, layout thrash, missing `prefers-reduced-motion` — **PR inmediato, merge ya**
   - 🟡 **Medium**: overused fonts, marginal contrast, small touch targets, purple gradients — **PR separado después de críticos**
   - 🟢 **Good/Low**: correct patterns, empty states, low-priority aesthetic suggestions

4. Score against the product register checklist:
   - Body text contrast ≥ 4.5:1 on background
   - Large text (≥18px or bold ≥14px) ≥ 3:1
   - Touch targets ≥ 44px
   - No arbitrary z-index (999/9999)
   - `prefers-reduced-motion` on every animation/transition
   - Semantic z-index scale: dropdown < sticky < modal-backdrop < modal < toast < tooltip

5. Check product-specific anti-patterns:
   - Decorative motion breaking focus
   - Low-contrast muted text on tinted surfaces
   - Cards nested inside cards
   - Pure black/pure gray in high-density text areas
   - Bounce/elastic easing

## Professional PR workflow for fixes

**User preference: one fix = one commit = one PR.** Never batch multiple findings into a single PR, even if they're all the same severity level. Each fix gets its own branch.

1. **For each finding** (critical first, then medium, one at a time):
   - `git checkout main && git checkout -b fix/<descriptive-slug>`
   - Apply the fix
   - `npm run build` to verify
   - `git add` + `git commit -m "fix: <description>"`
   - `git push -u origin <branch>`
   - `gh pr create --title "fix: <description>" --body "<one-liner reason>" --base main`
   - `gh pr merge <number> --squash --delete-branch`
   - `git checkout main && git pull origin main`
2. Re-run detector after each merge: `npx -y impeccable detect <paths>` — count should decrease
3. Verify merge chain: `git log --oneline -5` — confirm the PR commit is present on main
4. Report only what is actually merged; never present aspirational results

**Commit convention:** `fix:` prefix, lowercase, concise. Match the PR title.

## Common anti-patterns in AI-generated code — with CSS Fix Recipes

### layout-transition (transition:width)
```css
/* BEFORE — detector: layout-transition, causes real layout thrash */
.progress-fill { transition: width 0.3s; }
/* JSX: style={{ width: `${pct}%` }} */

/* AFTER — GPU-only transform */
.progress-fill {
  transform-origin: left;
  transform: scaleX(var(--pct, 0));
  transition: transform 0.3s;
}
/* JSX: style={{ '--pct': pct / 100 }} */
```

### prefers-reduced-motion (missing globally)
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### transition:all (expensive, triggers layout recalc)
```css
/* BEFORE — browser must check all properties on every frame */
.btn { transition: all 0.15s; }
.sidebar-link { transition: all 0.15s; }

/* AFTER — specify only changing properties */
.btn { transition: background-color 0.15s, color 0.15s; }
```

### translateY on hover (causes layout shift)
```css
/* BEFORE — triggers reflow on hover */
.project-card:hover { transform: translateY(-2px); }

/* AFTER — use border-color or box-shadow instead */
.project-card:hover { border-color: var(--accent); }
```

### overused-font (Inter as only typeface)
```css
/* BEFORE */
body { font-family: 'Inter', system-ui, -apple-system, sans-serif; }

/* AFTER — distinctive geometric with personality */
/* Font loaded via <link> in index.html (NOT @import — breaks PostCSS/Tailwind) */
body { font-family: 'Outfit', system-ui, -apple-system, sans-serif; }
```
```html
<!-- index.html -->
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

### marginal badge contrast (e.g. #94a3b8 on #1e293b ≈ 4.25:1)
```css
/* BEFORE */
.badge-draft { background: #1e293b; color: #94a3b8; }
.badge-todo   { background: #1e293b; color: #94a3b8; }

/* AFTER — bump text luminance ~2 stops on the gray ramp */
.badge-draft { background: #1e293b; color: #cbd5e1; }
.badge-todo   { background: #1e293b; color: #cbd5e1; }
```

### purple gradient logo (classic AI slop)
```css
/* BEFORE — cross-hue gradient flagged by detector */
background: linear-gradient(135deg, #6366f1, #a855f7);

/* AFTER — monochromatic hue gradient */
background: linear-gradient(135deg, #818cf8, #6366f1);
```

### touch targets below 44px
```css
/* BEFORE */
.btn-sm { padding: 4px 10px; font-size: 12px; }

/* AFTER — meets WCAG 2.5.5 minimum */
.btn-sm { padding: 8px 14px; font-size: 12px; min-height: 44px; }
```

## What NOT to flag

- Inter/system-ui in a product dashboard body is acceptable (brand register is where it hurts)
- Dark theme near-black backgrounds (not pure black) are fine for dashboards
- One-off gradient logos in product UI (only flag when it's the full hero)
