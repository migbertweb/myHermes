# Desktop App i18n Architecture

Verified against `apps/desktop/src/i18n/` (v0.17.0, Jul 2026).

## File Structure

```
apps/desktop/src/i18n/
├── catalog.ts          ← Registry: imports locale modules into TRANSLATIONS Record
├── context.test.tsx
├── context.tsx         ← React I18nProvider, config-backed persistence (saves to Hermes config)
├── define-locale.ts    ← Helper: defineLocale(partial) → merges overrides onto English base
├── en.ts               ← English translations (the base, full Translations interface)
├── es.ts               ← Spanish translations (added Jul 2026, ~2,484 lines, full override via defineLocale)
├── ja.ts               ← Japanese translations
├── languages.test.ts
├── languages.ts        ← LOCALE_OPTIONS, LOCALE_META, LOCALE_ALIASES, isLocale(), normalizeLocale()
├── runtime.test.ts
├── runtime.ts          ← Sets runtime i18n locale for boot/notifications
├── types.ts            ← Locale type, Translations interface, ToolTitleKey
├── zh-hant.ts          ← Traditional Chinese translations
└── zh.ts               ← Simplified Chinese translations
```

## Locale Count

**5 locales built-in:** en, es, zh, zh-hant, ja

The **web dashboard** (`web/src/i18n/`) has a completely separate i18n system with 16 locales. Do not conflate the two.

## The defineLocale() Helper

`define-locale.ts` exports a `defineLocale(overrides: TranslationOverrides)` function. It takes a partial translations object and merges it onto the **English base** (`en.ts`). Any untranslated key inherits the English string.

```typescript
import { defineLocale } from './define-locale'

export const es = defineLocale({
  common: {
    save: 'Guardar',
    // everything else → English fallback
  },
})
```

The `TranslationOverrides` type makes every key optional and recursively partial, so only the translated keys need to be provided.

**Template literal functions** (e.g. `deleteTitle: name => \`Delete ${name}?\``) are translated by providing a function with the same signature:

```typescript
deleteTitle: name => `¿Eliminar ${name}?`,
```

The function signature must exactly match the `Translations` type — `defineLocale()` passes it through without modification.

**Parallel setup trick:** the translation file creation and the 3 registration edits (`types.ts`, `catalog.ts`, `languages.ts`) are independent tasks. Dispatch them as parallel subagents for speed.

## Adding a Locale — 5 Files to Touch

| # | File | Change |
|---|---|---|
| 1 | `types.ts` | Add locale code to `Locale` union type |
| 2 | New file `es.ts` | Create with `defineLocale({...})` — see full ~2,484-line reference at `apps/desktop/src/i18n/es.ts` |
| 3 | `catalog.ts` | Import + register in `TRANSLATIONS` |
| 4 | `languages.ts` | Add to `LOCALE_OPTIONS` + `LOCALE_ALIASES` |
| 5 | Rebuild | `npm run build` in `apps/desktop/` |

**Note about `isLocale()` and `normalizeLocale()`:** both functions are dynamic — `isLocale()` uses `LOCALE_OPTIONS.some()` and `normalizeLocale()` uses `LOCALE_ALIASES`. Neither needs a code change when adding a locale, as long as the locale is added to both arrays.

**TS error to expect after step 3:** TypeScript will report `Property 'es' is missing in type '...' but required in type 'Record<Locale, Translations>'` until the actual locale file exists. This is normal — it means the type system found the new union member and is correctly enforcing completeness.

## How Locale Persistence Works

Unlike the web dashboard (which uses localStorage), the desktop app **saves the locale to the Hermes config file** via `saveHermesConfig()` → `hermes.config.set('display.language', value)`. On startup, it reads the config and normalizes the locale via `normalizeLocale()`.

## Verifying Compiled Locale Data

To check which locales are actually in the built JS:

```bash
grep -oP 'englishName:`[^`]*`' dist/assets/index-*.js
```

This lists all locale englishName values present in the compiled bundle. If a locale isn't here, it wasn't included in the build.

Example output (4-locale build):
```
englishName:`English`
englishName:`Spanish`
englishName:`Simplified Chinese`
englishName:`Traditional Chinese`
englishName:`Japanese`
```

## How the LanguagePicker Works (Compiled)

The compiled JS has an `Ipo` (LanguagePickerOptions) component that receives `allLocales` as an array of `[localeCode, { name, englishName }]` tuples. It renders a searchable list with:
- Native name (`name`) — shown to user
- English name (`englishName`) — search-only, so English speakers can type "japanese" to find 日本語
- Locale code — shown in monospace at right

## Key Differences: Desktop vs Web Dashboard

| Aspect | Desktop (`apps/desktop/src/i18n/`) | Dashboard (`web/src/i18n/`) |
|---|---|---|
| Locales | 5 | 16 |
| Has Spanish | ✅ Sí (es.ts, ~2,484 lines, added Jul 2026) | Yes (es.ts, ~765 lines) |
| Build step to add locale? | Yes (npm run build) | No (Vite dev server) |
| Persistence | Hermes config file | localStorage |
| Component | Settings-based LanguagePicker | Sidebar LanguageSwitcher |
| Partial locale support | Yes (defineLocale helper) | Yes (optional keys fall back to template literal) |
