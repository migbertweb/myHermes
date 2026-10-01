# Evaluación de skills antes de instalar

Antes de instalar un skill que pide el usuario, correr esta evaluación. No todo lo que se pide es un skill instalo.

## Checklist

1. **¿Es un skill real?** Buscar en el repo por `SKILL.md` o `.claude/skills/*/SKILL.md`. Si no hay SKILL.md, no es un skill para Hermes.
2. **¿Es un MCP server?** Si el repo expone herramientas vía stdio/HTTP, es MCP, no skill. Usar `hermes mcp add`.
3. **¿Es una librería?** Si es JS/Python lib para processar páginas, extraer contenido, etc. → no se instala como skill. Evaluar si Hermes ya lo cubre (firecrawl para extracción web, etc.).
4. **¿Es un bundle?** Varios SKILL.md interdependientes → copiar todos, no solo el principal.
5. **¿Ya está instalado?** `hermes skills list | grep <name>` antes de copiar.

## Casos concretos

### karpathy-guidelines (multica-ai/andrej-karpathy-skills)

Repo con `skills/karpathy-guidelines/SKILL.md`. Skill real, 4 principios. Instalado: copiar a `~/.hermes/skills/` y perfiles. Verificar con `hermes skills list`.

### defuddle (kepano/defuddle)

Librería JS para extraer contenido principal como Markdown. NO es skill. Hermes ya usa `extract_backend=firecrawl` que hace lo mismo. No instalar. Si firecrawl falla, considerar MCP server de defuddle (requiere JS runtime + DOM).

### caveman-compress-mode

Ya está en `~/.hermes/skills/caveman-compress-mode`. Activar con `/ponytail lite` o `/caveman`. Para hacerlo permanente, agregar sección en `~/.hermes/SOUL.md` (backup primero).

### agent-skills (addyosmani/agent-skills)

Bundle de 25 skills de engineering en `skills/*/SKILL.md`. Instalado completo copiando todos los subdirectorios a `~/.hermes/skills/` y 6 perfiles.

### marketingskills (coreyhaines31/marketingskills)

Bundle de 50 skills de marketing en `skills/*/SKILL.md`. Instalado completo. 8 skills ya existían localmente — se actualizaron en perfiles, local mantuvo override del usuario.

### awesome-design-md (VoltAgent/awesome-design-md)

NO es skill — colección de archivos `DESIGN.md` de referencia para diseño de UI. No hay `SKILL.md` en el repo. No instalar como skill; usar copiando `DESIGN.md` al root del proyecto cuando se necesite.

### codebase-memory-mcp (DeusData/codebase-memory-mcp)

MCP server, no skill. Binario estático `codebase-memory-mcp` → `hermes mcp add codebase-memory --command ~/.local/bin/codebase-memory-mcp`. 17 tools: index_repository, search_graph, query_graph, trace_path, get_code_snippet, etc.

## Pitfall

`hermes skills list` con grep de anclas falla en la tabla con nombres cortos. Usar `grep <name>` simple o `grep -E '(^|\s)(name)(\s|│)'`.