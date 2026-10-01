# OpenAI-Compatible Provider Patterns

Reference for typical OpenAI-compatible provider configs in Hermes Agent.

## Structure

All OpenAI-compatible providers follow this shape in config.yaml:

```yaml
providers:
  <name>:
    base_url: <endpoint>/v1            # required - must end in /v1
    api_key_env: <ENV_VAR_NAME>        # optional - omit for no-auth/local
    models: '[model1, model2, model3]' # optional - list as quoted string
```

## Local/No-Auth Providers

Omit `api_key` and `api_key_env` entirely:

```yaml
providers:
  ollama-local:
    base_url: http://192.168.1.17:11434/v1
    models: '[phi4-mini, qwen2.5-coder:7b, llama3.2:1b]'
```

## Quick Verification

Test any OpenAI-compatible provider with curl:

```bash
# 1. List models
curl -s $BASE_URL/v1/models | python3 -m json.tool | grep '"id"' | head

# 2. Test chat completion
curl -s $BASE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \   # omit -H for no-auth providers
  -d '{
    "model": "phi4-mini",
    "messages": [{"role":"user","content":"Responde solo: OK"}],
    "stream": false
  }' | python3 -m json.tool
```

## Common OpenAI-Compatible Providers

| Provider | Base URL | Auth |
|----------|----------|------|
| Ollama (local) | `http://<host>:11434/v1` | No auth |
| OpenRouter | `https://openrouter.ai/api/v1` | API key |
| Together AI | `https://api.together.xyz/v1` | API key |
| Groq | `https://api.groq.com/openai/v1` | API key |
| DeepSeek | `https://api.deepseek.com/v1` | API key |
| DashScope | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API key |

## Setting via CLI (when file edit is blocked)

```bash
hermes config set providers.<name>.base_url "http://host:11434/v1"
hermes config set providers.<name>.models "['model1', 'model2']"
# No api_key_env needed for local providers — just don't set it
```

## Shell Escaping Quirk

When using `hermes config set providers.<name>.models "...[...]"` from bash, the double-single-quote pattern `''model''` in the resulting YAML is correct YAML for a literal single quote inside a single-quoted string. The models string value will be `['model1', 'model2']` as intended.
