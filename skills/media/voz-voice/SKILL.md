---
name: voz-voice
description: "Prep text for TTS: strip symbols, markdown, code."
version: 1.0.0
author: Migbert + Hermes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [tts, voz, voice, clean, text-to-speech, guion]
    related_skills: [stop-slop, voz-output-friendly]
---

# Voz-voice — Texto a voz limpio

Pipeline para convertir texto escrito (guiones, transcripciones, documentos, escaletas) en texto listo para TTS: quitar TODO símbolo y carácter que el modelo de voz leería mal o tropezaría. El TTS lee literal: backticks, barras, corchetes, emojis, negritas, tablas y encabezados rompen la lectura. Este skill deja el texto plano, natural y de corrido.

## When to Use

- Pasar un guion formateado, transcripción o documento a audio (edge-tts, Kokoro, Voicebox, etc.).
- Cualquier texto con markdown, código, comandos o símbolos que vaya a ser leído en voz alta.
- Complementa a `voz-output-friendly` (ese es para respuestas del agente en chat con TTS; este es para archivos largos).

## Reglas absolutas (heredadas de voz-output-friendly)

1. **Cero barras**: `/` el TTS dice "barra diagonal". → reescribir en palabras.
2. **Cero extensiones**: `.md`, `.yaml`, `.txt` → "el archivo de configuración", "config", o sin extensión. Si importa el formato, frase aparte: "es un archivo yaml".
3. **Cero guiones bajos / snake_case**: `api_key` → "api key".
4. **Cero rutas técnicas**: `~/.hermes/profiles/` → "la carpeta de perfiles en hermes".
5. **Cero tablas**: convertir a frases o viñetas habladas.
6. **Cuidado con puntos de enumeración**: "1. primero 2. segundo" → "primero, segundo".

## Reglas de limpieza de formato

### Markdown → plano
- Encabezados `#`/`##` → eliminar (no se leen) o convertir en pausa de sección.
- `**negritas**`, `*cursivas*`, `` `código` ``, `~~tachado~~` → quitar los marcadores, conservar el texto.
- Listas `-`/`*`/`1.` → quitar el marcador, unir en frases.
- Blockquotes `>` → eliminar.
- Enlaces `[texto](url)` → conservar solo "texto".
- Imágenes `![alt](url)` → eliminar.
- Tablas `|` → reescribir como frases.

### Símbolos
- Emojis → eliminar.
- `[?]`, `[nota]`, corchetes de duda → resolver o eliminar; NUNCA dejarlos (el TTS los deletrea).
- Llaves `{}`, paréntesis técnicos → eliminar o convertir en inciso hablado ("entre paréntesis, ..." solo si aporta).
- `&` → "y". `+` → "más" (o eliminar si es decorativo). `=` → "igual" (o eliminar).
- Comillas `"..."` → eliminar; si el énfasis importa: "entre comillas, ...".
- Puntos suspensivos `...` → convertir en pausa (punto) o "punto punto punto" según contexto.
- Asteriscos sueltos `*` → eliminar.

### Código y comandos
- Bloques de código → reescribir a lectura natural: `uvicorn main:app --reload` → "el comando uvicorn main dos puntos app con reload" — mejor aún, describir: "para levantar el backend, ejecuta uvicorn con la opción reload".
- Comandos con flags (`npm run dev --port 3000`) → "npm run dev, en el puerto tres mil".
- `main.py` → "main punto py" o simplemente "main" según contexto.

### Siglas y nombres técnicos
Decidir por cómo las diría un humano:
- Se dicen como palabra: MoA ("moa"), Kanban, Docker, Linux, FastAPI ("fast api"), CachyOS ("cachi os"), Ollama.
- Se deletrean: MCP ("eme ce pe"), API ("a pi"), TTS ("te te ese"), CPU ("ce pu u"), URL ("u erre ele").
- Con contexto se resuelve mejor: si el texto ya dijo la sigla expandida, usar la sigla.

### Números
- Versiones: "V4 Flash" → "v4 flash" (o "versión 4 flash").
- Años: "2026" → "dos mil veintiséis" (el TTS de edge dice "veinte veintiséis" — si molesta, escribir el número en letras).
- Porcentajes: "15%" → "quince por ciento".
- Decimales con coma/punto: "1.500" → "mil quinientos" (o "uno coma cinco mil").
- Horas: "21:39" → "nueve y treinta y nueve de la noche" o "veintiuno treinta y nueve".

### Estructura de guion
- Los títulos de sección NO se leen: o se eliminan, o se convierten en "pausa" (doble salto de línea).
- Marcas de producción `[CORTE]`, `[MÚSICA]`, `(b-roll)` → eliminar o reemplazar por pausa.
- Paréntesis de acotación → eliminar (no son diálogo).

## Estilo hablado — reglas de stop-slop aplicadas a la voz

Este skill usa `stop-slop` como base de estilo. Sus 8 reglas core, adaptadas a texto que será leído en voz alta:

1. **Cortar relleno**: eliminar openers que carraspean ("les voy a mostrar que", "lo que quiero decir es que", "algo que quiero destacar es"), muletillas de énfasis ("realmente", "la verdad es que", "de hecho") y adverbios sueltos. Cada palabra sobrante es tiempo de audio.
2. **Romper estructuras formularias**: evitar contrastes binarios ("no es X, es Y"), listados negativos, fragmentación dramática ("nada de eso."), setups retóricos ("¿y sabes qué pasó?") y falsa agencia ("el error sugiere que...").
3. **Voz activa**: cada oración con sujeto humano haciendo algo. Sin pasivas ("la tarea fue creada" → "el perfil creó la tarea") y sin objetos inanimados con acciones humanas ("el Kanban decidió" → "el perfil decidió en el Kanban").
4. **Ser específico**: nada de declarativas vagas ("el sistema es eficiente") — nombrar la cosa concreta. Sin extremos perezosos ("siempre", "nunca", "todo").
5. **Poner al oyente en la escena**: "tú" gana a "la gente"; lo concreto gana a la abstracción. En guion de video: "tú ves", "te muestro".
6. **Variar ritmo**: mezclar longitud de oraciones; dos elementos ganan a tres; terminar párrafos distinto; sin em dashes (en voz son pausas largas raras — usar coma o punto).
7. **Confiar en el oyente**: afirmar hechos directo, sin suavizar ("tal vez", "quizás") ni justificar.
8. **Cortar quotables**: si suena a frase de cajón o eslogan, reescribir.

### Quick checks de stop-slop adaptados a voz

- ¿Adverbios? Eliminar.
- ¿Voz pasiva? Encontrar al actor y hacerlo sujeto.
- ¿Objeto inanimado con verbo humano ("el sistema detecta")? Nombrar a la persona.
- ¿Frase empieza con "aquí", "esto es", "lo que quiero"? Reestructurar.
- ¿"No es X, es Y"? Decir Y directo.
- ¿Tres oraciones seguidas del mismo largo? Partir una.
- ¿Em dash (—)? Eliminar: coma o punto.
- ¿Declarativa vaga ("las implicaciones son grandes")? Nombrar la implicación concreta.
- ¿Meta-comentario ("el resto del video...")? Eliminar, dejar que el texto fluya.

### Reglas de voz adicionales

- **Frases cortas**: máximo ~20 palabras por oración; el TTS se pierde en oraciones largas encadenadas.
- **Naturalidad**: mantener la voz del hablante; no "AI-izar" (nada de "es importante destacar").
- **Sin tecnicismos sueltos** que el TTS deletree: si un término es muy técnico y el TTS lo diría mal, describirlo en palabras.
- **Conservar entonación**: mantener `?` y `!` (dan curva de voz), pero no abusar.

## Flujo de trabajo

1. Leer el texto fuente (guion formateado, transcripción).
2. Limpiar con las reglas de arriba (puede ser con python + regex para archivos largos, o reescritura manual para textos cortos).
3. Guardar resultado como `.txt` plano en el mismo directorio del original (sufijo `_tts`).
4. Verificar: grep de símbolos residuales → debe dar 0 (ver checklist).
5. Convertir con `text_to_speech` (edge-tts default) en chunks (el TTS se corta en archivos largos; dividir por párrafos o por ~4000 caracteres).

## Checklist pre-entrega

```
¿Queda algún símbolo?          (/, |, *, #, _, `, [, ], {, }, &, emoji) → debe ser 0
¿Queda alguna extensión?       (.md, .py, .txt) → debe ser 0
¿Queda algún comando crudo?    (uvicorn, npm run, flags) → debe ser 0
¿Quedan marcas [?] o acotaciones? → debe ser 0
¿Hay oraciones >20 palabras?  → partir
¿Los números se leen bien?     → versiones/años/porcentajes revisados
```

## Pitfalls

- **edge-tts lee los números mal en español**: "2026" → "veinte veintiséis"; escribir en letras si molesta.
- **"punto" se dice literal**: `main.py` → "main punto py" es aceptable en contexto técnico, pero "config.yaml" mejor como "el archivo config".
- **El `%` no se dice**: "15%" → "quince por ciento" obligatorio.
- **Siglas de 2 letras** (API, IA, TTS) el TTS las deletrea — decidir por contexto y ser consistente en todo el documento.
- **No eliminar significado**: limpiar símbolos, no contenido. Si una marca [?] no se puede resolver, dejar la palabra sin la marca y anotar la duda aparte para el humano.
- **El punto y seguido es tu amigo**: ante la duda de cómo leería algo el TTS, partir la frase.

## Ejemplo rápido

Entrada (guion):
```
## 3. HERMES, MI AGENTE
Lo tengo configurado con DeepSeek `V4 Flash` (creo que 4 USD/mes) — bastante asequible. Usa MoA + MCPs.
```

Salida TTS-ready:
```
Lo tengo configurado con DeepSeek versión 4 flash. Creo que son cuatro dólares al mes. Bastante asequible. Usa MoA y eme ce pes.
```
