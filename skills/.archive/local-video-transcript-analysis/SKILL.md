---
name: local-video-transcript-analysis
description: Analyze local video files by reading existing transcript artifacts first. Covers transcript discovery, in-file fact corrections, patch verification, and summary delivery.
version: 1.0.0
author: agent-curated
platforms: [linux, macos, windows]
metadata:
  video:
    tags: [transcript, analysis, correction, local-media]
---

# Local Video Transcript Analysis

## Trigger
The user provides a local video file for analysis and has transcript-like files in the same folder.

## Workflow

1. Probe the video with ffprobe only if needed for metadata; do not transcode by default.
2. Discover transcripts before requesting media generation:
   - Find matching files by name hints: `transcripcion`, `transcript`, `transcrip`.
   - Prefer existing user-generated transcript files over generating new content.
3. If a transcript exists:
   - Read it and base all summaries on it.
   - Do not analyze raw video frames unless the user explicitly asks or the transcript is missing.
4. If the user supplies a factual correction about the transcript content:
   - Patch the transcript file in place with `patch/str.replace`, targeting the exact user-facing string.
   - Re-read the affected lines to verify only the intended change took effect.
   - Confirm the patch result to the user; do not rescan unrelated tokens.
5. Deliver the analysis in:
   - bullet/key points when asked for points,
   - concise narrative summary when asked for a summary,
   - use the user’s language for output and any edits.

## Pitfalls
- Do not fabricate analysis from video metadata alone; rely on the transcript.
- Do not regenerate or overwrite the transcript unless the user explicitly requests a new transcription.
- Do not guess model names, hardware identifiers, or other proper nouns if the transcript already specifies them; correct the transcript instead.
- Do not make broad persona or provider pricing claims from generic web search when the session model/provider is known from Hermes config; verify from authoritative sources first if needed.

## Verification
- After patching, reread the modified region.
- If `patch` reports “Could not find a match”, stop; do not retry with a different match unless the user clarifies.
