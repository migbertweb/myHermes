---
name: hermes-desktop-i18n-add-locale
description: Add a new language/locale to the Hermes Desktop Electron app i18n system. Covers creating translation files with defineLocale(), registering in types/catalog/languages, and rebuilding.
---

# Add a Locale to Hermes Desktop i18n

Add a new language to the **desktop app** (`apps/desktop/src/i18n/`) — NOT the web dashboard (`web/src/i18n/`). These are separate systems.

## Overview

5 files to touch:

| # | File | Action |
|---|------|--------|
| 1 | `src/i18n/types.ts` | Add `'<code>'` to the `Locale` union type |
| 2 | `src/i18n/catalog.ts` | Import + register the new locale in `TRANSLATIONS` |
| 3 | `src/i18n/languages.ts` | Add to `LOCALE_OPTIONS` + `LOCALE_ALIASES` |
| 4 | `src/i18n/<locale>.ts` | Create translation file using `defineLocale()` |
| 5 | Build | `npm run build` + copy assets to release dir |

## Step-by-step

### 1. Edit `types.ts` — add to `Locale` type

File: `apps/desktop/src/i18n/types.ts`

```diff
- export type Locale = 'en' | 'es' | 'zh' | 'zh-hant' | 'ja'
+ export type Locale = 'en' | 'es' | 'fr' | 'zh' | 'zh-hant' | 'ja'
```

### 2. Edit `catalog.ts` — import + register

File: `apps/desktop/src/i18n/catalog.ts`

```diff
  import { en } from './en'
  import { es } from './es'
+ import { fr } from './fr'
  import { ja } from './ja'
  import type { Locale, Translations } from './types'
  import { zh } from './zh'
  import { zhHant } from './zh-hant'

  export const TRANSLATIONS: Record<Locale, Translations> = {
    en,
    es,
+   fr,
    zh,
    'zh-hant': zhHant,
    ja
  }
```

### 3. Edit `languages.ts` — LOCALE_OPTIONS + aliases

File: `apps/desktop/src/i18n/languages.ts`

Add to `LOCALE_OPTIONS` array (keep alphabetical-ish order):

```ts
  {
    id: 'fr',
    name: 'Français',              // Endonym (native name)
    englishName: 'French',          // Search term (not shown)
    configValue: 'fr'
  },
```

Add to `LOCALE_ALIASES`:

```ts
  fr: 'fr',
  'fr-fr': 'fr',
  fr_fr: 'fr',
  'fr-ca': 'fr',
  fr_ca: 'fr',
```

⚠️ **`isLocale()` does NOT need changes** — it uses `LOCALE_OPTIONS.some()` dynamically.

### 4. Create translation file using `defineLocale()`

File: `apps/desktop/src/i18n/fr.ts`

```typescript
import { defineLocale } from './define-locale'

export const fr = defineLocale({
  common: {
    save: 'Enregistrer',
    saving: 'Enregistrement…',
    cancel: 'Annuler',
    // ... translate only keys you want, rest inherits from English
  },
  // ...
})
```

**Key rules:**
- Use `defineLocale()` — NOT the raw `Translations` type. This allows partial translations; missing keys fall back to English.
- Template-literal functions keep the same shape:
  ```ts
  // EN: deleteTitle: name => `Delete ${name}?`
  // FR: deleteTitle: name => `Supprimer ${name} ?`
  ```
- The `en.ts` file (2515 lines) is the complete reference for all keys.
- Import `FIELD_LABELS` / `FIELD_DESCRIPTIONS` from `@/app/settings/constants` is handled by `defineLocale()` — you DON'T need these in your translation file.
- For a new locale, create a comprehensive translation covering: `common`, `fileMenu`, `boot`, `language`, `titlebar`, `keybinds`, `notifications` (incl. `region`, `voice`, `native`), `settings` (all subsections), `starmap`, `composer`, `tools`/`assistant` sections.
- NOMBRES PROPIOS que NO se traducen: "Hermes", "Hermes Desktop", nombres de proveedores (OpenAI, Anthropic, etc.), términos técnicos (Gateway, IPC, MCP, OAuth, PKCE, Sidebar, Titlebar, Starmap, Keybinds).
- **GENERACIÓN DEL ARCHIVO — DELEGA A SUBAGENT**: `en.ts` tiene ~2,500 líneas. Escribirlo inline en el contexto del agente principal CAUSA TRUNCAMIENTO (se corta a mitad de archivo, dejando un objeto TS inválido). Usa `delegate_task` (role: leaf) con su propia ventana de contexto. Pásale: ruta de `en.ts` como referencia, el mapa de secciones (`references/en-ts-section-map.md`), reglas de traducción, y la instrucción de usar `defineLocale()`. El subagent no se trunca.
- **PERO EL SUBAGENT TAMBIÉN PUEDE TRUNCARSE/TIMEOUT**: En la práctica, un subagent leaf intentando generar un archivo de 2,500 líneas en UNA sola operación `write_file` se cortó a la línea ~648 (dentro de `settings.mcp`) dejando el objeto TS inválido. Otro subagent en paralelo hizo timeout (600s) sin escribir nada. LECCIÓN: la generación de un locale completo NO es confiable en un solo paso.
- **MITIGACIÓN CONFIABLE — EL PADRE TERMINA EN CHUNKS**: Si el subagent entrega un archivo incompleto (verificable con `wc -l` + `tail` + conteo de llaves `{}`), el PADRE debe finalizarlo usando `patch` con `old_string` = últimas líneas exactas del archivo y `new_string` = esas mismas + TODO lo que falta (el patch completo de ~1,800 líneas SÍ cabe en una llamada `patch` del padre porque no ocupa todo el contexto, solo se añade). Esto evitó un nuevo truncamiento y el archivo quedó válido (2,522 líneas, 530/530 llaves balanceadas).
- **SIEMPRE VERIFICA ANTES DE BUILD**: Tras cualquier generación/finalización, corre:
  ```bash
  wc -l <locale>.ts
  tail -3 <locale>.ts          # debe terminar en })
  node -e "const s=require('fs').readFileSync('<locale>.ts','utf8'); const o=(s.match(/{/g)||[]).length,c=(s.match(/}/g)||[]).length; console.log(o,c,o===c?'BALANCED':'UNBALANCED')"
  grep -cE "^  <seccion>: \{" <locale>.ts   # cada top-level debe aparecer 1 vez (sin duplicados)
  ```
  Si está incompleto/desbalanceado, aplica la mitigación de chunks arriba. NO corras build con un archivo roto.

### 5. Build + deploy

```bash
cd ~/.hermes/hermes-agent/apps/desktop
npm run build
```

Then copy the new build artifacts to the release directory:

```bash
cd ~/.hermes/hermes-agent/apps/desktop

# Remove old JS bundle (different hash per build)
rm -f release/linux-unpacked/resources/app.asar.unpacked/dist/assets/index-*.js

# Copy new build
cp dist/assets/index-*.js   release/linux-unpacked/resources/app.asar.unpacked/dist/assets/
cp dist/assets/index-*.css  release/linux-unpacked/resources/app.asar.unpacked/dist/assets/
cp dist/index.html          release/linux-unpacked/resources/app.asar.unpacked/dist/
cp dist/electron-main.mjs   release/linux-unpacked/resources/app.asar.unpacked/dist/
cp dist/electron-preload.js release/linux-unpacked/resources/app.asar.unpacked/dist/
```

Restart Hermes Desktop to pick up the new locale.

## Verification & lint (PASO OBLIGATORIO)

El usuario requiere lint final antes de dar por terminado. Ejecutar SIEMPRE:

```bash
cd ~/.hermes/hermes-agent/apps/desktop
npx tsc --noEmit          # Debe salir 0 errores
npm run build             # Rebuild después de crear el archivo de traducción
```

Si `tsc --noEmit` reporta errores de tipos en el nuevo `<locale>.ts`, el build fallará
en `tsc -b`. Corregir antes de copiar assets al release.

Luego copiar build al release (ver Paso 5) y verificar strings compilados.

## Referencias de la skill

- `references/en-ts-section-map.md` — mapa de las ~2,529 líneas de `en.ts`: todas las
  claves top-level, sub-secciones y reglas de traducción. Pásalo al subagent que
  genere el archivo de traducción para que no tenga que leer `en.ts` en tu contexto.

## Verification

After rebuilding, confirm the locale strings are compiled in:

```bash
grep -oP 'Guardar|Español|Idioma|Configuración' \
  release/linux-unpacked/resources/app.asar.unpacked/dist/assets/index-*.js
```

Check the locale selector shows all expected languages:

```bash
grep -oP 'Español|English|Français|日本語|简体中文|繁體中文' \
  release/linux-unpacked/resources/app.asar.unpacked/dist/assets/index-*.js
```

## Pitfalls

- **Tarea larga = truncamiento en contexto principal**: Crear un archivo de ~2,500 líneas (`<locale>.ts`) inline en tu contexto se corta a mitad (objeto TS inválido, roto en `settings.mcp`). SOLUCIÓN: delegar generación a subagent (`delegate_task`, role leaf) con su propia ventana. Ver sección "Create translation file" arriba.
- **EL SUBAGENT TAMBIÉN SE TRUNCA/TIMEOUT en archivos de ~2,500 líneas**: Un subagent leaf en `write_file` único se cortó en la línea ~648 (dentro de `settings.mcp`); otro hizo timeout (600s) sin escribir nada. NO confíes en un solo paso para un locale completo. Si el archivo quedó incompleto, el PADRE debe finalizarlo con `patch` (old_string = últimas líneas, new_string = esas + resto). Ver mitigación en "Create translation file".
- **Verificación obligatoria post-generación**: Antes de `npm run build`, valida que el archivo termine en `})`, que las llaves `{}` estén balanceadas (node one-liner arriba) y que cada sección top-level aparezca exactamente 1 vez (sin duplicados por escritura concurrente de subagents). Un archivo roto hace fallar `tsc -b` y el build.
- **`defineLocale()` imports FAIL at build time** if `es.ts` has syntax errors. The TypeScript compiler (`tsc -b`) runs before Vite. Test with `npx tsc --noEmit` first.
- **Hash collision on CSS but not JS**: the CSS hash may stay the same between builds if Vite detects no CSS changes. Copy it anyway — the JS hash ALWAYS changes when source changes.
- **Release vs dist**: `npm run build` writes to `dist/`. The packaged app reads from `release/linux-unpacked/resources/app.asar.unpacked/dist/`. You MUST copy files between these directories — there's no `npm run package` shortcut.
- **ASAR vs unpacked**: The renderer assets live in `app.asar.unpacked` (not inside `app.asar`), so they can be patched directly without repacking. This is intentional and makes deployment easy.

## Reference

| Path | Description |
|---|---|
| `apps/desktop/src/i18n/` | All i18n source files |
| `apps/desktop/src/i18n/en.ts` | English translations (2,515 lines — complete reference) |
| `apps/desktop/src/i18n/es.ts` | Spanish translations (2,484 lines — example of full locale) |
| `apps/desktop/src/i18n/define-locale.ts` | Helper for partial locales with English fallback |
| `apps/desktop/src/i18n/types.ts` | Translations interface + Locale type |
| `apps/desktop/src/i18n/catalog.ts` | Registry of all translation files |
| `apps/desktop/src/i18n/languages.ts` | LOCALE_OPTIONS + LOCALE_ALIASES |
| `apps/desktop/release/linux-unpacked/resources/app.asar.unpacked/dist/` | Build output consumed by Electron |
