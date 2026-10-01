# Server Deployment Guide

Production deployment of llama.cpp server with OpenAI-compatible API.

## Direct from Hugging Face Hub

Prefer the model repo's local-app page first:

```text
https://huggingface.co/<repo>?local-app=llama.cpp
```

If the page shows an exact snippet, copy it. If not, use one of these forms:

```bash
# Choose a quant label directly from the Hub repo
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

```bash
# Pin an exact GGUF file from the repo tree
llama-server \
    --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf \
    --hf-file Phi-3-mini-4k-instruct-q4.gguf \
    -c 4096
```

Use the file-specific form when the repo has custom naming or when you already extracted the exact filename from the tree API.

## Server Modes

### llama-server

```bash
# Basic server
./llama-server \
    -m models/llama-2-7b-chat.Q4_K_M.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    -c 4096  # Context size

# With GPU acceleration
./llama-server \
    -m models/llama-2-70b.Q4_K_M.gguf \
    -ngl 40  # Offload 40 layers to GPU
```

## Model ID Discovery

When configuring an OpenAI-compatible client (like Hermes Agent) to talk to a llama.cpp server, you need the exact **model ID** the server exposes. This varies depending on how you started the server.

### Model ID by server launch method

| Launch method | Exposed model ID | Example |
|---|---|---|
| `-hf org/model:QUANT` | `org/model:QUANT` (same as argument) | `bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0` |
| `--hf-repo org/model --hf-file file.gguf` | `file.gguf` (filename only) | `Phi-3-mini-4k-instruct-q4.gguf` |
| `-m /path/to/model.gguf` (local file) | **Full path** to `.gguf` file | `/home/user/models/model.Q4_K_M.gguf` |

### Probe the server for the real model ID

```bash
curl http://localhost:8080/v1/models
```

Look for the `"id"` field inside `"data"` array — that's the exact string the client must send in the `"model"` field of chat completion requests.

The response also includes useful metadata:
- `n_ctx` — current context size (set by `-c` flag)
- `n_ctx_train` — model's native training context
- `n_params` — parameter count
- `size` — file size in bytes

### Configuring Hermes Agent

Set the model ID in `providers.llama-cpp.models`:

```bash
# For -hf launch
hermes config set providers.llama-cpp.models "org/model:QUANT"

# For -m local file launch
hermes config set providers.llama-cpp.models "/path/to/model.gguf"
```

Always match `context_length` in Hermes to the `-c` value passed to llama-server:

```bash
hermes config set providers.llama-cpp.context_length 65536
```

## OpenAI-Compatible API

### Chat completions
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-2",
    "messages": [
      {"role": "system", "content": "You are helpful"},
      {"role": "user", "content": "Hello"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

### Streaming
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-2",
    "messages": [{"role": "user", "content": "Count to 10"}],
    "stream": true
  }'
```

## Docker Deployment

**Dockerfile**:
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y git build-essential
RUN git clone https://github.com/ggerganov/llama.cpp
WORKDIR /llama.cpp
RUN make LLAMA_CUDA=1
COPY models/ /models/
EXPOSE 8080
CMD ["./llama-server", "-m", "/models/model.gguf", "--host", "0.0.0.0", "--port", "8080"]
```

**Run**:
```bash
docker run --gpus all -p 8080:8080 llama-cpp:latest
```

## Monitoring

```bash
# Server metrics endpoint
curl http://localhost:8080/metrics

# Health check
curl http://localhost:8080/health
```

**Metrics**:
- requests_total
- tokens_generated
- prompt_tokens
- completion_tokens
- kv_cache_tokens

## Load Balancing

**NGINX**:
```nginx
upstream llama_cpp {
    server llama1:8080;
    server llama2:8080;
}

server {
    location / {
        proxy_pass http://llama_cpp;
        proxy_read_timeout 300s;
    }
}
```

## Performance Tuning

**Parallel requests**:
```bash
./llama-server \
    -m model.gguf \
    -np 4  # 4 parallel slots
```

**Continuous batching**:
```bash
./llama-server \
    -m model.gguf \
    --cont-batching  # Enable continuous batching
```

**Context caching**:
```bash
./llama-server \
    -m model.gguf \
    --cache-prompt  # Cache processed prompts
```
