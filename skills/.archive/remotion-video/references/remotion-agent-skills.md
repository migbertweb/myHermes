# Remotion Agent Skills (remotion-dev/skills)

Instalados vía `npx -y skills add remotion-dev/skills` → `~/.agents/skills/remotion-*` (universal para Codex/Gemini/Kimi/OpenCode/Amp, symlink a Claude Code, Hermes Agent, Qoder, Qwen Code). Código fuente: https://github.com/remotion-dev/remotion/tree/main/packages/skills

| Skill | Para qué sirve |
|---|---|
| remotion-best-practices | El general, engloba los demás. Úsalo si dudas cuál elegir |
| remotion-create | Crear proyecto o composición nueva |
| remotion-markup | Escribir markup React de Remotion: composiciones, animaciones, layout, tipografía, media, efectos, audio, timing |
| remotion-studio | Lanzar el Studio para previsualizar |
| remotion-render | Renderizar a video o imagen estática |
| remotion-maps | Animaciones de mapas: rutas, markers, GeoJSON, Mapbox/MapLibre, flyovers 3D con CesiumJS |
| remotion-captions | Subtítulos/captions |
| remotion-saas | Arquitectura para apps/productos basados en Remotion |
| remotion-interactivity | Hacer el código editable en Studio |
| remotion-docs | Buscar en la documentación y traer páginas como Markdown antes de implementar |
| remotion-upgrade | Actualizar Remotion, paquetes compatibles y los propios skills |
| remotion-multimedia | Manejo multimedia en browser con Mediabunny (metadatos de audio/video) |

## Uso con Hermes
- Los symlinks de Hermes apuntan a `~/.agents/skills/`; aparecen en skills_list de una sesión nueva.
- Estos skills son de terceros (hub-install), no editarlos.
- Verificación del flujo tras instalar: `bunx remotion compositions` (baja Chrome Headless Shell en el primer run).
