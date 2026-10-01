# Civitai Orchestration MCP — Full Workflow (no-GPU image/video/audio generation)

Discovered 2026-08-23 while replacing Comfy Cloud (paid subscription wall) for a
CPU-only user. Civitai Orchestration = free-credit cloud generation MCP: images,
video, audio (TTS/music), upscale, analysis, workflows. 19 tools.

## Endpoint & auth

- URL: `https://orchestration.civitai.com/mcp` (Streamable HTTP, same as Claude Desktop)
- Docs: https://developer.civitai.com/orchestration/mcp/
- Auth: `Authorization: Bearer <CIVITAI_API_KEY>` on every request.
  Key from civitai.com/user/account.
- TWO different MCPs, don't confuse them:
  - **Site MCP** (`https://mcp.civitai.com/mcp`) — browse models/images, posts,
    comments, messaging, moderation. NO generation.
  - **Orchestration MCP** (`https://orchestration.civitai.com/mcp`) — GENERATION.
    This is the one to use for image/video/audio.

## Hermes integration (this machine, already done)

In `~/.hermes/config.yaml` under `mcp_servers:`:

```yaml
  civitai-orchestration:
    url: https://orchestration.civitai.com/mcp
    headers:
      Authorization: Bearer ${CIVITAI_API_KEY}
    timeout: 180
    connect_timeout: 60
    enabled: true
```

- Key stored in `~/.hermes/.env` as `CIVITAI_API_KEY=<key>` — NEVER the literal
  key in config.yaml (user security rule: `{env:VAR}`).
- PITFALL: user must add the key as `CIVITAI_API_KEY=...`, NOT as a raw line
  `Authorization: Bearer ...` in .env — a raw header line is not a resolvable
  env var and config references fail silently.
- Config edits via python3/sed (patch/write_file refuse ~/.hermes/config.yaml);
  backup config.yaml + .env first.

## Commands

```bash
hermes mcp list                    # shows civitai-orchestration ✓ enabled
hermes mcp test civitai-orchestration   # Connected + 19 tools discovered
hermes mcp remove comfy-cloud      # removes server + wipes OAuth tokens
```

Handshake test without a client:
```bash
curl -s -X POST https://orchestration.civitai.com/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $CIVITAI_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"t","version":"1.0"}}}'
```
Note: `tools/list` after initialize needs the `Mcp-Session-Id` header from the
initialize response — normal MCP session semantics, Hermes handles it itself.

## Generate an image (simplest path)

Call `mcp__civitai_orchestration__generate_image` with `prompt` only — engine
defaults sensibly (sdcpp). Returns:
- `[MCP resource link: uri=spine://blobs/<uuid>-0.jpg ...]`
- Direct signed URL `https://orchestration-new.civitai.com/v2/consumer/blobs/<uuid>-0.jpg?sig=...&exp=...`
  (signed URLs expire — download promptly)
- Workflow ID for tracking.

## Downloading the generated blob (CRITICAL)

The signed URL **301-redirects** to `/v2/consumer/blobs/content/<encoded>`.
Naive `curl -o` → empty 0-byte file. Working pattern:

```bash
curl -sL -o out.jpg \
  -H "Authorization: Bearer $CIVITAI_API_KEY" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" \
  -H "Accept: image/jpeg,image/*,*/*" \
  "<signed-url>"
```

- `-L` required (follows the 301 to /content/), else HTTP 301 + 0 bytes.
- Bearer header required even on the signed URL.
- User-Agent header helps (some CDN edges reject empty UA).
- Verify with `file out.jpg` → should say `JPEG image data ... 1024x1024`.
- `read_resource` on the `spine://blobs/...` URI FAILS for images ("embedded
  resource could not be decoded: image/jpeg") — use curl on the signed URL.

## Tool families (19)

- Generation: generate_image, generate_video, generate_music, text_to_speech, transcribe_audio
- Post: upscale_image, upscale_video, convert_image, extract_video_frames
- Analysis: caption_media, tag_media, rate_media (NSFW/safety), enhance_prompt, find_models
- Workflows: submit_workflow, get_workflow, list_workflows, cancel_workflow
- LLM: chat_completion (any OpenRouter model)

Most tools accept anonymous calls, but `list_workflows` and per-user state need
the token; authenticated calls are tracked for Buzz (credit) accounting.

## Skill: verify output before declaring success

After downloading, run `vision_analyze` on the local file to confirm the image
actually matches the prompt — cheap and catches silent prompt-mangling.
