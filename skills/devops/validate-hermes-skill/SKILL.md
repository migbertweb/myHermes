---
name: validate-hermes-skill
description: Validate Hermes Agent skills (frontmatter, references, toolsets, syntax checks).
version: 1.0.0
author: Migbert
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [devops, skills, validation]
    related_skills: [skill-management, hermes-config-management]
---

# Validar Skills en Hermes Agent

Para asegurarte de que un skill de Hermes Agent está bien estructurado y funcionará correctamente, sigue estos pasos:

1.  **Verificar Frontmatter:**
    *   Comprueba que el archivo empieza con `---` y termina con `---`.
    *   Asegúrate de que existan los campos obligatorios: `name`, `description`, `version`, `author`, `license`, `platforms`.
    *   La descripción debe ser concisa (≤60 caracteres) y terminar en un punto.

2.  **Validar Referencias a Skills (`related_skills`):**
    *   Verifica que cada skill mencionado en `metadata.hermes.related_skills` existe en tu directorio de skills (`~/.hermes/skills/`).

3.  **Verificar Herramientas Requeridas:**
    *   Si el skill declara `requires_toolsets` o `requires_tools`, asegúrate de que esas herramientas estén registradas en tu configuración de Hermes.

4.  **Comprobar Sintaxis de Scripts (Python):**
    *   Si el skill contiene scripts Python en `scripts/`, ejecuta `python -m py_compile <script_name>.py` para verificar errores de sintaxis.

5.  **Verificar Archivos de Soporte:**
    *   Si el skill usa archivos en `references/`, `templates/` o `assets/`, asegúrate de que existan y que sus rutas son correctas.

6.  **Usar Herramienta de Validación (`hermes skills lint`):**
    *   Puedes ejecutar `hermes skills lint --all` para una validación automática de todos los skills en tu sistema.

**Ejemplo de uso:**

Para validar un skill llamado `my-skill`:

```bash
# 1. Crear un archivo de prueba
touch ~/.hermes/skills/my-skill/SKILL.md

# 2. Escribir contenido
cat <<EOF > ~/.hermes/skills/my-skill/SKILL.md
---
name: my-skill
description: A test skill.
version: 0.1.0
author: Test Author
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [test]
    related_skills: [another-skill]
requires_toolsets: [web]
requires_tools: [web_search]
EOF

# 3. Validar
hermes skills lint my-skill

# 4. Si hay errores, solucionarlos y repetir