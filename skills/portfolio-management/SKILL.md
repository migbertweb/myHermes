---
name: portfolio-management
description: "Manage migbertweb.xyz portfolio site: content updates, design decisions, PDF CV generation, and deploy workflow via PRs"
---

# Portfolio Management — migbertweb.xyz

## Stack

- **Framework:** React 19 + TypeScript + Vite
- **Styling:** Tailwind CSS v4 (custom `@theme` with neon-blue/neon-purple)
- **Animations:** Framer Motion (scroll reveals, stagger, `whileInView`)
- **i18n:** i18next (pt, es, en — 3 locale files)
- **Font:** Outfit (Google Fonts, loaded via `<link>` in index.html)
- **Deploy:** Dokploy (auto-deploy on push to `master`)

## Repo

- Path: `/home/migbert/proyectos/frontend/portfolio-react`
- Remote: `git@github.com:migbertweb/portafolio.git` (branch `master`)
- Auto-deploy via Dokploy on push to `master`

## Project Structure

```
src/
├── App.tsx               # Main layout: Navbar, Hero, StatsBar, FeaturedProjects, Experience, YouTube, GitHub, Skills, Contact
├── components/
│   ├── Section.tsx       # Reusable section wrapper with scroll animation
│   ├── Navbar.tsx        # Sticky nav with section scroll + language/theme toggles
│   ├── ProfileImage.tsx  # Hero profile photo with glow
│   ├── FeaturedProjects.tsx  # 3 project cards (WorkApp, DeskMate, DevOps)
│   ├── StatsBar.tsx      # Metrics (5+ anos, 10+ projetos, etc.)
│   ├── GitHubRepos.tsx   # Featured repo links
│   ├── YoutubeCarousel.tsx  # Video carousel with channel link
│   ├── CursorFollower.tsx   # Custom cursor dot + ring
│   └── MouseGlow.tsx     # Ambient gradient following mouse
├── i18n/locales/         # pt.ts, es.ts, en.ts — all texts
├── assets/               # CV PDFs (Curriculum-{pt,es,en}.pdf)
└── styles/               # (not used — Tailwind in index.css)
```

## Workflow for Changes

### Standard PR workflow (applies to all portfolio changes)

1. **Create issue** on GitHub (`gh issue create`) describing the change
2. **Branch** from master: `git checkout -b feat/<slug>` or `fix/<slug>`
3. **Make changes**, verify with `npm run build`
4. **Commit** with conventional commit message referencing the issue
5. **Push** + create PR: `gh pr create --body "Closes #N"`
6. **Merge** squash: `gh pr merge N --squash --delete-branch`
7. **Dokploy** auto-deploys to https://migbertweb.xyz
8. **Verify** on live site — run the full live-site QA procedure (below)

### Multi-PR sequential delivery

When several PRs target master simultaneously (e.g. phased features):

```
1. gh pr merge 1 --squash --delete-branch
2. git checkout main && git pull origin main
3. git checkout feat/phase-2 && git rebase main
   (resolve conflicts if any)
   git push --force-with-lease origin feat/phase-2
4. gh pr merge 2 --squash --delete-branch
5. Repeat for each subsequent PR
```

Use `git -c core.editor=true rebase --continue` if rebase prompts for editor.

### Live-site QA procedure

After every deploy — or on request — run a full audit cycle:

1. **Console check** — navigate to `migbertweb.xyz`, open console. Must be 0 JS errors (warnings OK). Use `browser_console()`.

2. **Theme toggle** — click theme button (ref `e8`). Verify it cycles (system → light → dark). Check console after each click.

3. **Language switching** — click current locale button, then each locale option (PT, ES, EN). For each locale, verify:
   - Nav labels change (Sobre→Sobre mí→About)
   - Hero title/subtitle/bio translate
   - StatsBar labels ALL translate (common misses: "Experiência"→"Experiencia"→"Experience", "Projetos"→"Proyectos"→"Projects", "Tecnologias"→"Tecnologías"→"Technologies")
   - Experience section: job titles translate (known misses: "Auxiliar de Produção I", "Esmerilhador")
   - Section titles translate
   - Skills section category headings translate (Frontend/Backend/DevOps/"Banco de Dados"→"Base de Datos"→"Database")
   - Contact section labels translate
   - CV download link label changes
   - GitHub repo descriptions are NOT localized (they come from GitHub API — expected)

4. **Link validation** — extract all `<a href>` from the page. Verify:
   - Social links (GitHub, LinkedIn, WhatsApp, Email) point to correct URLs
   - Upwork URL is NOT `~your_upwork_id` — should be `~01d443f2b06423fe93`
   - CV PDFs exist per locale (Curriculum-{pt,es,en}.pdf)
   - "Agendar Conversa/Conversación/Meeting" mailto has correct subject
   - YouTube channel link targets `@MigbertonLinux`
   - GitHub repo links point to `github.com/migbertweb/*`
   - Project cards (WorkApp, DeskMate, DevOps) MUST be clickable links — each card should wrap an `<a href>` or the "Ver Projeto / Ver Proyecto / View Project" label must be inside a link. If they're StaticText only, wrap each card in `<a href={project.url}>` in FeaturedProjects.tsx.
   - Project card URLs: WorkApp→workapp.migbertweb.xyz, DeskMate→github.com/migbertweb/deskmate-dashboard, DevOps→github.com/migbertweb

5. **OG / SEO meta** — verify per locale:
   - `<meta name="description">` translates dynamically
   - `<meta property="og:description">` same
   - `<meta property="og:image">` points to existing image
   - `<meta property="og:title">` reflects current locale

6. **Image loading** — `document.querySelectorAll('img')` — every image should have `complete=true` and `naturalWidth > 0`. Check alt text presence.

7. **Visual sanity** — `browser_vision()` for full-page screenshot. Look for: layout breaks, overlapping text, missing sections, broken styling.
   - **Caveat**: `browser_vision()` with `annotate=true` draws numbered red bounding boxes over every interactive element. The vision model often misinterprets these as "debug overlays" or "broken red boxes" — they are NOT page issues, they're annotation artifacts from the tool. Check the accessibility snapshot (`browser_snapshot`) for actual content presence instead of relying solely on vision.
   - If vision says "most content is missing/broken" but the snapshot shows all text content, trust the snapshot — the content IS rendering. This is a known false positive with headless browser screenshots + annotations.

8. **Known identity decisions** (not errors, skip in QA):
   - Gradient text on headings (`bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text`)
   - Neon/cyberpunk theme
   - Cursor follower + mouse glow effects
   - StatsBar metric labels intentionally mixed-case

### Advanced QA: Adversarial UX test (optional, deeper-dive)

After the standard QA passes, optionally run the **adversarial-ux-test** skill for a complementary perspective. This finds *friction* — UX pain points a checklist won't catch:

1. **Define a persona**: the HARDEST user for this portfolio (e.g. Don Carlos — 59yo Venezuelan ferretería owner, WhatsApp-only, burned by 3 freelancers who ghosted him)
2. **Browse as the persona**: navigate the portfolio trying to accomplish their ONE goal (hire a dev). Note confusion, jargon, trust signals, and friction.
3. **The rant**: write feedback in the persona's voice — raw and unfiltered
4. **Pragmatism filter**: classify each complaint as:
   - 🔴 **RED** (real UX bug — any user would hit this)
   - 🟡 **YELLOW** (valid but low priority)
   - ⚪ **WHITE** (persona noise — "I hate computers")
   - 🟢 **GREEN** (feature request hidden in the complaint)
5. **Ticket only RED and GREEN** items — max 10 per session

The adversarial test catches what the checklist misses: confusing terminology, too-many-choices paralysis, trust signals that backfire, and cold-start confusion. Install with `hermes skills install official/dogfood/adversarial-ux-test`.

### Post-deploy checklist

After merging a PR and Dokploy auto-deploys:
1. Wait 30s for Dokploy build + deploy
2. Check Dokploy logs for build failures (puppeteer is a known culprit — see Deploy Troubleshooting)
3. Run full live-site QA (above)
4. If issues found: file a GitHub issue and fix in a follow-up PR
5. If Upwork/contact links changed: verify externally (the URLs are the revenue surface)
6. Commit any build fixes directly to master and let Dokploy auto-redeploy

## Deploy Troubleshooting

### Puppeteer / npm ci postinstall failure

**Symptom**: Dokploy build fails at `npm ci` with:
```
ERROR: Failed to set up chrome v150.0.7871.24!
Set "PUPPETEER_SKIP_DOWNLOAD" env variable to skip download.
```

**Root cause**: `puppeteer` is in `dependencies` (or `devDependencies`). Dokploy uses nixpacks which runs `npm ci`, which installs all packages including devDeps. Puppeteer's postinstall script tries to download Chrome, but the build container has no unzip.

**Fix**: Remove puppeteer entirely if not used in the codebase:
1. Delete from both `dependencies` and `devDependencies` in `package.json`
2. Delete `node_modules/` and `package-lock.json`, re-run `npm install --include=dev`
3. Remove any `allowScripts` entry for puppeteer
4. Commit directly to master: `git commit -m "chore: remove puppeteer entirely"`
5. Push — Dokploy auto-redeploys

**Prevention**: Before adding a package to dependencies, check if it has a postinstall script that downloads binaries. If it's not used in the bundle (e.g. puppeteer is only for dev tooling), don't add it at all.

### npm 12 local dev

**npm 12 no longer installs devDependencies by default** on `npm install`. Always use:
```bash
npm install --include=dev
```
Or use `npm ci` which installs everything. If `npm run build` fails with missing type declarations (`@types/react-dom`, `@vitejs/plugin-react`), run `npm install --include=dev` first.

### `allowScripts` field in package.json

If `package.json` has an `allowScripts` field, it **overrides** the `.npmrc` `allow-scripts=true` setting. Only packages listed in `allowScripts` get their postinstall scripts executed — everything else is silently blocked. To allow all scripts, remove the `allowScripts` field entirely from `package.json`.

## Known Limitations

### Light mode text contrast

The portfolio's CSS (`data-theme` attribute-based theming) does not properly invert text colors in light mode. Body text remains light gray, making it nearly illegible on the light background. Buttons, accent elements, and gradient headings retain sufficient contrast.

**Not a priority fix** — the default (system/dark) mode is the primary viewing experience. If fixing, ensure `--text-primary`, `--text-secondary`, and `--text-muted` CSS variables are correctly mapped for the `[data-theme="light"]` selector.

### QA: Theme contrast check

During QA (step 2 above), after clicking the theme toggle to switch to light mode, do a quick visual check with `browser_vision()`. If body text is unreadable, note it as a pre-existing known issue — do not block the deploy.

## CV PDF Generation

### Source files (Obsidian vault)
```
Work-Freelancer/Upwork/cv-migbert-dev-pt.md
Work-Freelancer/Upwork/cv-migbert-dev-es.md
Work-Freelancer/Upwork/cv-migbert-dev-en.md
```

### Destination (portfolio assets)
```
/home/migbert/proyectos/frontend/portfolio-react/src/assets/Curriculum-pt.pdf
/home/migbert/proyectos/frontend/portfolio-react/src/assets/Curriculum-es.pdf
/home/migbert/proyectos/frontend/portfolio-react/src/assets/Curriculum-en.pdf
```

### Tool: fpdf2 (Python, A4, Unicode support)

```python
from fpdf import FPDF

pdf = FPDF('P', 'mm', 'A4')
pdf.add_font('DJV', '', '/usr/share/fonts/TTF/DejaVuSans.ttf')
pdf.add_font('DJV', 'B', '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf')
pdf.add_font('DJV', 'I', '/usr/share/fonts/TTF/DejaVuSans-Oblique.ttf')
```

Key points:
- Strip YAML frontmatter before rendering
- Replace Helvetica with a Unicode font (DejaVu Sans) — fpdf2's built-in fonts don't support em-dash, accented chars, bullets
- Set `auto_page_break` with bottom margin for footer
- Use `multi_cell` for long text, `cell` for short lines
- Add page numbers with `{nb}` alias
- Verify with `npm run build` after replacing PDFs
