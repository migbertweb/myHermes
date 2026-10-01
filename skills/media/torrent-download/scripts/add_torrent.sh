#!/usr/bin/env bash
set -euo pipefail

TYPE="${1:-}"
MAGNET="${2:-}"

if [[ -z "${TYPE}" || -z "${MAGNET}" ]]; then
  echo "Uso: $(basename "$0") <movies|series|music> <magnet|.torrent>"
  exit 2
fi

case "${TYPE}" in
  movies|series|music) ;;
  *)
    echo "Tipo inválido: ${TYPE}. Usa movies|series|music."
    exit 2
    ;;
esac

BASE="/home/piro/multimedia"
DEST="${BASE}/${TYPE}"

# Verificar que el destino exista
if [[ ! -d "${DEST}" ]]; then
  echo "Directorio destino no existe: ${DEST}"
  exit 3
fi

# Verificar daemon vivo
if ! transmission-remote -l >/dev/null 2>&1; then
  echo "transmission-remote no responde en el server."
  exit 4
fi

# Agregar torrent
OUT="$(transmission-remote -a "${MAGNET}" -w "${DEST}" 2>&1 || true)"

if echo "${OUT}" | grep -qi "success"; then
  echo "OK: Agregado a ${TYPE}."
else
  echo "FAIL: ${OUT}"
  exit 5
fi

# Mostrar estado reciente del agregado (el último)
echo "--- Estado actual ---"
transmission-remote -l | tail -n 8
