---
name: agent-skills-creator
description: Crea y mejora skills portable AGENT.
version: 1.0.0
author: mblode
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [devops, skills, creator]
    related_skills: [validate-hermes-skill]
---

# Agent Skills Creator

Crea y mejora skills portable AGENT.

## Modos
- New skill → Workflow de creación
- Audit/improve → references/improving-existing-skills.md
- Simplify/collection → same ref + capability-delta.md

### Workflow
1. Elegir patrón
2. Crear directorio y frontmatter
3. Escribir SKILL.md body
4. Añadir references
5. Validar con validate.sh
6. Actualizar README
7. Smoke-test
8. Evalúa e itera

### Referencias
- references/skill-patterns.md
- references/format-specification.md
- references/rules-folder-structure.md
- references/evaluation-and-iteration.md

### Gotchas
- No usar /tmp para instalación persistente
- Nombres vagos (helper, utils)
- Sin testing across tiers
- Descripciones sin "Use when"