# Linux Codec Limitations — DaVinci Resolve

## Overview

DaVinci Resolve Free on Linux has no H.264/H.265 decoding or encoding. The Studio version supports it only via NVIDIA CUDA hardware (NVENC/NVDEC). AAC audio is not supported on Linux at all, even in Studio.

## Supported Codecs (Free, Linux)

| Category | Supported | Unsupported |
|----------|-----------|-------------|
| Video containers | MOV, MP4 (iff codecs supported) | MKV (unreliable) |
| Video codecs | DNxHD, DNxHR, ProRes, Motion JPEG, Uncompressed, DV/DVCPRO, CineForm, DPX, EXR, TIFF sequences | H.264/AVC, H.265/HEVC, AV1 (free only), VP9 |
| Audio codecs | PCM (WAV/AIFF), FLAC, MP3 | AAC (all Linux versions), AC3/E-AC3 |

## Studio Version GPU Support Matrix (Linux)

| GPU Vendor | H.264/H.265 Decode | H.264/H.265 Encode |
|------------|-------------------|-------------------|
| NVIDIA (CUDA) | ✅ Studio only | ✅ Studio only |
| AMD (ROCm/VAAPI) | ❌ (not supported natively) | ❌ (not supported natively) |
| Intel (QSV) | ❌ (not supported natively) | ❌ (not supported natively) |

### Workarounds for AMD/Intel (Studio version only)

Free community plugins add H.264/H.265/ProRes encode support via CPU or VAAPI:

- **x264/x264/ProRes CPU encoders**: https://github.com/ekiefl/dr-h264
- **VAAPI GPU encoders** (AMD/Intel): https://github.com/ekiefl/dr-vaapi

These are plugins that expose encoders inside Resolve's Deliver page. They require the Studio version.

## Quick Reference: ffmpeg Transcoding

### First try: remux-only (no re-encode, preserves quality & size)

Some MKV/MP4 files play fine when just re-wrapped into a MOV container, especially if the internal codecs happen to be compatible but the container format is not:

```bash
# Remux: copy streams as-is, just change container
ffmpeg -i input.mkv -f mov -c copy output.mov

# From MP4
ffmpeg -i input.mp4 -f mov -c copy output.mov
```

**Note**: Only works if the video and audio codecs *inside* are already compatible (e.g., video is DNxHD/ProRes, or audio is PCM). If the video is H.264/H.265 or the audio is AAC, remux won't help — you need full transcoding (below). Check first with `ffprobe`.

### Full transcode (always works)

```bash
# Info: check what codecs your file actually uses
ffprobe input.mp4

# DNxHD (good quality, ~220 Mbps at 1080p)
ffmpeg -i input.mp4 -c:v dnxhd -profile:v dnxhr_hq -pix_fmt yuv422p \
  -c:a pcm_s16le -f mov output.mov

# DNxHR LB (lower bitrate ~36 Mbps at 1080p)
ffmpeg -i input.mp4 -c:v dnxhd -profile:v dnxhr_lb -pix_fmt yuv422p \
  -c:a pcm_s16le -f mov output.mov

# ProRes 422 HQ
ffmpeg -i input.mp4 -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le \
  -c:a pcm_s16le -f mov output.mov

# ProRes 422 LT (lower bitrate)
ffmpeg -i input.mp4 -c:v prores_ks -profile:v 1 -pix_fmt yuv422p10le \
  -c:a pcm_s16le -f mov output.mov

# Batch conversion script (place in folder with source files)
cat > batch-convert.sh << 'SCRIPT'
#!/usr/bin/env bash
# Usage: ./batch-convert.sh *.mkv
mkdir -p converted
for f in "$@"; do
  name="${f%.*}"
  ext="${f##*.}"
  echo "Converting: $f"
  ffmpeg -i "$f" -c:v dnxhd -profile:v dnxhr_hq -pix_fmt yuv422p \
    -c:a pcm_s16le -f mov "converted/${name}.mov" 2>/dev/null
done
echo "Done — files in converted/"
SCRIPT
chmod +x batch-convert.sh
```

## Sources

- ArchWiki: DaVinci Resolve
- Nobara Project Wiki: DaVinci Resolve
- Blackmagic Design forum: viewtopic.php?f=21&t=78058
- ekiefl/dr-h264 and ekiefl/dr-vaapi plugins
- CachyOS Forum: discuss.cachyos.org/t/davinci-resolve-free-no-video/9032
- Reddit r/davinciresolve: multiple threads confirming NVIDIA-only for Studio on Linux
