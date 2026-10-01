#!/usr/bin/env bash
# Post-download reorg (variant: accepts .mkv OR .mp4): waits for a transmission
# torrent to finish, then moves its video file into KODI convention
# (Title (Year)/Title (Year).ext), cleans release junk, removes the torrent
# from the list, and verifies with ffprobe.
#
# Use this variant when the release extension is unknown or known to be .mp4 —
# the original post_download_reorg.sh only finds *.mkv and fails on mp4
# releases (Hackstore Dual-Lat saga releases are frequently .mp4).
#
# Run ON the media server (survives SSH session drop):
#   rsync -av post_download_reorg_mp4.sh serverhogar:/tmp/
#   ssh serverhogar 'setsid nohup bash /tmp/post_download_reorg_mp4.sh <ID> <SRC_DIR> "<FINAL_DIR>" "<FINAL_FILE>" > /tmp/reorg<ID>.log 2>&1 < /dev/null &'
# Poll progress with: ssh serverhogar 'tail /tmp/reorg<ID>.log'
#
# Args:
#   1: torrent ID (from transmission-remote -l)
#   2: SRC_DIR   — release folder where the torrent wrote files
#   3: FINAL_DIR — KODI folder, e.g. '/home/piro/multimedia/movies/Misión Imposible/Misión: Imposible (1996)'
#   4: FINAL_FILE — exact filename, e.g. 'Misión: Imposible (1996).mp4'
#   5: MAX_WAIT_MIN — optional, default 120
set -euo pipefail
ID="${1:?torrent id}"
SRC_DIR="${2:?source dir}"
FINAL_DIR="${3:?final KODI dir}"
FINAL_FILE="${4:?final filename}"
MAX_WAIT_MIN="${5:-120}"

echo "[$(date)] Esperando descarga del torrent $ID (max ${MAX_WAIT_MIN} min)..."
for i in $(seq 1 $((MAX_WAIT_MIN * 2))); do
  st=$(transmission-remote -t "$ID" -i 2>/dev/null || true)
  pct=$(echo "$st" | grep 'Percent Done' | grep -oE '[0-9.]+%' || echo '?')
  state=$(echo "$st" | grep 'State:' | cut -d: -f2 | tr -d ' ')
  echo "[$(date)] state=$state pct=$pct"
  if [[ "$pct" == "100%" ]] || echo "$state" | grep -qiE 'seeding|finished'; then
    break
  fi
  sleep 30
done

pct=$(transmission-remote -t "$ID" -i | grep 'Percent Done' | grep -oE '[0-9.]+%' || echo '?')
[[ "$pct" == "100%" ]] || { echo "NO TERMINÓ en ${MAX_WAIT_MIN} min"; exit 3; }

VIDEO=$(find "$SRC_DIR" -maxdepth 2 \( -name '*.mkv' -o -name '*.mp4' \) | head -1)
[[ -n "$VIDEO" ]] || { echo "ERROR: no se encontró .mkv/.mp4 en $SRC_DIR"; exit 4; }
echo "[$(date)] Archivo fuente: $VIDEO"

mkdir -p "$FINAL_DIR"
if [[ -f "$FINAL_DIR/$FINAL_FILE" ]]; then
  echo "Destino ya existe, saliendo"; exit 0
fi
mv -v "$VIDEO" "$FINAL_DIR/$FINAL_FILE"
# safe-delete rule: verificar destino ANTES de tocar la fuente
[[ -f "$FINAL_DIR/$FINAL_FILE" ]] || { echo "ERROR: destino no existe tras mover"; exit 5; }

# limpiar basura del release (solo tras verificar destino)
rm -rf "$SRC_DIR/.pad" 2>/dev/null || true
rm -f "$SRC_DIR"/*.url "$SRC_DIR"/*.vbs 2>/dev/null || true
rmdir "$SRC_DIR" 2>/dev/null || true

# quitar torrent de la lista (datos ya movidos)
transmission-remote -t "$ID" --remove >/dev/null 2>&1 || true

echo "[$(date)] VERIFICACION:"
ls -lh "$FINAL_DIR"
ffprobe -v error -show_entries format=filename,duration,size -of default=noprint_wrappers=1 "$FINAL_DIR/$FINAL_FILE" 2>/dev/null || stat -c '%n %s bytes' "$FINAL_DIR/$FINAL_FILE"
echo "OK: $FINAL_DIR/$FINAL_FILE"
