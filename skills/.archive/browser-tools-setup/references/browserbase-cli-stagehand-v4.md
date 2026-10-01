# Browserbase CLI + Stagehand v4 (standalone use)

Durable notes from the 2026-08-13 onboarding session on the laptop (CachyOS).
This covers driving Browserbase from your own scripts/terminal — separate from
using it as a Hermes browser-tools cloud provider (see main SKILL.md).

## Setup

```bash
npm install -g browse@latest          # the unified CLI (replaces deprecated @browserbasehq/cli, @browserbasehq/browse-cli)
browse --version
```

- The CLI prints an "Update available" banner on every command — informational
  noise, strip it before parsing JSON (`grep -v "Update available"`).
- **No `BROWSERBASE_PROJECT_ID` anywhere.** The API key alone identifies the
  project. Old Stagehand docs / training data saying otherwise are outdated.

## Verify access

```bash
browse cloud projects list      # key works if it returns projects
browse cloud sessions list      # recent browser sessions (Fetch/Search create none)
```

## Free-tier rules

- **Fetch API** (`browse cloud fetch <url>`) = lightweight HTTP, no browser
  session, no browser-time cost. Success is a payload, NOT a session row.
- **Search API** = URL/structured results, no session.
- **Proxies / Verified / CAPTCHA solving = paid.** Bot-protected targets
  (LinkedIn, Yelp, Instagram, large retailers) will block a plain free session.
  Warn before running, then steer to a free-tier alternative.
- **Model Gateway** included on Free up to $5 of tokens. Leave `MODEL_API_KEY`
  and other LLM provider keys BLANK so Stagehand routes through the Browserbase
  key; a placeholder value causes a misleading "API key not valid" error.

## Stagehand v4 — API break (critical)

Stagehand 4.0.0 (current `@browserbasehq/stagehand@latest`) is a **total rewrite**.
Template code written for v3 (`new Stagehand({...})` + `stagehand.init()` +
`stagehand.context.pages()` + `stagehand.browserbaseSessionID`) is **broken**.
v4 API:

```ts
import { browserbase, Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod/v4";               // v4 imports from "zod/v4", not "zod"

const browser = await browserbase.launch({ apiKey: process.env.BROWSERBASE_API_KEY! });
const stagehand = await Stagehand.create({ browser });   // static create, no init()
const [page] = await browser.context.pages();            // pages come from browser, not stagehand
await page.goto(url, { waitUntil: "domcontentloaded" });
const result = await stagehand.extract("...instruction...", PageDataSchema);
// model NOT configured → Browserbase Model Gateway picks one automatically
await stagehand.close();
await browser.close();
```

Key changes:
- `Stagehand.create({ browser })` replaces `new Stagehand()` + `stagehand.init()`.
- `browserbase.launch()` (or `localBrowser.launch()`) supplies the browser.
- Session id for Live View: `browser.sessionID` (NOT `stagehand.browserbaseSessionID`).
- Model config is now `model: { modelName, apiKey }`; with no model at all,
  Model Gateway auto-selects (best for free tier — zero LLM keys).
- Needs `zod@^4` (`npm install zod@^4`); the `zod/v4` import path requires it.

### Debugging pattern that worked

Template `smart-fetch-scraper` (cloned 2026-08-13) shipped v3-style code but
installed v4 — failure surfaced as a **misleading error**: `TypeError: browser
must be created by localBrowser or browserbase` at `Stagehand.close()`. The
template's `finally { await stagehand.close() }` masked the real error. Fix:
write a minimal standalone script that calls init/create directly with NO
finally wrapper to see the true error (`stagehand.init is not a function`).

## Template workflow (browse templates)

```bash
browse templates list                       # slugs drift — always confirm before cloning
browse templates clone <slug> /tmp/<slug>   # sandbox; some clones print pnpm steps but npm works
```

- `.env`: set `BROWSERBASE_API_KEY`, blank every LLM/provider key + any
  `BROWSERBASE_PROJECT_ID` placeholder.
- Run TS templates with `npx tsx index.ts <url>` — the Hermes terminal flags
  `npm start` as a long-lived server (false positive); call tsx directly.
- Demo target choices: Hacker News works via Fetch (static HTML, no browser);
  demoblaze.com is a JS-rendered e-commerce demo site with zero bot protection
  — good for forcing the browser fallback path.
