---
name: inteligente-hashtags
description: Genera hashtags inteligentes desde titulos de videos.
version: 1.0.0
author: Migbert
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [devops, hashtags, generador]
    related_skills: [validate-hermes-skill]
---

# Generador Inteligente de Hashtags para Instagram Reels

Este skill genera hashtags **semánticamente relevantes** a partir de títulos de videos, usando un LLM como backend para extraer conceptos técnicos reales (no solo filtrar stop words).

## Cuando Usar
- Automatizar la creación de hashtags para lotes de videos
- Mejorar discoverability de Reels con tags técnicos reales
- Procesar títulos con naming consistente (underscores, guiones)

## Arquitectura (Backend Semántico)

### 1. Backend Principal: Ollama + Gemma 4 (31B)
- Modelo: `gemma4:31b-cloud` via Ollama (requiere conexión a ollama.com)
- Prompt optimizado: extrae conceptos técnicos + palabras clave de dominio
- Temperatura: 0.1 para determinismo
- Timeout: 10s

### 2. Tags Base del Canal (@migbertonlinux)
Siempre se incluyen estos tags base al final:
`#Linux #ArchLinux #DevOps #Terminal #OpenSource #CachyOS #Hyprland`

### 3. Fallback: Regex Estricto (si LLM falla)
- Solo sustantivos (NOUN) + nombres propios (PROPN) via Spacy/NLTK
- Lista blanca técnica: `linux, docker, kubernetes, rust, go, python, nvim, vscode, git, terraform, ansible, prometheus, grafana, kafka, redis, postgres, mysql, mongodb, nginx, traefik, cachyos, hyprland, wayland, sway, i3, bspwm, qtile, awesome, xmonad, kde, gnome, xfce, arch, debian, ubuntu, fedora, opensuse, nixos, gentoo, alpine, void, artix, manjaro, endeavour, garuda, nobara, bazzite, bluefin, aurora, ublue, silverblue, kinoite, sericea, onyx`

## Entrada (JSON)
```json
{
  "title": "Adiós_Makefiles__Por_Qué_Necesitas_Just"
}
```

### Ejemplo de Salida (con gemma4:31b-cloud)
```json
{
  "title_original": "Adiós_Makefiles__Por_Qué_Necesitas_Just",
  "hashtags": ["#Makefiles", "#BuildSystems", "#Automation", "#SoftwareEngineering", "#DevelopmentTools", "#Linux", "#ArchLinux", "#DevOps", "#Terminal", "#OpenSource", "#CachyOS", "#Hyprland"]
}
```

## Parámetros
- `max_hashtags`: Total de hashtags (base + extraídos) (default: 12)
- `backend`: `ollama-gemma4` | `regex-strict` (default: `ollama-gemma4`)
- `canal`: nombre del canal para tags base (default: `@migbertonlinux`)

## Notas de Diseño
- El LLM filtra verbos, artículos, preposiciones y palabras irrelevantes
- Solo devuelve sustantivos técnicos, nombres de herramientas, conceptos
- Tags base del canal garantizan identidad y alcance
- Fallback regex evita basura si LLM no está disponible