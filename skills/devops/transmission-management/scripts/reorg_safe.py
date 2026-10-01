#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safe Kodi-reorg harness — move → VERIFY → cleanup, per item.
Run via:  ssh serverhogar 'python3 -' < reorg_safe.py
Encodes the lessons of 2026-08-16 (Equalizer trilogy data loss):
absolute paths only, never rm -rf a source before its video is verified in the
destination, per-item progress with flush, idempotent re-runs, transmission sweep.

Fill MOVES for your reorg. old_dir is relative to BASE, file names exact from
`find ... -printf '%y %u %s %p\n'`. Art files listed in ART move with the folder;
everything else in the old folder is treated as junk and deleted AFTER the move
is verified. sudo (PASS below) is used for root-owned leftovers — set PASS to the
server piro sudo password (documented in skill; 123456 on serverhogar).
"""
import os, re, subprocess, sys

BASE = "/home/piro/multimedia/movies"   # or /home/piro/multimedia/series
PASS = "123456"

# old_dir -> (new_dir_title, [(src_file, dst_filename), ...])
MOVES = {
    # "Old.Release.Name.2026.1080p-Dual-Lat": ("Titulo (2026)", [("Old.Release.Name.2026.1080p-Dual-Lat.mkv", "Titulo (2026).mkv")]),
}

# Artwork Kodi reads (moved into the new folder as-is)
ART = ["folder.jpg", "backdrop.jpg", "landscape.jpg", "logo.png",
       "poster.jpg", "banner.jpg", "clearart.png", "fanart.jpg", "keyart.jpg"]
# Season posters keep the Kodi seasonXX-* pattern
SEASON_ART = ["season01-poster.jpg", "season02-poster.jpg", "season03-poster.jpg"]

def run(cmd, sudo=False):
    c = (["sudo", "-S", "--"] if sudo else []) + cmd
    p = subprocess.run(c, input=(PASS + "\n" if sudo else None), text=True, capture_output=True)
    return p.returncode == 0, (p.stderr or p.stdout).strip()

def rm_any(path):
    ok, _ = run(["rm", "-rf", path])
    if not ok:
        ok, err = run(["rm", "-rf", path], sudo=True)
        if not ok:
            return False, err
    return True, ""

def process(old_dir, new_title, file_moves):
    old = os.path.join(BASE, old_dir)
    if not os.path.isdir(old):
        print(f"SKIP {old_dir}: no existe (ya procesado?)", flush=True)
        return
    new = os.path.join(BASE, new_title)
    os.makedirs(new, exist_ok=True)
    try:
        for src, dst in file_moves:
            s = os.path.join(old, src)
            if not os.path.exists(s):
                print(f"FALLO {new_title}: fuente {src} no existe — NO se borra nada", flush=True)
                return
            r, err = run(["mv", s, os.path.join(new, dst)])
            if r != 0 or not os.path.exists(os.path.join(new, dst)):
                print(f"FALLO {new_title}: mv {src} -> {err} — NO se borra nada", flush=True)
                return
        # arte local Kodi
        for art in ART + SEASON_ART:
            p = os.path.join(old, art)
            if os.path.exists(p):
                run(["mv", p, os.path.join(new, art)])
        # SOLO AHORA (todo movido y verificado): basura del folder viejo
        for entry in os.listdir(old):
            rm_any(os.path.join(old, entry))
        try:
            os.rmdir(old)
        except OSError:
            run(["rm", "-rf", old], sudo=True)
        print(f"OK {old_dir} -> {new_title}", flush=True)
    except Exception as e:
        print(f"FALLO {new_title}: {e} — revisar manualmente", flush=True)

for old_dir, (new_title, fm) in MOVES.items():
    process(old_dir, new_title, fm)

# transmission sweep: quita torrents cuyo Location/Name ya no existe en disco
out = subprocess.run(["transmission-remote", "-l"], capture_output=True, text=True).stdout
ids = [int(m.group(1)) for line in out.splitlines() if (m := re.match(r"\s*(\d+)\s+", line))]
removed = []
for tid in ids:
    info = subprocess.run(["transmission-remote", "-t", str(tid), "-i"], capture_output=True, text=True).stdout
    loc = re.search(r"Location:\s+(.+)", info)
    nm = re.search(r"Name:\s+(.+)", info)
    if loc and nm and not os.path.exists(os.path.join(loc.group(1).strip(), nm.group(1).strip())):
        subprocess.run(["transmission-remote", "-t", str(tid), "--remove"], capture_output=True, text=True)
        removed.append(tid)
print("TORRENTS_REMOVIDOS:", removed)
