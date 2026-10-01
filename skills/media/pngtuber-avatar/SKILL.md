---
name: pngtuber-avatar
description: "Avatares PNGTuber: generar, cortar, keying, Veadotube y OBS."
---

# PNGTuber Avatar (Veadotube Mini + OBS)

Flujo completo para crear un avatar que "habla" (PNGTuber): personaje con 2+ imágenes (boca cerrada/abierta), el programa alterna capas según el volumen del micrófono.

## Concepto
- **PNGTuber** = capas PNG + audio-reactivo (alterna boca abierta/cerrada con el volumen del mic).
- **Veadotube Mini** (gratis, itch.io): el programa de este flujo. Alternativa: PNGTuber Mini.
- Niveles superiores: **Live2D** (VTube Studio + webcam) y **3D** (VRoid + VSeeFace) — mueven cabeza/cejas de verdad.

## Flujo
1. **Generar avatar**: ideal = grid 2x2 con 4 variantes del MISMO personaje (2 boca cerrada, 2 boca abierta, poses distintas) sobre fondo blanco puro. ChatGPT Image lo hace muy bien; FLUX con FAL también.
2. **Cortar + keying**: `python3 scripts/cortar_avatares.py <grid.png> <outdir>` → 4 PNG con alpha (flood-fill desde bordes + feather; preserva blanco interno como camiseta/dientes).
3. **Veadotube Mini**: arrastrar imágenes a la ventana, asignar en slots boca **Closed** y **Open**, ajustar sensibilidad del audio hasta que abra con la voz y cierre en silencio.
4. **OBS**: fuente → captura; filtro Chroma Key; el mic del stream es el mic normal de OBS (el audio de Veadotube SOLO anima — no mezclarlo o se acopla).

## OBS en Linux/Wayland (Hyprland)
- **Game Capture NO existe en Linux** (es exclusivo de Windows) — no es un plugin que falte.
- Vía correcta: **+ → Captura de pantalla (PipeWire)** → en el diálogo del portal elegir **la ventana de Veadotube** (xdg-desktop-portal-hyprland permite ventana individual) → filtro **Chroma Key**.
- Veadotube: activar fondo chroma verde (toggle cámara/webcam) o dejar fondo blanco y cromar blanco — cualquiera de los dos.
- Chroma Key: cuentagotas sobre el fondo, Similitud ~400, Suavizado ~80, Reducción de contraste ~100.
- Si la ventana (Wine) no aparece en el selector del portal: captura de pantalla completa + recorte manual, o correr OBS en X11: `QT_QPA_PLATFORM=xcb obs`.

## Pitfalls
- **FAL_KEY expirada/inválida** → `{"detail":"invalid key credentials"}` HTTP 401. Test: `curl -s -X POST https://fal.run/fal-ai/flux/schnell -H "Authorization: Key $KEY" -H "Content-Type: application/json" -d '{"prompt":"test"}'`. Keys FAL = UUID (~36 chars); una key de ~69 chars es sospechosa (de otro servicio o corrupta). Renovar en fal.ai/dashboard.
- **Pollinations img2img** (gratis, sin key) es DÉBIL para edición fiel: cambia el personaje (gafas redondas, ropa, estilo) aunque uses `imageStrength` bajo. No sirve para variar boca de una imagen existente. text-to-image con `seed` fijo sirve para consistencia entre variantes generadas de cero.
- **Hosts de subida temporal**: catbox.moe a veces devuelve vacío; 0x0.st caído (spam de bots); usar **litterbox.catbox.moe** (`-F "time=24h"`) o **tmpfiles.org**.
- Pollinations `model=flux-pro` sin auth → devuelve silenciosamente lo mismo que `flux`.
- Warning `RuntimeWarning: invalid value encountered in sqrt` del script (overflow int16 en píxeles oscuros): cosmético, no afecta el resultado.

## Verificación
- El script genera `verificacion_alpha.png` (collage sobre damero) — revisarlo con visión: personaje completo, bordes limpios, camiseta blanca opaca.
- Prueba final: hablar → boca abre; callar → cierra; grabar 10s → audio limpio sin eco.
