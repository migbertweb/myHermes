# Obsidian note skeletons — freelance proposal archive

Folder: `<vault>/Freelancer/99frelas/propostas/<post title>/`
Reference example: "SaaS BenchIA para análise de atendimento ao cliente" (2026-08-02).

## 1. Index — `<post title>.md`

```markdown
---
tags: [freelance, propuesta, <platform>, saas, ia]
estado: propuesta-preparada
cliente: <client>
fecha: YYYY-MM-DD
fuente: /home/migbert/proyectos/Freelancer/99frelas/propostas/<post title>
---

# <Post title>

<One-line summary of the SaaS/project + post date>.

## Notas

- [[<Short>-Proyecto]] — descripción, template y análisis de ejecución
- [[<Short>-Propuesta]] — propuesta lista para colar

## Recursos

- Logo: [[Recursos/<descriptive-name>.jpg]]
- Template: [[Recursos/<descriptive-name>.png]]

## Estado

- [x] Análisis de ejecución
- [x] Propuesta (<n> caracteres)
- [ ] Enviar propuesta
- [ ] Call de alineamiento (20 min)

## Pendências con el cliente

1. <pregunta 1>
2. <pregunta 2>
3. <pregunta 3>
```

## 2. `<Short>-Proyecto.md`

```markdown
---
tags: [freelance, <project-type>, analise]
estado: analisado
fecha: YYYY-MM-DD
---

# <Short> — Proyecto y Análisis de Ejecución

[[<post title>|← Índice]] · [[<Short>-Propuesta|Propuesta →]]

## Descripción del proyecto (post original)
<Restate the job post requirements compactly>.

## Template (anexo analizado)
<Description from vision_analyze: layout, KPIs, gráficos, colores, marca.>

## Análisis de ejecución
**Veredicto:** <viable; duración; horas estimadas; riesgo técnico principal>.

### Alcance por módulo
| Módulo | Entregable |
|---|---|
| ... | ... |

### Arquitectura
```text
ASCII diagram: client ⇄ API ⇄ DB/workers ⇄ IA ⇄ payments
```

### Stack (opinado)
| Capa | Elección | Por qué |
|---|---|---|
| ... | ... | ... |

### Decisiones clave
1. <decisión + justificación>

### Fases y precio
| Fase | Contenido | Duración |
|---|---|---|
| F1 | ... | ... |

| Opción | Escopo | Precio |
|---|---|---|
| MVP | ... | R$ ... |
| Completo | ... | R$ ... |

### Riesgos
| Riesgo | Mitigación |
|---|---|
| ... | ... |

### Preguntas abiertas al cliente
1. <...>
```

## 3. `<Short>-Propuesta.md`

```markdown
---
tags: [freelance, propuesta, pt-br]
estado: lista-para-enviar
fecha: YYYY-MM-DD
caracteres: <n>
---

# <Short> — Propuesta PT-BR

[[<post title>|← Índice]] · [[<Short>-Proyecto|Proyecto →]]

> Copiar y pegar tal cual. Límite Upwork: 300–500 palabras.

---

<PROPOSAL BODY — PT-BR:
hook que cita un detalle del post → entendimiento del problema →
bullets de entregables → cronograma → experiencia → precio R$ →
3 preguntas de cierre → CTA call de 20 min>

---

## Follow-up (48h sin respuesta)

> <Mensaje corto recordando el proyecto + las 3 preguntas + disponibilidad.>
```
