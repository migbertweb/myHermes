# Pruning the OmniRoute catalog in config.yaml (2026-08-03, laptop profile)

## Resultado verificado

`config.yaml`: 1744 → **787 líneas** (−55%). `custom_providers[0].models`: **961 → 4 modelos**.
YAML validado con `yaml.safe_load`, 72 claves top-level intactas, sin referencias rotas.

## Por qué es seguro podar (el punto clave)

La lista `models:` de un custom provider (OmniRoute) es **solo el catálogo del picker**
(`hermes model`), NO una validación de qué modelos se pueden usar. Prueba empírica de la sesión:
`combo-coding` (el `model:` default del provider), `deepseek-v4-flash`, `deepseek-v4-pro`,
`deepseek-v4-flash-free`, `mimo-v2.5-free` y `nvidia/nemotron-3-super-120b-a12b:free` están
referenciados en MoA/fallback/auxiliary y **no están** en la lista `models` — funcionan igual
porque el router los resuelve internamente. Podar el catálogo no rompe nada.

## Qué mantener al podar

1. Los modelos referenciados en el resto del config (caminar el YAML excluyendo
   `custom_providers`, recolectando valores de claves `model:`, `aggregator:` y `refs:`).
2. El `model:` default del propio provider (ej. `combo-coding` — aunque no necesite estar
   en la lista, conservarlo por claridad).

Lo que se descartó en esta sesión: todos los prefijos duplicados (cada modelo aparecía 3-4
veces como `ali/x`, `alibaba/x`, `nvidia/x`, `opencode-zen/x`...), los 5 `auto/pro-*`
(`pro-chat`, `pro-coding`, `pro-fast`, `pro-reasoning`, `pro-vision`) y los 34 `auto/*` no
referenciados — solo se mantuvo `auto/best-coding` (único `auto/*` citado en MoA omni) y los
3 antigravity referenciados (`gemini-2.5-flash-thinking`, `gemini-2.5-flash-lite`,
`claude-opus-4-6-thinking-high`).

## Técnica: edición quirúrgica por rango de líneas (mejor que yaml.dump)

Reescribe SOLO el bloque objetivo — el resto del archivo queda byte a byte idéntico (sin
reformateo, sin pérdida de comentarios, sin reordenar claves). A diferencia de
`safe_load`/`yaml.dump` que reformatea todo el archivo.

```python
path = 'config.yaml'
lines = open(path).read().split('\n')
start = end = None
for i, ln in enumerate(lines):
    if ln.rstrip() == '    models:':          # header del bloque (indent exacto)
        start = i + 1
    if start is not None and end is None and i > start and ln.rstrip() == '    name: omniroute':
        end = i                               # siguiente clave sibling = fin del bloque
        break
assert start and end

keep = ['auto/best-coding', 'antigravity/gemini-2.5-flash-thinking',
        'antigravity/gemini-2.5-flash-lite', 'antigravity/claude-opus-4-6-thinking-high']
bloque = ['    models:'] + [f'      - {m}' for m in keep]
open(path, 'w').write('\n'.join(lines[:start-1] + bloque + lines[end:]))
```

Verificación post-edición:
- `python3 -c "import yaml; c=yaml.safe_load(open('config.yaml')); print(len(c))"` — parseable y claves top-level intactas.
- Walk de referencias (excluyendo `custom_providers`) para confirmar cobertura:
  las referencias con prefijo proveedor (`auto/...`, `antigravity/...`, `combo-...`) deben
  seguir existiendo en el catálogo; las sin prefijo (deepseek-v4-*, mimo-v2.5-free) no aplica.

## Artefacto `custom_providers[0]:` (clave literal)

Una clave top-level literal `custom_providers[0]:` (con `base_url`/`key_env` solos) es un
residuo de un `hermes config set custom_providers[0].<key> <val>` pasado — `hermes config
set` guarda rutas con brackets como claves string literales, no indexa listas. Inofensiva
(~3 líneas), seguro dejarla. En este archivo vivía entre `custom_providers:` (línea ~695) y
`fallback_model:` (línea ~1665).

### Por qué es seguro borrarla (verificación, no suposición)

1. **Mecanismo del bug**: `_set_nested` (`hermes_cli/config.py`) navega con `.` — separa la
   ruta en segmentos y `custom_providers[0]` se convierte en una clave literal del dict
   top-level (no navega la lista). La sintaxis correcta para indexar listas es con punto +
   índice numérico: `hermes config set custom_providers.0.base_url <url>`.
2. **Cero lectores**: el runtime solo consume `config["custom_providers"]` (lista) y
   `config["providers"]` (esquema keyed) — `get_compatible_custom_providers()` en
   `hermes_cli/config.py` nunca toca la clave literal. Confirmar con:
   `grep -rn '"custom_providers\[0\]"' ~/.hermes/hermes-agent --include='*.py' | grep -v test`
   → sin resultados = muerta, se puede eliminar sin riesgo.

## Backups

Siempre `cp config.yaml config.yaml.bak.$(date +%Y%m%d_%H%M%S)` antes de editar (la skill
`config-backup-rotation` aplica; su rotación max-3 se ejecutó también).
