# remote-agent-connectivity (original content — absorbed into model-provider-setup)

Remote agent connectivity skill for connecting Hermes to remote Ollama instances. Covered: SSH tunnel setup, persistent tunnel systemd unit, remote provider config, network requirements, and troubleshooting (SSH test, Ollama API test, remote logs). Full original content at 6KB. Key patterns now in `model-provider-setup` section 5.

## Key preserved patterns
- `ssh -L 11434:localhost:11434 user@remote-server` for tunneling
- Systemd user service for persistent tunnel
- Config: providers.remote-ollama.api_base
- curl checks for API health
- Prefer SSH tunnel over direct exposure
