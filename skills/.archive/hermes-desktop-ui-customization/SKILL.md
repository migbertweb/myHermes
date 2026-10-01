---
name: hermes-desktop-ui-customization
description: Customize the Hermes Desktop app — font/size CSS patching, font family from native UI, and i18n locale system (5 desktop vs 16 dashboard locales). Covers both source-code analysis and release-build asset patching.
---

# Hermes Desktop UI Customization

Three aspects of the UI can be customized: **language** (desktop app: 5 locales; web dashboard: 16 locales), **font family** (native picker in the ThemeSwitcher), and **font sizing / spacing** (CSS patch to the compiled build).

## Key CSS Variables

Defined in `styles.css` (`:root` block) and compiled into a single minified `index-*.css` in the release build:

| Variable | Default (rem) | Default (px) | Purpose |
|---|---|---|---|
| `--conversation-text-font-size` | 0.8125rem | 13px | Main chat text, markdown, inputs, dialogs, menus |
| `--conversation-tool-font-size` | 0.6875rem | 11px | Tool output blocks, code cards, composer dock |
| `--conversation-caption-font-size` | 0.75rem | 12px | Labels, timestamps, secondary text |
| `--conversation-line-height` | 1.125rem | — | Line height for tool blocks |
| `--conversation-caption-line-height` | 1rem | — | Line height for captions |
| `--paragraph-gap` | 0.7rem | — | Gap between markdown paragraphs |
| `--dt-base-size` | 1rem | 16px | HTML root `font-size` — scales all `rem` values |

These variables are consumed throughout the codebase via Tailwind utility `text-[length:var(--variable-name)]`.

## Finding the Compiled CSS

The packaged Electron app bundles the minified CSS in the release directory:

```
release/linux-unpacked/resources/app.asar.unpacked/dist/assets/index-*.css
```

It's typically a **single minified line** (~300KB). The file is **not** inside `app.asar` — it lives in `app.asar.unpacked` so it can be patched directly without ASAR repacking.

## Patching the Compiled CSS

1. Find the CSS file:
   ```bash
   ls ~/.hermes/hermes-agent/apps/desktop/release/linux-unpacked/resources/app.asar.unpacked/dist/assets/index-*.css
   ```

2. The CSS variables are defined in the `:root` block as a continuous chain (mind the minified format — no spaces after colons):
   ```css
   --conversation-text-font-size:.8125rem;--conversation-tool-font-size:.6875rem;--conversation-caption-font-size:.75rem
   ```

3. Replace the definition values (NOT `var()` — usage pattern). Each variable appears **exactly once** as a definition in the file. Example:
   ```bash
   sed -i 's/--conversation-text-font-size:\.8125rem/--conversation-text-font-size:\.875rem/g' index-*.css
   ```

4. Reload the app with `Ctrl+R` or restart Hermes Desktop.

### Verifying

After patching, confirm the new values are the only ones present:
```bash
grep -o '--conversation-text-font-size[^;]*' index-*.css
```

## Language / i18n — Web Dashboard vs Desktop App

⚠️ **CRITICAL: There are TWO separate i18n systems.** Do not confuse them.

| System | Location | Locales | Has Español? |
|---|---|---|---|
| **Web dashboard** (served at `/dashboard` by the Hermes backend) | `web/src/i18n/` | 16 locales | ✅ Sí |
| **Desktop app** (Electron) | `apps/desktop/src/i18n/` | 5 locales | ✅ Sí (es.ts, ~2,484 lines) |

### Desktop App i18n (Electron)

The desktop app has its **own** i18n system with only 4 built-in locales:

| Código | Idioma |
|---|---|
| `en` | English |
| `es` | Español |
| `zh` | 简体中文 |
| `zh-hant` | 繁體中文 |
| `ja` | 日本語 |

Files are at `apps/desktop/src/i18n/` — NOT `web/src/i18n/`.

### How to add Español (or any other locale) to the Desktop App

The system uses a `defineLocale(partial)` helper that inherits untranslated strings from English — partial translations work immediately.

**Step 1 — Add `'es'` to the Locale type** (`apps/desktop/src/i18n/types.ts`):
```diff
- export type Locale = 'en' | 'zh' | 'zh-hant' | 'ja'
+ export type Locale = 'en' | 'zh' | 'zh-hant' | 'ja' | 'es'
```

**Step 2 — Create the translation file** (`apps/desktop/src/i18n/es.ts`):
```typescript
import { defineLocale } from './define-locale'

export const es = defineLocale({
  common: {
    save: 'Guardar',
    cancel: 'Cancelar',
    close: 'Cerrar',
    // ... translate what you need, everything else falls back to English
  },
  // ... all sections are optional with defineLocale()
})
```

> ✅ **Existing reference:** A complete ~2,484-line Spanish translation (`apps/desktop/src/i18n/es.ts`) was created in July 2026 covering every section of the `Translations` interface. Use it as a model when adding other locales — it shows the scale of a full override vs the minimal stub above.
    description: 'Selecciona el idioma de la interfaz de escritorio.',
    saving: 'Guardando idioma...',
    saveError: 'Error al actualizar el idioma',
    switchTo: 'Cambiar idioma',
    searchPlaceholder: 'Buscar idioma...',
    noResults: 'No se encontraron idiomas',
  },
  // ... all sections are optional with defineLocale()
})
```

**Step 3 — Register in catalog** (`apps/desktop/src/i18n/catalog.ts`):
```diff
  import { en } from './en'
+ import { es } from './es'
  export const TRANSLATIONS: Record<Locale, Translations> = {
    en,
+   es,
    // ...
  }
```

**Step 4 — Add to locale options** (`apps/desktop/src/i18n/languages.ts`):
```diff
  export const LOCALE_OPTIONS = [
    { id: 'en', name: 'English', englishName: 'English', configValue: 'en' },
+   { id: 'es', name: 'Español', englishName: 'Spanish', configValue: 'es' },
    // ...
  ]
```

**Step 5 — Add aliases** (`apps/desktop/src/i18n/languages.ts`):
```diff
  const LOCALE_ALIASES: Record<string, Locale> = {
+   es: 'es',
+   'es-es': 'es',
+   'es-mx': 'es',
    // ...
  }
```

**Step 6 — Rebuild**:
```bash
cd ~/.hermes/hermes-agent/apps/desktop && npm run build
```

### Web Dashboard i18n (16 locales)

The web dashboard at `web/src/i18n/` has 16 fully translated locales including Español (`es.ts`, ~765 lines). This uses a **different** React context (`I18nProvider` at `web/src/i18n/context.tsx`) with localStorage persistence under the `hermes-locale` key.

**Supported dashboard locales:**

`en`, `zh`, `zh-hant`, `ja`, `de`, `es`, `fr`, `tr`, `uk`, `af`, `ko`, `it`, `ga`, `pt`, `ru`, `hu`

**Architecture (dashboard):**

| Layer | File(s) | Role |
|---|---|---|
| Types | `web/src/i18n/types.ts` | `Locale` union type, `Translations` interface |
| Context | `web/src/i18n/context.tsx` | React provider, `getInitialLocale()`, `setLocale()`, `useI18n()` hook |
| Translations | `web/src/i18n/{es,en,de,...}.ts` | One file per locale |
| UI | `web/src/components/LanguageSwitcher.tsx` | Dropdown / bottom-sheet picker in the sidebar |

### Pitfall: wrong source directory

When investigating i18n issues, always verify which codebase you're in:
- `web/src/i18n/` = dashboard, 16 locales, no build step to edit
- `apps/desktop/src/i18n/` = desktop app, 4 locales, requires rebuild

## Font Selection (Native UI)

Font **family** can be changed from the UI — no CSS patch required. The **ThemeSwitcher** component (sidebar → palette icon) includes a **Font** section below the theme list with **12 curated options** plus "Theme default".

Font override is **independent of the active theme**: switching themes keeps your font choice. Persisted in `localStorage` (`hermes-dashboard-font`).

### Available fonts

**Sans:** System Sans, Inter, IBM Plex Sans, Work Sans, Atkinson Hyperlegible, DM Sans
**Serif:** System Serif, Spectral, Fraunces, Source Serif 4
**Mono:** System Mono, JetBrains Mono, IBM Plex Mono, Space Mono

Catalog defined in `web/src/themes/fonts.ts` — each entry has `id`, `label`, `category`, `stack`, and optional `fontUrl` (Google Fonts). The backend allow-list in `hermes_cli/web_server.py` (`_FONT_CHOICES`) must stay in sync with the frontend catalog.

### Programmatic font override

Font choice is stored in localStorage under `hermes-dashboard-font` as a font id string. Setting it to `"theme"` resets to the active theme's default.

## Limitations

- **Desktop app only ships 5 locales** (en, es, zh, zh-hant, ja) — the web dashboard has 16. Adding a locale requires creating the translation file, registering it in 3 places, and rebuilding. See `i18n` section above for exact steps.
- **No settings UI exists for font SIZE** — only font family has a native picker. The Appearance settings only control theme colors and translucency, not typography sizing. Font size requires the CSS-patch approach documented above.
- **JS bundle may contain hardcoded sizes** that don't use the CSS variables — these won't scale with the variable changes. Affected areas: terminal output sizing, code editor, some pet overlay hardcoded `fontSize`. The main chat text is fully variable-driven.
- **Updates may overwrite the CSS** — the `index-*.css` filename changes with every Vite build (content-hash), so an app update will create a new hash and leave the old file untouched but unused. After an update, re-apply the patch to the new hash file.
- **Source edits require a rebuild** — editing `src/styles.css` and running `npm run build` is the developer path. The release-build CSS patching approach is for users who don't want to rebuild.

## Approach: Release Patching vs Source Edit

| Approach | Durability | Complexity |
|---|---|---|
| Patch compiled `index-*.css` | Survives relaunch, lost on app update | Low — direct file edit |
| Edit `src/styles.css` + rebuild | Survives everything | High — needs full dev build toolchain |
| Inject via Electron preload | Survives relaunch, lost on reinstall | Medium — needs to modify preload.cjs |

## References

- `references/font-variables-analysis.md` — Verified CSS variable values from compiled build, font catalog, grep commands for verification
- `references/desktop-i18n-architecture.md` — Desktop app i18n architecture: file structure, how to add a locale, defineLocale helper, differences vs web dashboard
