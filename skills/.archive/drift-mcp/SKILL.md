---
name: drift-mcp
description: "Use when inspecting or editing video projects via Drift MCP."
version: 1.0.0
author: Antigravity + Migbert
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [drift, mcp, video-editing, subtitles, tts, audio]
---

# Drift MCP Video Editing & Workflow

Workflow for inspecting, editing, and automating video projects in the **Drift** video editor using its MCP tools.

## When to Use

- Inspecting active Drift timelines, tracks, clips, and media assets.
- Automating video editing (adding tracks, placing/trimming/moving clips, applying effects/transforms).
- Transcribing audio, generating/importing subtitles, and adding synchronized TTS audio tracks to Drift timelines.

## Core Drift MCP Tools

| Tool Name | Purpose |
|---|---|
| `mcp__drift__catalog` | Start point: lists toolboxes, endpoints, units, and workflow guide. |
| `mcp__drift__inspect` | State reader: `clips: true, detail: true` shows tracks, clips, asset IDs, and subtitle cues. |
| `mcp__drift__apply` | Executor: runs sequential mutation ops inside `ops: [{tool: "...", args: {...}}]`. |
| `mcp__drift__capture` | Visual verification: returns a JPEG or full-res PNG still of the canvas at playhead/timestamp. |
| `mcp__drift__toolbox` | Loads parameter schemas for specific toolboxes (`timeline`, `media`, `subtitles`, `audio`, etc.). |

---

## Key Operations & Parameter Quirks

### 1. Inspecting Timeline State
```json
{
  "name": "mcp__drift__inspect",
  "arguments": {
    "clips": true,
    "detail": true
  }
}
```
Returns track lists, clip UUIDs, duration, frame rate, asset bin catalog, and subtitle cues.

### 2. Importing Media Assets
```json
{
  "name": "mcp__drift__apply",
  "arguments": {
    "ops": [
      {
        "tool": "import_media",
        "args": {
          "paths": ["/path/to/media.mp3"]
        }
      }
    ]
  }
}
```
> **Pitfall:** `import_media` requires `paths` (an array of strings). Passing a single `path` string returns a `bad_args` error.

### 3. Adding Tracks & Placing Clips
```json
{
  "name": "mcp__drift__apply",
  "arguments": {
    "ops": [
      { "tool": "add_track", "args": { "type": "audio" } },
      { "tool": "place_clip", "args": { "asset": "<assetUUID>", "at": 0, "track": 0 } }
    ]
  }
}
```

### 4. Subtitle Management
- **Importing SRT/VTT file**:
  ```json
  { "tool": "import_subtitle_file", "args": { "path": "/path/to/subtitles.srt", "at": 0 } }
  ```
- **Updating cues directly on an existing subtitle clip**:
  ```json
  { "tool": "set_subtitle_cues", "args": { "clip": "<subtitleClipUUID>", "cues": [{ "start": 0, "end": 5.0, "text": "Hola..." }] } }
  ```

---

## Complete Pipeline: STT Transcribe + Subtitles + TTS Track Sync

When internal `generate_subtitles` in Drift is unavailable or cancelled, use this automated pipeline:

1. **Extract Audio**:
   ```bash
   ffmpeg -y -i "/path/to/video.mkv" -vn -c:a copy "/path/to/audio.m4a"
   ```

2. **Transcribe with Groq STT**:
   - Send `audio.m4a` to Groq Whisper (`whisper-large-v3-turbo`) with `response_format=verbose_json`.
   - Postprocess technical terms (Dokploy, PostgreSQL, Cloudflare R2, MinIO, CachyOS, Hyprland, etc.).

3. **Generate & Import SRT**:
   - Save clean segment cues to `.srt`.
   - Import to Drift via `import_subtitle_file`.

4. **Synthesize & Sync TTS**:
   - Generate TTS audio for each cue using `edge_tts` (e.g. `es-VE-SebastianNeural`).
   - Assemble a continuous audio track padded with silence matching cue `start` timestamps using FFmpeg.
   - Import the resulting `.m4a` file into Drift (`import_media`) and place it on an audio track (`add_track` + `place_clip`).

---

## Troubleshooting & Pitfalls

- **`import_media` `paths` schema**: Array required (`paths: ["..."]`).
- **Clip UUIDs vs Index**: Always use `clip` UUID from `inspect({clips: true})` for clip ops rather than index, as track indices shift when tracks are added/removed.
- **Async jobs**: `generate_subtitles`, `export_video`, and `package_project` return `{started: true}` immediately. Poll `inspect({detail: true})` until active is `false`.
