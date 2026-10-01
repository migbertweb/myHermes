---
name: pen-design
description: Use for visual designs, mockups, UI via pen.dev MCP (opencode).
---

# pen.dev Design (vía opencode + MCP pencil)

Crea diseños visuales profesionales (websites, app screens, dashboards, slides, marketing assets) usando **pen.dev** a través del **MCP `pencil`** que corre en opencode.

## Arquitectura (VERIFICADA 2026-08-23)

```
Hermes → opencode run → MCP pencil (mcp-server-linux-x64) → pen.dev → archivo .pen + PNG exportado
```

- El MCP `pencil` está configurado en `~/.config/opencode/opencode.json` (`mcp.pencil`)
- Ejecutable: `/home/migbert/.pencil/mcp/vscodium/out/mcp-server-linux-x64 --app vscodium --agent openCodeCLI`
- pen.dev debe estar abierto/corriendo (VSCodium con la extensión, o la app pen.dev) para que el MCP responda
- **NO** añadir `pencil` como MCP directo de Hermes (`hermes mcp add` falla con "Connection closed" — el server es stdio corto-vida diseñado para el cliente opencode)

## Herramientas del MCP pencil

| Herramienta | Función |
|---|---|
| `pencil_get_app_state` | Estado actual del canvas: archivo activo, nodos seleccionados, top-level nodes |
| `pencil_read_skill` | Docs de la API `execute` (leer `execute.md` para referencia completa) |
| `pencil_execute` | Ejecuta JavaScript para crear/modificar el diseño. Params: `filePath`, `input` (código JS) |

## Procedimiento

### 1. Verificar readiness

```bash
opencode --version          # debe responder
# Verificar que el MCP pencil está configurado:
grep -A5 '"pencil"' ~/.config/opencode/opencode.json
```

Si `pencil` no está en la config de opencode, hay que añadirlo:
```json
"mcp": {
  "pencil": {
    "command": ["/home/migbert/.pencil/mcp/vscodium/out/mcp-server-linux-x64", "--app", "vscodium", "--agent", "openCodeCLI"],
    "enabled": true,
    "type": "local"
  }
}
```

### 2. Crear un diseño

Delegar a opencode con instrucciones precisas:

```bash
opencode run 'Create a design with pen.dev MCP. Generate a <DESCRIPCIÓN>. Save the .pen file to <RUTA>.pen and export a PNG preview to <RUTA>.png. Use the pencil MCP tools to create this design.'
```

**Reglas para el prompt:**
- Pasar el request del usuario **tal cual**, sin expandir ni añadir detalles creativos propios — el agente de pen.dev toma las decisiones de layout/colores/tipografía
- Especificar rutas absolutas para `.pen` y `.png`
- Usar `--format json` para output machine-readable
- Timeout generoso: ≥ 600s (diseños complejos tardan 3-5+ min)

**Modelo**: opencode usa `omniroute` (configurado en su json) — el modelo real lo elige OmniRoute. Se puede forzar con `--model omniroute/auto/best-coding` o el deseado.

### ⚠️ Dónde quedan los archivos (VERIFICADO)

- **`.pen`**: el `filePath` del MCP es una **referencia de documento interno**, NO una ruta literal en disco. El diseño real vive en el canvas del editor de pen.dev y se persiste en `~/.pencil/documents/<uuid>/pencil-*.pen`. **No esperar** que aparezca un `.pen` en la ruta pedida (el agente de opencode reporta éxito pero el archivo no se crea ahí).
- **Export PNG**: SÍ respeta la ruta pedida, pero crea un **directorio** con el nombre pedido y escribe `<nodeId>.png` dentro: `export()/s7dNSa.png`. Buscar el PNG con `find <dir> -name "*.png"`.
- Para iterar sobre un diseño existente, opencode usa el documento activo del canvas (el `pencil_get_app_state` muestra cuál está abierto) — no apuntar a un `.pen` local.

### 3. Iterar sobre un diseño existente

```bash
opencode run 'Modify the existing pen.dev design at <RUTA>.pen. <CAMBIOS DESEADOS>. Save to <RUTA>-v2.pen and export PNG to <RUTA>-v2.png.'
```

Naming pattern: `design.pen` → `design-v2.pen` → `design-v3.pen`

### 4. Mostrar el resultado

Después de completar, leer el PNG exportado con `vision_analyze` y mostrarlo al usuario. Siempre mostrar la imagen — es el punto de la herramienta.

## API `execute` de pen.dev (referencia rápida)

Dentro del código JS que opencode pasa a `pencil_execute`:

**Mutaciones:**
```js
Insert(parent, nodeData)                    // inserta nodo, retorna id
Copy(path, parent, copyNodeData?)           // copia nodo
Update(path, updateData)                    // actualiza props (no children)
Replace(path, nodeData)                     // reemplaza nodo completo
Move(path, parent?, index?)                 // mueve nodo
Delete(path)                                // borra nodo
Generate(nodeId, "ai"|"svg"|"stock", prompt) // genera imagen/SVG (async!)
SetVariables(variables, replace?)           // define variables/theme
```

**Lectura:**
```js
Get(path, {depth})                          // lee nodo/subárbol
Get(path, visit, options)                   // visita con función
GetVariables()                              // variables actuales
FindEmptySpace({width, height, direction, padding})  // espacio libre
Print(...values)                            // output al response
TakeScreenshot(nodeIds)                     // screenshot (caro, usar con moderación)
Export(nodeIds, format, outputPath, {scale}) // exporta PNG/JPEG/WEBP/PDF/HTML
```

**Reglas críticas:**
- Todo nodo DEBE tener `name` legible
- NUNCA setear `id` al crear — pen.dev genera ids únicos
- Variables persistidas entre calls: declarar SIN `const`/`let` (`myId = Insert(...)`)
- `Insert` inserta UN nodo — añadir children con el id retornado en el siguiente Insert
- `Generate` es async: el frame queda `placeholder: true` hasta que termina. NO re-generar, verificar con `Get` en calls posteriores
- Los style objects que se hagan spread deben incluir `type`
- Cuando un `execute` falla, corregir con el parámetro `edits` + `editId` del mensaje de error
- Verificar layout con `TakeScreenshot` al terminar cada sección y corregir issues (textos sin `fill`, nodos colapsados `fit_content(0)`)

## Timing

- **Simple** (card, componente): 1-2 min
- **Medio** (app screen, sección landing): 2-3 min
- **Complejo** (landing completo, dashboard): 3-5+ min
- **SVG/IA generado**: puede tardar varios minutos adicionales en background

Avisar al usuario que la generación tomará unos minutos.

## Working Directory

Guardar diseños en el cwd del usuario o subdirectorio `designs/`. No usar temp dirs.

## Pitfalls

- `hermes mcp add pencil` FALLA con "Connection closed" — no intentarlo; el MCP vive en opencode
- El MCP pencil necesita que pen.dev/VSCodium esté corriendo
- No confundir el skill con el CLI `pen` directo (que requiere Claude Code/Codex/Gemini CLI autenticados — no disponibles)
- `--format json` genera mucho output; usar `| tail -60` o capturar a archivo
- El output del test real mostró que opencode auto-corrige issues de layout (fills faltantes, CTAs colapsados) en calls sucesivas — dejar que lo haga