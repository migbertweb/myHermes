#!/usr/bin/env python3
import sys
import argparse
import urllib.parse
import requests
from typing import Optional
from pathlib import Path

def generate_pollinations_image(prompt: str, output_path: str, width: int = 1080, height: int = 1920, seed: Optional[int] = None, model: str = "flux"):
    """
    Genera una imagen con Pollinations.ai y la guarda en output_path.
    Soporta resoluciones 9:16 (1080x1920), 16:9 (1920x1080), seeds y modelos.
    """
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true"
    if seed is not None:
        url += f"&seed={seed}"
    
    print(f"Descargando imagen desde Pollinations: {url}")
    res = requests.get(url, timeout=60)
    if res.status_code == 200:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_bytes(res.content)
        print(f"Imagen guardada exitosamente en: {output_path}")
        return True
    else:
        print(f"Error ({res.status_code}): {res.text}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Generador de imágenes vía Pollinations.ai")
    parser.add_argument("--prompt", "-p", required=True, help="Descripción de la imagen en inglés/español")
    parser.add_argument("--output", "-o", required=True, help="Ruta de salida del archivo (png/jpg)")
    parser.add_argument("--width", type=int, default=1080, help="Ancho (default: 1080)")
    parser.add_argument("--height", type=int, default=1920, help="Alto (default: 1920 para Reels/Shorts, 1080 para 16:9)")
    parser.add_argument("--seed", type=int, default=None, help="Semilla aleatoria")
    parser.add_argument("--model", type=str, default="flux", help="Modelo (flux, turbo, etc.)")

    args = parser.parse_args()
    success = generate_pollinations_image(
        prompt=args.prompt,
        output_path=args.output,
        width=args.width,
        height=args.height,
        seed=args.seed,
        model=args.model
    )
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
