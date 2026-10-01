---
name: multi-agent-orchestration
description: Design and management of specialized sub-agent teams coordinated by an Orchestrator (Deliberative Routing).
category: devops
---

# Multi-Agent Orchestration (Deliberative Routing)

## Description
Workflow for designing and managing teams of specialized sub-agents coordinated by a strong "Orchestrator" model. This approach optimizes cost and quality by routing tasks to the most capable/cheapest model for that specific domain.

## Architecture Pattern
- **Orchestrator (The Brain):** High-reasoning model (e.g., DeepSeek V4 Flash/Coder) responsible for planning, task decomposition, and quality control.
- **Workers (The Specialists):** Domain-specific models (e.g., M3 for video/vision, Gemma for formatting/publishing) invoked via `delegate_task`.

## Implementation Steps
1. **Agent Definition:** Create a `.yaml` file in `~/.hermes/agents/` defining the system prompt and the routing logic.
2. **Specialized Skills:** Create a set of class-level skills in `~/.hermes/skills/` that workers will load.
3. **Depth Configuration:** Ensure `delegation.max_spawn_depth` in `config.yaml` is set to at least `2` to allow the orchestrator to spawn workers.
4. **MoA Configuration:** Define presets in `moa.presets` section of `config.yaml`. Example:
   ```yaml
   moa:
     active_preset: omni
     presets:
       omni:
         reference_models:
           - model: auto/best-fast
             provider: custom
             base_url: http://localhost:20128/v1
           - model: auto/reasoning
             provider: custom
             base_url: http://localhost:20128/v1
           - model: auto/best-chat
             provider: custom
             base_url: http://localhost:20128/v1
         aggregator:
           provider: custom
           base_url: http://localhost:20128/v1
           model: auto/reasoning
         enabled: true
         reference_max_tokens: 600
   ```
5. **Activation:** Invoke via `/agent <agent_name>` or use the configured MoA preset.

## OmniRoute Integration (Gateway MoA)

When using OmniRoute as a local gateway for MoA:
- **Provider:** Use `custom` with `base_url: http://localhost:20128/v1`
- **Recommended Models:**
  - `auto/best-fast` — Latencia ~3.8s, agente ejecutor rápido
  - `auto/reasoning` — Latencia ~7s, agente de decisión
  - `auto/best-chat` — Latencia ~5s, agente conversacional
- **Benchmarking:** Test model latency before finalizing MoA preset:
  ```bash
  curl -s -X POST http://localhost:20128/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer dummy" \
    -d '{"model":"auto/best-fast","messages":[{"role":"user","content":"Hola"}],"max_tokens":15}' \
    -w "⏱️ %{time_total}s\n" -o /dev/null
  ```
- **Latencia medida (2026-08-01):**
  - `auto/best-fast`: p50 ~3.8s (rango 2.8-4.8s)
  - `auto/reasoning`: p50 ~7s (rango 1.3-7.2s)
  - `auto/best-free`: >30s (inestable, no recomendado)
  - `auto/coding`: >45s (timeout, no recomendado)

## Pitfalls & Constraints
- **Config Protection:** El agente no puede modificar `config.yaml` directamente via `patch` o `write_file`. Usar `hermes config set <key> <value>` o editar manualmente.
- **Gateway Restarts:** El agente no puede reiniciar el servicio `hermes-gateway` desde su propio proceso (se autodestruiría). Pedir al usuario ejecutar `hermes gateway restart`.
- **Context Propagation:** Los sub-agentes no tienen acceso a la conversación padre. Pasar todo estado, rutas de archivos y restricciones explícitamente en el campo `context` de `delegate_task`.
- **YAML Comment Loss:** `yaml.dump` no preserva comentarios. Evitar reescrituras de archivo completo si hay documentación crítica.

## Verification
- Run `hermes config check` to verify delegation depth.
- Run `python3 -c "import yaml; yaml.safe_load(open('~/.hermes/config.yaml'))" to verify MoA config syntax.
- Test worker hand-off with a simple prompt targeting a specific worker's skill.
