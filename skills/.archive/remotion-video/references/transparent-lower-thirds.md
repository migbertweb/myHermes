# Lower thirds transparentes (end cards) con Remotion

Patrón validado (ago 2026, laptop CachyOS, Remotion 4.0.509) para los "pies de
video" del usuario: cintillos estilo noticias de TV, transparentes, para
superponer sobre cualquier footage en el editor.

## Preferencias del usuario (validadas con 2 iteraciones de rediseño)
- SIN badge/etiqueta (un "EN ESTE VIDEO" fue rechazado explícitamente).
- SIN fondo de pantalla: solo texto + línea de acento, con `textShadow`
  multi-capa para legibilidad sobre cualquier video.
- Posición: pegada al borde inferior (paddingBottom ~72px), centrada, estilo
  cintillo de noticias (CG). Primera versión quedaba más arriba y se pidió
  bajarla.
- 10s: 300 frames @ 30fps, 1920×1080. Entrada ~1s, hold, salida ~1.5s.

## Timeline que funciona
- 0-30: título sube desde abajo (spring damping 15 / stiffness 90) + deblur
  12→0 + scale 1.05→1 — como emerge un cintillo
- 8-30: línea de acento se dibuja (scaleX spring, gradiente
  transparent→accent→accent2→transparent, glow)
- 12-27: subtítulo fade + slide (interpolate, Easing.out(quad))
- 30-255: hold (pulso sutil del glow: 1 + sin(t*2.6)*0.07)
- 255-300: salida — baja 50px + fade + blur 10 (Easing.in(quad))

## Render con alpha (único camino que funciona en este entorno)
ProRes 4444 (verificado: pix_fmt `yuva444p12le`):
```bash
bunx remotion render src/index.ts <Comp> out/X.mov \
  --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png
```
PNG sequence (universal, pix_fmt `rgba64be`):
```bash
ffmpeg -i out/X.mov -c:v png out/pngseq_X/frame_%04d.png
```
WebM: NO — ver pitfall en SKILL.md (alpha se pierde en VP8/VP9/AV1 en este entorno).

## Verificación (no saltar)
1. Alpha real: `ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt -of csv=p=0 X.mov` → debe ser `yuva444p12le`.
2. QA visual: componer frames sobre testsrc2 y revisar con visión
   (script listo: `scripts/verify-alpha-overlay.sh`):
   - frame ~8 (mitad entrada: título debe verse emergiendo/borroso, escalonado)
   - frame ~100 (hold: nítido)
   - frame ~270 (mitad salida: desvaneciéndose)
3. Si vision_analyze rechaza el PNG (400 "too large after auto-resize"):
   convertir a JPEG primero (`ffmpeg -i check.png -q:v 4 check.jpg`).

## Notas de flujo
- Tras un rediseño, borrar los formatos viejos de `out/` (mp4 con fondo, webm
  sin alpha) para no dejar entregables que confundan.
- La config del proyecto (`remotion.config.ts`) tiene
  `Config.setVideoImageFormat("jpeg")` que gana sobre el flag CLI
  `--image-format=png` — para renders con alpha quitarla temporalmente o usar
  ProRes (que internamente fuerza PNG igual).
- Componente reutilizable: `src/EndCard/EndCard.tsx` (props: `title`,
  `subtitle`, `accent`, `accent2`). Composiciones registradas en `src/Root.tsx`.
