#!/usr/bin/env python3
import sys
import re
import argparse
import urllib.parse
import requests
from pathlib import Path
from typing import List, Tuple

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    if source_lang.lower() == target_lang.lower():
        return text
    
    # Map target language codes for MyMemory API
    lang_pair_map = {
        "es": "es",
        "pt": "pt-BR",
        "pt-br": "pt-BR",
        "en": "en"
    }
    src = lang_pair_map.get(source_lang.lower(), source_lang.lower())
    tgt = lang_pair_map.get(target_lang.lower(), target_lang.lower())
    
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={src}|{tgt}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated:
                return translated
    except Exception as e:
        print(f"Error en traducción ({source_lang}->{target_lang}): {e}", file=sys.stderr)
    return text

def parse_srt(srt_content: str) -> List[Tuple[str, str, str]]:
    """
    Retorna lista de tuplas (index, timing, text)
    """
    blocks = re.split(r'\n\s*\n', srt_content.strip())
    cues = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            idx = lines[0].strip()
            timing = lines[1].strip()
            text = "\n".join(lines[2:]).strip()
            cues.append((idx, timing, text))
        elif len(lines) == 2:
            idx = "1"
            timing = lines[0].strip()
            text = lines[1].strip()
            cues.append((idx, timing, text))
    return cues

def build_srt(cues: List[Tuple[str, str, str]]) -> str:
    out_blocks = []
    for idx, timing, text in cues:
        out_blocks.append(f"{idx}\n{timing}\n{text}")
    return "\n\n".join(out_blocks) + "\n"

def translate_srt_file(input_srt_path: str, source_lang: str = "es", target_langs: List[str] = None):
    if target_langs is None:
        target_langs = ["es", "pt", "en"]
    
    input_file = Path(input_srt_path)
    if not input_file.exists():
        print(f"Archivo no encontrado: {input_srt_path}", file=sys.stderr)
        sys.exit(1)
        
    srt_content = input_file.read_text(encoding="utf-8")
    cues = parse_srt(srt_content)
    
    base_name = input_file.stem
    if base_name.endswith((".es", ".pt", ".en")):
        base_name = base_name.rsplit('.', 1)[0]
        
    for lang in target_langs:
        out_path = input_file.parent / f"{base_name}.{lang}.srt"
        if lang.lower() == source_lang.lower():
            out_path.write_text(srt_content, encoding="utf-8")
            print(f"Guardado SRT original ({lang.upper()}): {out_path}")
            continue
            
        print(f"Traduciendo SRT a {lang.upper()}...")
        translated_cues = []
        for idx, timing, text in cues:
            t_text = translate_text(text, source_lang, lang)
            translated_cues.append((idx, timing, t_text))
            
        translated_srt = build_srt(translated_cues)
        out_path.write_text(translated_srt, encoding="utf-8")
        print(f"Guardado SRT traducido ({lang.upper()}): {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Traductor de subtítulos SRT a ES, PT-BR y EN")
    parser.add_argument("srt_file", help="Ruta al archivo SRT fuente")
    parser.add_argument("--source", "-s", default="es", help="Idioma origen (default: es)")
    parser.add_argument("--target", "-t", nargs="+", default=["es", "pt", "en"], help="Idiomas destino (default: es pt en)")
    
    args = parser.parse_args()
    translate_srt_file(args.srt_file, source_lang=args.source, target_langs=args.target)

if __name__ == "__main__":
    main()
