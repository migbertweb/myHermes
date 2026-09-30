#!/usr/bin/env python3
"""
🌍 Briefing diario del Mundial 2026 — Ejecutado por cron (no_agent=True)
Entrega un resumen matutino a Telegram: resultados de ayer + partidos de hoy + próximos destacados.
"""

import sys, os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
from mundial import cmd_resumen

if __name__ == "__main__":
    print(cmd_resumen())
