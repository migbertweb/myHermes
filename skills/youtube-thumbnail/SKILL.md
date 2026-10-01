---
name: youtube-thumbnail
description: Genera thumbnails de YouTube: brief visual, composición, texto, generación con FAL.ai. Worker M3 del equipo youtube_team.
platforms: [linux]
---

# YouTube Thumbnail (M3 worker)

Esta skill la carga el **worker de thumbnails** del agente `youtube_team`.
El orquestador (deepseek-v4-flash-free) la activa cuando el usuario pide:
"hazme un thumbnail", "genera 3 opciones de portada", "dame un brief visual para la miniatura".

## Cuándo el orquestador debe activar esta skill

- **Generar thumbnail** desde cero (FAL.ai)
- **Iterar variantes** de un thumbnail existente
- **Crear brief visual** para que un diseñador humano lo ejecute
- **Análisis de CTR** de thumbnails competidores
- **A/B testing** visual (2-3 versiones para probar)

## NO usar esta skill para

- Edición del video en sí (eso es `youtube-editor` con M3)
- Copy/título del video (eso es `youtube-script` con deepseek)
- Optimización de archivo para YouTube (eso es `youtube-editor`)

## Especificaciones técnicas OBLIGATORIAS

```
- Resolución: 1280x720 px (16:9)
- Peso máximo: 2 MB
- Formato: JPG o PNG
- Safe area para texto: 1100x600 centrado (deja 90px de margen)
- Resolución mínima legible: 200x112
- Zona crítica de CTR (esquina sup-der): 423x238 (aparece en mobile sidebar)
```

## Anatomía de un thumbnail que funciona

| Elemento | Regla |
|---|---|
| **Cara humana** (si aplica) | Grande, expresión exagerada, ojo mirando al texto o al objeto clave |
| **Texto** | Máximo 4-5 palabras, fuente bold sans-serif, alto contraste, outline negro de 2-3px |
| **Contraste** | Fondo oscuro + elemento brillante, o viceversa. Nunca tonos similares |
| **Profundidad** | 3 planos: foreground (texto), midground (sujeto/objeto), background (gradiente/blur) |
| **Color pop** | 1-2 colores saturados que destaque. Amarillo + rojo, azul + naranja funcionan |
| **Branding sutil** | Logo o handle del canal en una esquina, máximo 5% del área |

## Brief visual (cuando el worker NO genera la imagen)

Cuando el orquestador pide **brief** (no imagen generada), el worker devuelve:

```markdown
## Thumbnail Brief — Video N: <título>

### Concepto visual
<1 frase describiendo la composición>

### Elementos
- **Foreground:** <texto exacto, color, posición>
- **Midground:** <sujeto/objeto, pose, expresión>
- **Background:** <color, gradiente, blur, escena>

### Paleta
- Primario: #XXXXXX
- Acento: #XXXXXX
- Texto: #FFFFFF con outline #000000

### Referencias
<URLs de thumbnails similares que funcionan en el nicho>

### Notas de producción
- <Cualquier constraint técnico o de marca>
```

## Generación con FAL.ai (FLUX 2 Klein 9B)

El worker usa `image_generate` con prompts optimizados:

```python
# Aspect ratio siempre landscape (16:9)
image_generate(
  prompt="<prompt detallado con todos los elementos del brief>",
  aspect_ratio="landscape"
)
```

**Estructura del prompt:**
```
"[sujeto principal], [expresión/acción], [ropa/estilo], 
[escena/background], [iluminación], [estilo fotográfico: 
e.g. 'professional YouTube thumbnail, high contrast, 
vibrant colors, sharp focus on subject'], 
[specific tech: '4K, dramatic lighting, slight depth of field']"
```

**Negative prompt mental (lo que NUNCA debe aparecer):**
- Texto mal renderizado o ilegible
- Múltiples caras confundidas
- Fondo que distraiga del sujeto
- Colores lavados o de bajo contraste
- Anatomía rara (manos con 6 dedos, etc.)

## Iteración

El worker SIEMPRE genera **3 variantes** en la primera pasada. El orquestador presenta las 3 al usuario, el usuario elige 1, y el worker itera sobre esa con 2-3 refinamientos antes de dar por bueno el thumbnail.

## Reporte al orquestador

```json
{
  "status": "ok | error",
  "variantes": [
    {"path": "/path/to/thumb_v1.png", "concepto": "...", "ctr_score_estimate": 7.5},
    {"path": "/path/to/thumb_v2.png", "concepto": "...", "ctr_score_estimate": 8.2},
    {"path": "/path/to/thumb_v3.png", "concepto": "...", "ctr_score_estimate": 6.9}
  ],
  "recomendacion": "v2 — mejor balance texto/imagen y contraste con feed del canal"
}
```

## Cómo invocar al worker

```
delegate_task(
  goal="<pedido: brief | generar | iterar>",
  context="<título del video, ángulo, paleta si existe, referencias>",
  role="leaf",
  toolsets=["terminal", "file", "vision", "image_gen"]
)
# Este worker DEBE ser M3 — el orquestador lo especifica en el agent
```

## Pitfalls

- **No usar aspect_ratio "square" o "portrait"** — YouTube ignora o recorta mal
- **No meter más de 5 palabras** — en mobile se vuelve borroso
- **No usar gradientes suaves en el texto** — se pierde en mobile
- **No generar con el título del video** — el título ya aparece al lado del thumbnail, redundancia mata CTR
- **No olvidar el outline negro** en el texto — sin él, desaparece en fondos claros
