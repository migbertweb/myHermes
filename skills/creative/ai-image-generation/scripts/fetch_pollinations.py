#!/usr/bin/env python3
"""Genera imágenes vía Pollinations.ai (gratis, sin key) y las guarda.
Uso: python3 fetch_pollinations.py [out_dir]
Personaliza IMAGES con {nombre_archivo: prompt}. Ajusta W/H según necesidad
(recuerda: el modelo flux clampa el lado largo a 1024 → 9:16 = 576x1024 máx).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

OUT_DIR = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "public/img")

BASE_PROMPT = (
    "3D tech illustration, dark navy background with cyan and purple neon glow, "
    "clean minimal composition, lots of negative space in the upper third for text overlay, "
    "high quality render, no text in image"
)

IMAGES = {
    "example-1.jpg": (
        "a friendly robot deploying colorful shipping containers into a glowing server rack, " + BASE_PROMPT
    ),
    "example-2.jpg": (
        "a giant glowing arrow going up made of infrastructure blocks, evolution concept, " + BASE_PROMPT
    ),
}

W, H = 1080, 1920
UA = "Mozilla/5.0 (X11; Linux x86_64)"


def fetch(name: str, prompt: str) -> None:
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt)
        + f"?width={W}&height={H}&model=flux&nologo=true"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = urllib.request.urlopen(req, timeout=300).read()
    out_path = os.path.join(OUT_DIR, name)
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"OK {name} {len(data)} bytes")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}
    for name, prompt in IMAGES.items():
        try:
            fetch(name, prompt)
            results[name] = "ok"
        except Exception as e:
            results[name] = f"ERROR: {e}"
    print(json.dumps(results, indent=2))
    if any(v != "ok" for v in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
