#!/usr/bin/env bash
# Verifica que un render tiene canal alpha y genera frames de QA visual
# (entrada/hold/salida) compuestos sobre testsrc2 para revisarlos con visión.
# Uso: verify-alpha-overlay.sh <video.mov> [frame_hold]
#   frame_hold por defecto 100 (de 300). Entrada=8, salida=268.
set -euo pipefail

MOV="${1:?uso: verify-alpha-overlay.sh <video.mov> [frame_hold]}"
HOLD="${2:-100}"
FPS="${FPS:-30}"

echo "== stream info =="
ffprobe -v error -select_streams v:0 \
  -show_entries stream=pix_fmt,codec_name,width,height,duration -of csv=p=0 "$MOV"

echo "== QA frames (entrada/hold/salida) =="
for n in 8 "$HOLD" 268; do
  tmp=$(mktemp --suffix=.png)
  ffmpeg -v error -y -i "$MOV" -vf "select=eq(n\,$n)" -vframes 1 -c:v png "$tmp"
  out="/tmp/qa_frame_${n}.png"
  ffmpeg -v error -y -f lavfi -i "testsrc2=size=1920x1080:rate=$FPS" -i "$tmp" \
    -filter_complex "[0:v][1:v]overlay=0:0" -frames:v 1 "$out"
  rm -f "$tmp"
  echo "frame $n -> $out"
done
echo "Revisa los PNG con vision_analyze. Si da 400 (too large), convierte a JPEG:"
echo "  ffmpeg -i /tmp/qa_frame_N.png -q:v 4 /tmp/qa_frame_N.jpg"
