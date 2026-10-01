# Font Variables & Font Catalog — Verified from Compiled Build

Verified against a real compiled build: `index-D3Rq2b1l.css` (July 2026, ~310KB minified).

## CSS Variable Definitions (in `:root`)

All grep-verified from the actual minified CSS:

| Variable | Value (rem) | px equivalent | Domain |
|---|---|---|---|
| `--dt-base-size` | `1rem` | 16px | Root font-size — scales everything in `rem` |
| `--conversation-text-font-size` | `.8125rem` | 13px | Chat text, markdown, inputs, dialogs, menus |
| `--conversation-tool-font-size` | `.6875rem` | 11px | Tool output blocks, code cards, composer dock |
| `--conversation-caption-font-size` | `.75rem` | 12px | Labels, timestamps, secondary text |
| `--conversation-line-height` | `1.125rem` | — | Line height for tool blocks |
| `--conversation-caption-line-height` | `1rem` | — | Line height for captions |
| `--paragraph-gap` | `.7rem` | — | Gap between markdown paragraphs |

## grep Commands to Verify

The minified CSS is one line — patterns are regex-safe as they don't start with `-` when using `grep -oP`:

```bash
grep -oP '(?<=--)conversation-text-font-size:[^;]+' index-*.css
grep -oP '(?<=--)conversation-tool-font-size:[^;]+' index-*.css
grep -oP '(?<=--)conversation-caption-font-size:[^;]+' index-*.css
grep -oP '(?<=--)dt-base-size:[^;]+' index-*.css
grep -oP '(?<=--)conversation-line-height[^;]+' index-*.css
grep -oP '(?<=--)conversation-caption-line-height[^;]+' index-*.css
grep -oP '(?<=--)paragraph-gap[^;]+' index-*.css
```

Or search-only (find them): `grep -oP 'conversation-(text|tool|caption)-font-size[^;]+' index-*.css`

## Font Catalog (from `web/src/themes/fonts.ts`)

Font override is a separate layer from themes. Each entry: `id`, `label`, `category`, `stack`, optional `fontUrl`.

### System (no webfont fetch)

| id | label | stack |
|---|---|---|
| `system-sans` | System Sans | `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` |
| `system-serif` | System Serif | `Georgia, Cambria, "Times New Roman", Times, serif` |
| `system-mono` | System Mono | `ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace` |

### Sans

| id | label | Google Fonts URL |
|---|---|---|
| `inter` | Inter | `Inter:wght@400;500;600;700` |
| `ibm-plex-sans` | IBM Plex Sans | `IBM+Plex+Sans:wght@400;500;600;700` |
| `work-sans` | Work Sans | `Work+Sans:wght@400;500;600;700` |
| `atkinson-hyperlegible` | Atkinson Hyperlegible | `Atkinson+Hyperlegible:wght@400;700` |
| `dm-sans` | DM Sans | `DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700` |

### Serif

| id | label | Google Fonts URL |
|---|---|---|
| `spectral` | Spectral | `Spectral:wght@400;500;600;700` |
| `fraunces` | Fraunces | `Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600` |
| `source-serif` | Source Serif 4 | `Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600;8..60,700` |

### Mono

| id | label | Google Fonts URL |
|---|---|---|
| `jetbrains-mono` | JetBrains Mono | `JetBrains+Mono:wght@400;500;700` |
| `ibm-plex-mono` | IBM Plex Mono | `IBM+Plex+Mono:wght@400;500;700` |
| `space-mono` | Space Mono | `Space+Mono:wght@400;700` |

## localStorage Keys

| Key | Value | Persistence |
|---|---|---|
| `hermes-dashboard-font` | Font id string (e.g. `"inter"`) or `"theme"` for default | Font override across themes |
| `hermes-dashboard-theme` | Theme name string (e.g. `"nous-blue"`) | Theme selection |
| `hermes-locale` | Locale code (e.g. `"es"`) | Language selection |

## Pitfalls

- The minified CSS has **no spaces after colons**: `--conversation-text-font-size:.8125rem` not `--conversation-text-font-size: .8125rem`. sed replacements must match the no-space format exactly.
- Each variable appears **exactly once** as a definition, but the `var(--name)` usage pattern appears many times. Only patch the definition (the `:` assignment), never every `var()` occurrence.
- After an app update, `index-*.css` gets a new content-hash. The old file stays on disk but is unused. Re-apply patches to the new hash.
- Backend allow-list in `hermes_cli/web_server.py` (`_FONT_CHOICES`) must stay in sync with the frontend catalog. A mismatch causes server rejection of the font override.
