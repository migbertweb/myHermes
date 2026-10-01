# Veredicto QA → Manager

> Formato obligatorio de salida del agente QA para cada tarjeta.
> El QA vota; el manager decide.

## Verdict

**Card:** `<card-id>: <título>`
**Resultado:** ✅ PASS | ❌ FAIL | ⚠️ PASS CON RESERVAS
**Fecha:** `YYYY-MM-DD`
**Alcance:** `<lo que se probó / URL / rama>`

## Resumen (1 línea)
`<Ej: "El flujo de login funciona pero rompe en reset de password".>`

## Evidencia
| # | Severidad | Categoría | URL / pantalla | Screenshot |
|---|-----------|-----------|----------------|------------|
| 1 | Critical/High/Medium/Low | Funcional/Visual/Accessibility/Console/UX/Content | `/login` | MEDIA:`<path>` |

## Issues (por hallazgo)

### 1. `<título del hallazgo>`
- **Severidad:** Critical | High | Medium | Low
- **Categoría:** Funcional | Visual | Accessibility | Console | UX | Content
- **URL:** `<dónde ocurre>`
- **Repro steps:**
  1. `...`
  2. `...`
- **Esperado:** `...`
- **Actual:** `...`
- **Consola JS:** `<errores si hay, si no: "sin errores">`
- **Screenshot:** MEDIA:`<path>`

## Notas de prueba
- **Probado:** `...`
- **No probado (bloqueadores):** `...`
- **Fricción UX (adversarial):** `<persona usada + hallazgos RED/GREEN del filtro>`

## Recomendación
- **PASS:** mover a `done`.
- **FAIL:** regresar a `in_progress` con la lista de issues.
- **PASS CON RESERVAS:** mover a `done` pero crear bug card para lo pendiente.
