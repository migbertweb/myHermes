---
name: freelance-profile-builder
description: specialized workflow for creating high-conversion freelancer profiles and CVs on platforms like Upwork. Focuses on moving from 'commodity' (generic full-stack) to 'premium' (outcome-led specialist).
---

# Freelance Profile Builder

This skill governs the transition of a developer from a generalist hire to a premium specialist. The goal is to stop bidding wars and start attracting high-value clients by shifting the focus from "what I know" (stack) to "what I solve" (outcomes).

## The Transition Framework

### 1. Commodity vs. Premium Positioning
- **Commodity:** "Full Stack Developer (React, Node, Python)". Result: Bidding wars, low rates, generic clients.
- **Premium:** "Full Stack Developer — Automation & Real-time Dashboards for Startups". Result: Value-based pricing, lower competition, high-trust clients.

### 2. CV & Profile De-noising
- **Remove Noise:** Strip non-technical experience that doesn't support the technical narrative (e.g., industrial labor in a dev CV) unless it demonstrates a specific soft skill (adaptability, pressure).
- **Add Signal:** Replace "Responsible for X" with "Achieved Y by doing X". Use metrics (e.g., "improved reliability by 40%", "reduced downtime to zero").
- **Portfolio as Proof:** Don't just list projects; describe them as case studies: Problem $\rightarrow$ Solution $\rightarrow$ Tech Stack $\rightarrow$ Measurable Result.

## Workflow: Profile Generation

### Step 1: Technical Audit
Analyze the current CV and project history to find the "Sweet Spot" — the intersection of high technical competence and high market demand.

### Step 2: Niche Selection
Apply the 4-question gate:
1. **Tech specialty:** Narrow slice (e.g., "FastAPI + React" instead of "Python").
2. **Vertical specialty:** (e.g., "SaaS for Fintech" instead of "Web Apps").
3. **Outcome specialty:** (e.g., "Zero-downtime migrations" instead of "DevOps").
4. **Decision-maker fit:** Target the specific buyer (CEO, CTO, Product Manager).

### Step 3: Content Drafting (The 'Hook' Method)
- **Title:** Keyword-rich but outcome-focused.
- **Bio:** 
    - Paragraph 1: The Hook (What problem do I solve?).
    - Paragraph 2: Social Proof (Concrete projects + results).
    - Paragraph 3: The Process (How I work, communication, tools).
    - Paragraph 4: The Call to Action (Low-friction next step).

### Step 4: Portfolio Structuring
For each project, define:
- **The Goal:** What was the client trying to achieve?
- **The Stack:** Specific tools used.
- **The Win:** The specific technical or business victory.

## Live Profile Audit — Extract & Evaluate an Existing Profile

Use this when the user already has a live Upwork profile and wants it reviewed against a strategy checklist.

### Extraction (Cloudflare bypass)

Upwork profile pages are behind Cloudflare Turnstile — `browser_navigate` often returns a "Just a moment…" challenge, while `web_extract` (plain HTTP extraction) reliably returns the profile content. Verified working across multiple sessions.

**Verified strategy:**
1. **Start with `web_extract`** on the public profile URL (`/freelancers/~<id>/?mp_source=share`). It returns title, rate, bio text, skills list, portfolio entries (count + titles), and the completeness percentage — enough for a full audit.
2. Add `?mp_source=share` to the URL — it helps the cache layer return the full profile page.
3. If `web_extract` fails (returns Cloudflare challenge text), try once more with `char_limit=80000`. If still blocked, rely on the user's Obsidian vault strategy notes or request a manual copy-paste of the specific section.
4. **Do NOT use `browser_navigate` for Upwork profile extraction** — it always hits the Turnstile challenge without premium proxies.
5. **All profile edits require manual paste by the user** — the agent cannot log in, edit, or save changes to Upwork. Deliver all content as ready-to-copy text blocks with character limits honored.

### SPA Login Screenshot Capture

When the user's own SPA project (e.g. a custom-built dashboard for portfolio) is behind Cloudflare and needs login to capture screenshots, form-filling in the browser may fail because Cloudflare intercepts relative-URL fetch calls from the SPA's JavaScript.

**Workaround:** `references/cloudflare-spa-login.md` — curl API login to get JWT token → base64 encode → inject into browser localStorage via `atob()` in console.

**Workflow:**
```python
from hermes_tools import web_extract
result = web_extract(urls=["https://www.upwork.com/freelancers/~<id>?mp_source=share"])
# Returns: title, rate, bio text, skills list, completeness %
```

### Audit Checklist

Cross-reference the live profile against these dimensions:

| Component | What to check |
|-----------|---------------|
| **Title** | Follows `[Rol] \| [Tecnologías clave] \| [Valor diferencial]`? Includes niche (IoT, ESP32, automation)? No generic "Data manager" or "Developer" alone? **Length:** Upwork truncates at ~70 characters — verify the full title is visible. If it cuts off, reorder most important keyword first (role > tech > niche) so the visible part carries the signal. |
| **Bio** | 4-paragraph structure: hook → measurable results → process/tools → CTA? In English for global reach? Has specific metrics (%, response time, data volume)? |
| **Skills** | At least 10-15. Covers core stack (React, Node, Python) + niche (IoT, ESP32, CI/CD, Docker) + management? Missing critical keywords? |
| **Rate** | Matches positioning? Below $25/hr for specialist signals commodity. Cross-check against rate-positioning matrix. |
| **Portfolio** | 3-5 projects visible each with problem → solution → stack → measurable result? Links to GitHub/demos? |
| **Testimonials** | Any visible? Social proof is the highest-conversion element. |
| **Completeness** | % shown on profile. < 50% means critical sections missing. Aim for 100% (verified identity, photo, portfolio, skills). |

### Diagnosis structure

Present findings in this order:
1. **Completeness score** — flag if < 50%
2. **Title verdict** — pass/fail + specific replacement
3. **Bio verdict** — language, structure, missing elements
4. **Skills gap** — what's listed vs what's missing (especially niche keywords)
5. **Rate alert** — benchmark vs positioning
6. **Portfolio holes** — what's missing
7. **Priority actions** — top 3 in order

### Progress tracking over time

When revisiting a profile that was previously audited, use a **before/after comparison table** to show what changed:

```
| Element | Antes | Ahora | 
|---------|-------|-------|
| Title   | ❌ Generic | ✅ Optimized |
| Rate    | $11/hr ❌ | $18/hr ⚠️ (still low) |
| Skills  | 10 (wrong) | ✅ 17 (aligned) |
```

This format lets the user see progress at a glance and highlights what still needs work. Always include a priority-action table at the end with impact-level indicators (🔴 🟡 🟢).

When the completeness % hasn't changed between audits but visible improvements were made (title, bio, skills, portfolio), note that some profile sections (photo, verification, education) require user-side action and may not be reflected in the scrape. Recommend specific fields by name.

**Important:** All profile edits require manual paste by the user. Deliver every title, bio, skills list, and portfolio entry as **ready-to-copy text** with Upwork's character limits pre-checked (see `references/upwork-section-content.md` for exact limits).

## Rate-Positioning Matrix

When evaluating a profile, cross-check rate against positioning:

| Profile Type | Typical Rate | Warning Signal |
|---|---|---|
| Generalist (no niche) | $15-30/hr | OK for entry, but no leverage |
| Stack specialist | $30-60/hr | Below $25 = undervaluing |
| Stack + vertical | $50-100/hr | Below $40 = leaving money on table |
| Stack + vertical + outcome | $80-150/hr | Below $60 = pricing as commodity |
| Niche + IoT/DevOps/automation | $35-70/hr (LATAM) | Below $25 = race to bottom |

For Full Stack + IoT + ESP32 + DevOps positioning, $11/hr is a red flag — the user is pricing as a commodity generalist despite having specialist skills.

## Pitfalls & Lessons
- **The 'Available for Hire' Trap:** Never use passive phrases like "Open to opportunities". Use active, value-driven language.
- **The Stack-Dump:** Avoid listing 20+ technologies in the bio. It looks desperate/generic. Group them into "Core Stack" and "Specialized Tools".
- **Language Barrier:** For global platforms, always prioritize English profiles, even for LATAM targets, as it signals a higher tier of professional capability.
- **Rate too low:** Below $25/hr signals commodity. For specialist profiles (Full Stack + IoT + DevOps), anything under $25/hr undermines the positioning regardless of location.
- **Bio in Portuguese:** Limits reach to Brazil-only. If targeting US/EU, English bio triples addressable market.
- **Missing niche keywords:** IoT, ESP32, automation, CI/CD are differentiators absent from most dev profiles — omitting them wastes the advantage.
- **Portfolio without metrics:** "Built an app" is noise. "Built a dashboard processing 50K records/day, reducing response time 40%" is signal.
- **Checklist not in memory:** If the user has a strategy note in Obsidian vault, load it with the obsidian skill and cross-reference — the user's own playbook may have specific title formulas and bio structure preferences.
- **Verify character counts with `wc -c`:** Eyeballing char counts for portfolio fields (70/100/600) miscounts multi-byte characters (—, á, é, ç, etc.) and wastes user time when they paste and it gets rejected. Always run `echo -n "<text>" | wc -c` in terminal before delivering portfolio content.

## Section Content Generation

After identifying gaps via the audit, generate copy-paste ready content for each Upwork section. See `references/upwork-section-content.md` for:

- **Skills** — priority-ordered additions with rationale and removal candidates
- **Portfolio** — Upwork field schema (Title, Your Role, Description, Skills, Deliverables, Images/Video) + reusable project templates with real examples
- **Employment History** — job entry format with examples outside Upwork
- **Bio** — single-paragraph ready-to-paste versions (English + Spanish)

### Portfolio Visual Assets

Portfolio entries with images convert significantly better. See `references/portfolio-visuals.md` for generating professional visuals:

- **Infographics** via `baoyu-infographic` skill (requires `image_gen` toolset + FAL_KEY)
- **Architecture diagrams** via `architecture-diagram` skill (HTML/SVG, no API key needed)
- **Live screenshots** of running apps and dashboards
- **Per-project strategy** matching visual type to project category (web app, IoT, DevOps, API)

## Deliverables
- Optimized Upwork Profile (Title, Bio, Skills).
- Live Profile Audit Report (completeness, gaps, priority actions).
- Dev-focused CV (Cleaned of noise, outcome-driven).
- Portfolio Case Studies (problem → solution → stack → result).
