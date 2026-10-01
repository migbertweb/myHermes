#!/usr/bin/env python3
"""
Descargador de playlists de YouTube (audio MP3) usando yt-dlp.

Lee config.json con la lista de playlists y descarga cada una en su
carpeta destino, dentro del directorio del script.

Uso:
    python3 descargar_playlists.py                 # descarga todas
    python3 descargar_playlists.py --nombre "mix"  # solo las que coincidan
    python3 descargar_playlists.py --lista         # solo muestra la config

Requisitos:
    - yt-dlp instalado (which yt-dlp)
    - ffmpeg/ffprobe instalados (para extraer audio MP3)
    - cookies.txt opcional en la misma carpeta (para playlists privadas/
      restringidas por edad). Se obtiene con la extension "Get cookies.txt"
      de Chrome/Firefox estando logueado en YouTube.
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
COOKIES_FILE = BASE_DIR / "cookies.txt"
LOGS_DIR = BASE_DIR / "logs"
ARCHIVE_FILE = BASE_DIR / ".archive.txt"  # evita re-descargar lo ya bajado


def setup_logging() -> Path:
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / f"descarga_{datetime.now():%Y-%m-%d_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_file


def check_dependencies() -> None:
    for tool in ("yt-dlp", "ffmpeg"):
        if shutil.which(tool) is None:
            logging.error("Falta %s. Instalalo con: sudo pacman -S %s", tool, tool)
            sys.exit(1)


def load_config() -> list[dict]:
    if not CONFIG_FILE.exists():
        logging.error("No existe %s", CONFIG_FILE)
        sys.exit(1)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_command(playlist: dict) -> list[str]:
    dest = (BASE_DIR / playlist["carpeta_destino"]).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--newline",
        "--ignore-errors",                      # sigue si un video falla
        "--no-overwrites",                      # no re-bajar existentes
        "--download-archive", str(ARCHIVE_FILE),
        "-f", "bestaudio/best",                 # mejor audio disponible
        "-x",                                   # extraer audio
        "--audio-format", "mp3",
        "--audio-quality", "0",                 # VBR mas alta
        "--embed-metadata",                     # tags id3 desde youtube
        "--embed-thumbnail",
        "--add-metadata",
        "-o", str(dest / "%(playlist_index)03d - %(title)s.%(ext)s"),
    ]

    if COOKIES_FILE.exists():
        cmd += ["--cookies", str(COOKIES_FILE)]

    if playlist.get("max_canciones"):
        cmd += ["--playlist-items", f"1:{playlist['max_canciones']}"]

    cmd.append(playlist["playlist_url"])
    return cmd


def run_playlist(playlist: dict) -> int:
    nombre = playlist["nombre"]
    logging.info("=" * 60)
    logging.info("🎵 Descargando: %s", nombre)
    logging.info("=" * 60)
    cmd = build_command(playlist)
    logging.info("Comando: %s", " ".join(cmd))
    t0 = time.time()
    proc = subprocess.run(cmd)
    dt = time.time() - t0
    if proc.returncode == 0:
        logging.info("✅ %s terminada en %.1f min", nombre, dt / 60)
    else:
        logging.warning("⚠️  %s terminó con código %d (%.1f min)", nombre, proc.returncode, dt / 60)
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga playlists de YouTube a MP3")
    parser.add_argument("--nombre", help="Filtra playlists por substring del nombre")
    parser.add_argument("--lista", action="store_true", help="Solo muestra la config y sale")
    args = parser.parse_args()

    log_file = setup_logging()
    check_dependencies()
    playlists = load_config()

    if args.lista:
        for p in playlists:
            print(f"{p['prioridad']:>2}. {p['nombre']}  ({p['max_canciones']} items)  → {p['carpeta_destino']}")
        return

    if args.nombre:
        playlists = [p for p in playlists if args.nombre.lower() in p["nombre"].lower()]
        if not playlists:
            logging.error("Ninguna playlist coincide con '%s'", args.nombre)
            sys.exit(1)

    playlists.sort(key=lambda p: p.get("prioridad", 99))
    logging.info("🗂  Log: %s", log_file)
    logging.info("Iniciando %d playlist(s)…", len(playlists))

    fallos = 0
    for playlist in playlists:
        if run_playlist(playlist) != 0:
            fallos += 1

    logging.info("=" * 60)
    logging.info("Resumen: %d playlist(s), %d con errores.", len(playlists), fallos)
    if fallos:
        sys.exit(1)


if __name__ == "__main__":
    main()
