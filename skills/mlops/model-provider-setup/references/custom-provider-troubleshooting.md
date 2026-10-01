# Custom Provider Connectivity Troubleshooting

When configuring a `custom` provider in Hermes (top-level `model.provider: custom` + `model.base_url`), use this step-by-step diagnostic flow when Hermes can't reach your model server.

## Two Config Approaches

### 1. Custom provider (top-level)
Simplest — sets the model globally:
```bash
hermes config set model.provider custom
hermes config set model.base_url http://<host>:<port>/v1
hermes config set model.default <model-name>
```
Use for a single local endpoint. No named provider entry in `providers:` needed.

### 2. Named provider (providers.<name>)
Use when you have multiple endpoints and switch between them:
```yaml
# In config.yaml or via:
# hermes config set providers.<name>.base_url "..."
# hermes config set providers.<name>.models "['m1', 'm2']"
providers:
  my-local:
    base_url: http://<host>:<port>/v1
    models: '[model1, model2]'
```
Then set `model.provider: my-local` and `model.default: model1`.

Both patterns need the same endpoint to be reachable — the diagnostic flow below applies to both.

## Step-by-Step Diagnostic Workflow

### Phase 1: Verify current config
```bash
hermes config | grep -A5 -i "model"
```
Check that `provider`, `base_url`, and `default` are set as expected.

### Phase 2: Host reachability
```bash
ping -c 2 -W 3 <host>
```
- **Reachable**: IP responds. Move to port check.
- **Unreachable**: Wrong IP, subnet mismatch, host powered off, or local/remote network issue.

### Phase 3: Port connectivity
Probe the target port directly (avoids HTTP-layer timeouts that mask lower-level failures):

```bash
# Quick port test — connection refused = reachable but no service
timeout 5 bash -c 'echo > /dev/tcp/<host>/<port>' 2>&1; echo "Exit: $?"

# Alternative with nc
nc -zv <host> <port> 2>&1

# Also try curl endpoint
curl -s --max-time 5 http://<host>:<port>/v1/models
```

**Read the result:**
| Outcome | Meaning | Next step |
|---------|---------|-----------|
| `Exit: 0` (connected) | Port open, service running | Verify models list |
| `Connection refused` (Exit: 1) | Port reachable, **nothing listening** | Start the model server |
| Timeout (Exit: 124) | **Firewall blocking** or host unreachable on that port | Check ufw/firewall on target machine |
| No route to host | Wrong IP or network | Check IP and subnet |

### Phase 4: Firewall check (target machine)
On the **target machine**:
```bash
sudo ufw status verbose
sudo ufw allow <port>/tcp
sudo ufw reload
```

After opening, retry Phase 3. If it changes from timeout → refused, the firewall was the blocker.

### Phase 5: What IS running?
If the target port is refused (no service), scan for active services:
```bash
# Check common ports for model servers
for port in 11434 8080 8000 7860 8081 3000 5000; do
  timeout 2 bash -c "echo > /dev/tcp/<host>/$port" 2>/dev/null && echo "$port: OPEN" || echo "$port: closed"
done
```

Common model server ports:
| Port | Service |
|------|---------|
| 11434 | Ollama |
| 8080 | llama.cpp server, text-gen-webui default |
| 8000 | vLLM, FastAPI |
| 7860 | text-generation-webui Gradio |
| 5000 | Various Python servers |

### Phase 6: Test the live endpoint
Once a service is found on a port, verify it provides an OpenAI-compatible API:
```bash
# List available models
curl -s http://<host>:<port>/v1/models | python3 -m json.tool

# Test a chat completion
curl -s http://<host>:<port>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model-name>","messages":[{"role":"user","content":"Say OK"}],"stream":false}' | python3 -m json.tool
```

If you get a valid JSON response with `choices[0].message.content`, the endpoint works.

### Phase 7: Update Hermes config
Point Hermes to the working endpoint:
```bash
hermes config set model.base_url http://<host>:<working-port>/v1
hermes config set model.default <model-name-from-models-list>
```

## Common Pitfalls

### Missing `/v1` path suffix
Ollama's OpenAI-compatible endpoint is at `http://host:11434/v1` (not just `http://host:11434`). llama.cpp server's default path is at `/v1` as well.

### Model name mismatch
The model name you set in `model.default` must match exactly what the server returns in `/v1/models` listing. A llama.cpp server serving one model expects its CLI-provided alias or GGUF filename; Ollama expects the tag (e.g. `llama3.2:1b`, not just `llama3.2`).

### Firewall still blocking after `ufw allow`
After `sudo ufw allow <port>`, run `sudo ufw reload`. Some systems need a full reload for the rule to take effect.

### No auth vs auth-required
- Local services (Ollama, llama.cpp on LAN): no API key needed — omit `model.api_key` entirely.
- Remote/cloud OpenAI-compatible providers: set `model.api_key` or configure via `model.api_key_env`.

### Hermes model.provider vs model.base_url conflict
Setting `model.provider: custom` tells Hermes the provider is not a named one — it uses `model.base_url` and `model.default` directly. If you later set `model.provider` to a named one (e.g. `openrouter`), the `model.base_url` setting is ignored for that provider's config. Either use `custom` with top-level URL, or use a named provider block with `providers.<name>.base_url`.

### llama.cpp: model name is a file path or HF ID
When llama.cpp serves a local GGUF file (not a Hugging Face repo), the model ID returned by `/v1/models` is the **absolute file path** on disk, e.g. `/home/user/Descargas/Modelos/Llama-3.2-1B-Instruct-Q8_0.gguf`. Set this exact path as `providers.llama-cpp.models` and `model.default`. For Hugging Face shorthand (`-hf`), the ID is the repo:quant string like `bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0`.

### context_length mismatch (silent truncation)
Every Hermes provider can set a `context_length`:
```yaml
providers:
  llama-cpp:
    base_url: http://host:8080/v1
    context_length: 65536
```
This tells Hermes the max context before compression kicks in. If it's **larger** than the llama-server's `-c` value, Hermes sends prompts the server can't fully process — silent truncation or errors. If it's **much larger**, Hermes packs the system prompt → slow processing on CPU. **Always match** `context_length` in Hermes config to the `-c` value in llama-server.

---

## Performance Troubleshooting (Phase 8)

When the endpoint responds to curl but Hermes "hangs" or "doesn't respond":

### Step 1: Test with minimal prompt
```bash
time curl -s --max-time 60 http://<host>:<port>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<model-id-from-v1/models>",
    "messages": [{"role": "user", "content": "Say OK"}],
    "max_tokens": 10
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','FAIL'))"
```

- **Fast response (<5s)**: model is healthy; the issue is prompt size or context_length
- **Slow response (30s+)**: model is CPU-bound for large prompts

### Step 2: Diagnose prompt processing speed
Check the llama-server logs for lines like:
```
I slot print_timing: n_tokens = 4096, t = 174.11 s / 23.53 tokens per second
```
- **< 30 tok/s on prompt**: CPU-bound; expect 30+ seconds per 1K tokens
- Hermes sends its full system prompt (typically 3-6K tokens) on every first message
- At 20 tok/s, a 6K prompt takes **5 minutes** before generating the first token

### Step 3: Mitigations for slow CPU inference
- **Use Q4_K_M instead of Q8_0** — half the memory bandwidth, ~2x faster prompt processing
- **Set `-t` to full physical cores** (e.g. `-t 8` on a 4C/8T CPU, not `-t 4`)
- **Reduce Hermes `context_length`** in the provider config to match realistic usage (e.g. 8192-16384) — prevents Hermes from filling the context with compression artifacts that slow processing
- **Use a smaller model** (1B instead of 3B+)
- **Consider GPU offload** (`-ngl 99`) if any GPU is available
