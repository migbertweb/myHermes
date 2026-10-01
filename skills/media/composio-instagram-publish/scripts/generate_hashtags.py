#!/usr/bin/env python3
"""
Genera hashtags inteligentes para Instagram Reels usando Ollama.
Integración directa con el skill inteligente-hashtags.
"""
import json
import sys
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b"  # local, rápido
# MODEL = "gemma4:31b-cloud"  # premium, mejor semántico

# Tags base del canal @migbertonlinux
BASE_TAGS = ["#Linux", "#ArchLinux", "#DevOps", "#Terminal", "#OpenSource", "#CachyOS", "#Hyprland"]

def generate_hashtags(title: str, max_tags: int = 5) -> list:
    """Genera hashtags semánticos desde un título usando Ollama."""
    prompt = f"Extract {max_tags} technical keywords from this title for Instagram hashtags. Output ONLY the words, comma-separated, no other text:\n\n{title}"
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=15)
        resp.raise_for_status()
        keywords = resp.json().get("response", "").strip()
        # Parse comma-separated keywords
        tags = [f"#{k.strip().capitalize()}" for k in keywords.split(",") if k.strip()]
        return tags[:max_tags]
    except Exception as e:
        print(f"Error Ollama: {e}, usando fallback regex...", file=sys.stderr)
        return fallback_hashtags(title, max_tags)

def fallback_hashtags(title: str, max_tags: int) -> list:
    """Fallback regex estricto: solo sustantivos técnicos."""
    import re
    stop_words = {'el','la','un','una','y','en','de','por','para','con','los','las','su','mi','tu','nuestro'}
    clean = re.sub(r'[_\-]+', ' ', title.lower())
    words = [w for w in clean.split() if w not in stop_words and len(w) >= 3]
    tech_whitelist = {'linux','docker','kubernetes','rust','go','python','nvim','vscode','git','terraform','ansible','prometheus','grafana','kafka','redis','postgres','mysql','mongodb','nginx','traefik','cachyos','hyprland','wayland','sway','i3','qtile','awesome','xmonad','kde','gnome','xfce','arch','debian','ubuntu','fedora','opensuse','nixos','gentoo','alpine','void','artix','manjaro','endeavour','garuda','nobara','bazzite','bluefin','aurora','ublue','silverblue','kinoite','sericea','onyx','makefiles','buildsystems','automation','valgrind','debugging','memory','lazygit','git','history','fzf','menus','interactive','terminal','replaces','programming','dokploy','coolify','produccion','triage','server','downtime'}
    tags = [f"#{w.capitalize()}" for w in words if w in tech_whitelist]
    return tags[:max_tags]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_hashtags.py \"Título del video\"")
        sys.exit(1)
    
    title = sys.argv[1]
    semantic_tags = generate_hashtags(title)
    all_tags = semantic_tags + BASE_TAGS
    print(json.dumps({"title": title, "hashtags": all_tags}, ensure_ascii=False))