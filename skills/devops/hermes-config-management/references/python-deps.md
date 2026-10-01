# Python Dependencies for Hermes Skills on Arch/CachyOS

On Arch-based distros (CachyOS), the system Python is externally managed (PEP 668). `pip install` system-wide fails with `externally-managed-environment`.

## Solution: Use the Hermes venv

Hermes runs from its own virtualenv:

```
~/.hermes/hermes-agent/venv/bin/pip
```

So to install deps for a skill:

```bash
~/.hermes/hermes-agent/venv/bin/pip install <package>
```

## Common skill dependencies

| Skill Area | Package | Install command |
|---|---|---|
| Finance (Excel) | `openpyxl` | `~/.hermes/hermes-agent/venv/bin/pip install openpyxl` |
| Finance (PPTX) | `python-pptx` | `~/.hermes/hermes-agent/venv/bin/pip install python-pptx` |
| Meme generation | `Pillow` | Already present in venv |
| Concept diagrams | None (self-contained HTML/SVG) | — |

## Check what's installed

```bash
~/.hermes/hermes-agent/venv/bin/pip list | grep -i <package>
```

## Do NOT

- `sudo pip install` — corrupts system Python
- `pip install --break-system-packages` — breaks Arch policy
- `pip install` outside venv on Arch — won't work
