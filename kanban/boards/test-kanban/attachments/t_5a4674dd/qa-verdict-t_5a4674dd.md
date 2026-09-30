# Veredicto QA → Manager

## Verdict

**Card:** t_5a4674dd: Verificar integración end-to-end y corregir fallos
**Resultado:** ✅ PASS
**Fecha:** 2026-08-11
**Alcance:** Webapp Kanban demo multi-agente — backend FastAPI/SQLite en `http://127.0.0.1:8000`, frontend React/Chakra UI en `http://localhost:3000`. API (CRUD + validación + concurrencia), UI (crear/mover/eliminar, polling, persistencia, validación), resiliencia ante caída del backend, consola JS, build/lint.

## Resumen (1 línea)
La demo cumple todos los criterios del enunciado (agentes crean/mueven/eliminan vía API, el frontend refleja cambios externos por polling en ≤5 s, sin errores de consola); se corrigieron 3 bugs menores encontrados durante la verificación (2 backend, 1 frontend).

## Evidencia

| # | Severidad | Categoría | URL / pantalla | Screenshot |
|---|-----------|-----------|----------------|------------|
| 1 | — | Funcional | Tablero con tareas en las 3 columnas (estado demo) | MEDIA:`/home/migbert/.hermes/kanban/boards/test-kanban/workspaces/t_5a4674dd/evidence/ui-tablero-3-columnas-pobladas.png` |
| 2 | — | UX | Validación "El título es obligatorio." visible al enviar formulario vacío (post-fix) | MEDIA:`/home/migbert/.hermes/kanban/boards/test-kanban/workspaces/t_5a4674dd/evidence/ui-validacion-titulo-obligatorio.png` |
| 3 | — | Funcional | Tarea QA movida a Done + tarea externa reflejada por polling | MEDIA:`/home/migbert/.hermes/kanban/boards/test-kanban/workspaces/t_5a4674dd/evidence/ui-panel-1-tareas-y-columnas.png` |
| 4 | — | Funcional | Tablero vacío tras eliminar desde la UI | MEDIA:`/home/migbert/.hermes/kanban/boards/test-kanban/workspaces/t_5a4674dd/evidence/ui-panel-2-tras-eliminar.png` |
| 5 | — | Console/UX | Badge "API sin conexión" + alerta al caer el backend (detección) | MEDIA:`/home/migbert/.hermes/kanban/boards/test-kanban/workspaces/t_5a4674dd/evidence/ui-resiliencia-backend-caido.png` |
| 6 | — | Console/UX | Recuperación automática a "API conectada" tras reiniciar el backend | MEDIA:`/home/migbert/.hermes/kanban/boards/test-kanban/workspaces/t_5a4674dd/evidence/ui-resiliencia-recuperado.png` |

## Issues (por hallazgo)

### 1. Título con solo espacios crea tarea sin título vía API (backend)
- **Severidad:** Low
- **Categoría:** Funcional
- **URL:** `POST /tasks`, `PUT /tasks/{id}`
- **Repro steps:**
  1. `POST /tasks` con `{"title": "   "}` → responde **201** con `title: ""`.
  2. `PUT /tasks/{id}` con `{"title": "   "}` → responde **200** con `title: ""`.
- **Esperado:** 422 (título inválido tras recortar espacios).
- **Actual:** Pydantic valida `min_length=1` sobre el valor sin recortar; el `.strip()` posterior en el endpoint convierte `"   "` en `""` y se persiste una tarea sin título.
- **Consola JS:** sin errores.
- **Fix aplicado:** `field_validator("title", mode="before")` en `TaskCreate` y `TaskUpdate` que recorta antes de validar. Re-verificado: 422 en ambos endpoints.

### 2. DELETE no atómico bajo concurrencia (backend)
- **Severidad:** Low
- **Categoría:** Funcional
- **URL:** `DELETE /tasks/{id}`
- **Repro steps:**
  1. Lanzar 5 `DELETE /tasks/{id}` simultáneos sobre la misma tarea.
  2. Los 5 responden **204** (carrera TOCTOU: `_get_task_or_404` hace el SELECT de existencia antes del DELETE; entre SELECT y DELETE otra conexión borra la fila y el DELETE no verifica filas afectadas). En secuencial, el 2º DELETE responde 404: comportamiento inconsistente.
- **Esperado:** exactamente 1×204 + 4×404 (o todos 404/204 idempotente, pero consistente).
- **Actual:** 5×204 en carrera; 204+404 en secuencial.
- **Consola JS:** sin errores.
- **Fix aplicado:�� `DELETE ... WHERE id = ?` + chequeo de `rowcount == 0` → 404 (operación atómica). Re-verificado: 1×204 + 4×404 en carrera, 404 secuencial intacto.

### 3. Validación nativa del navegador bloquea el mensaje de error custom (frontend)
- **Severidad:** Medium
- **Categoría:** UX / Funcional
- **URL:** `http://localhost:3000/` (formulario de creación)
- **Repro steps:**
  1. Cargar la página y pulsar "Crear tarea" con el campo Título vacío.
  2. No aparece "El título es obligatorio."; el navegador muestra la burbuja nativa "Completa este campo" (evento `invalid`, fuera del DOM).
- **Esperado:** mensaje de error de la app visible en el formulario (como en el caso de título con solo espacios).
- **Actual:** Chakra v3 `Field.Root required` propaga el atributo nativo `required` al `<input>`; la validación nativa bloquea el submit vacío y el mensaje custom queda como código muerto en el caso más común. Resultado: dos estilos de error inconsistentes (burbuja nativa vs. mensaje custom) según el contenido.
- **Consola JS:** sin errores.
- **Fix aplicado:** `noValidate` en el `<form>` (validación custom: trim + título obligatorio). Re-verificado: el mensaje custom aparece en ambos casos (vacío y espacios) y no se crean tareas inválidas.

## Notas de prueba
- **Probado:**
  - API: 19/19 checks (GET vacío, POST default/completo, validaciones 422: status inválido, sin título, título vacío, título espacios, título >200; PUT status/título, body vacío 422, título espacios 422, status inválido; DELETE 204/404; PUT inexistente 404; estado final coherente).
  - Concurrencia: 11/11 (30 POST simultáneos → 30×201 sin bloqueos; 20 PUT simultáneos misma tarea → 20×200 sin 5xx; workload mixto 10 agentes × 12 ops → 0 errores; 5 DELETE simultáneos → 1×204+4×404; integridad final: status válidos, sin títulos vacíos, sin ids duplicados; limpieza).
  - UI (Playwright headless Chromium 149): 28/28 (render 3 columnas, badge API conectada, estado vacío, validación vacío y espacios, crear con acentos, mover todo→in_progress→done, flechas deshabilitadas en bordes, polling refleja POST/PUT/DELETE externos sin recargar en ≤5 s, persistencia tras refresh, eliminar con confirm, consola JS limpia).
  - Resiliencia: con backend caído la UI muestra badge "API sin conexión" + alerta y el formulario sigue operable; al reiniciar el backend la UI se recupera sola a "API conectada" y recarga datos (≤2 ciclos de polling). Errores de consola esperados durante la caída: solo `ERR_CONNECTION_REFUSED` del fetch de polling, manejados por la app.
  - Build (`npm run build`): OK, 144 kB gzip. Lint (`npm run lint`): OK, solo 3 warnings de fast-refresh preexistentes en archivos generados por el CLI de Chakra.
- **No probado (bloqueadores):** ninguno. `browser_exec` (harness browser-use) no funciona en esta máquina (no hay Chrome de sistema); se usó playwright-core embebido de Hermes + Chromium 149 con `executablePath` explícito (ruta probada por el worker de frontend).
- **Fricción UX (adversarial):** persona hostil = agente que pulsa submit vacío en frío, agente que envía títulos con espacios por API, 20 agentes moviendo la misma tarea, 5 agentes borrando la misma tarea, backend caído a mitad de sesión. Hallazgos RED: #3 (validación nativa), #1 y #2 (backend). Todo corregido y re-verificado.

## Recomendación
- **PASS:** mover a `done`. Bugs encontrados fueron menores y ya corregidos con re-verificación completa (API 19/19, concurrencia 11/11, UI 28/28). No se requieren bug cards pendientes. Criterios de aceptación del enunciado cumplidos: agentes crean/mueven/eliminan vía API, frontend refleja cambios correctamente (polling 5 s + refresh), demo cumple criterios de prueba.
- Nota para el manager: los servidores quedaron **detenidos** para no bloquear puertos; arrancar con `cd backend && ./venv/bin/uvicorn main:app --reload` y `cd frontend && npm start` (documentado en README.md).
