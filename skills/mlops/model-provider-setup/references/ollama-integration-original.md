# ollama-integration (original content — absorbed into model-provider-setup)

Ollama integration skill for Hermes Agent. Covered: installation, model pulling, systemd override for remote access, config.yaml configuration, GPU acceleration (NVIDIA/AMD), common models table, and troubleshooting. Full original content at 9KB. Key patterns now in `model-provider-setup` section 2.

## Key preserved patterns
- `ollama pull`, `ollama serve`, `ollama list`
- Systemd override: OLLAMA_HOST=0.0.0.0:11434
- GPU: auto-detects NVIDIA (nvidia-container-toolkit) and AMD (ROCm)
- Config: providers.ollama.api_base
- Troubleshooting: journalctl -u ollama, ss -tlnp
