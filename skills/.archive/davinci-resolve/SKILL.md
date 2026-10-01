---
name: davinci-resolve
category: creative
description: Install, diagnose, and fix DaVinci Resolve on Arch/CachyOS. Covers the classic glib library conflict (bundled old glib vs system glib), the Linux codec limitations (no H.264/H.265/AAC in Free version), transcoding workarounds, wrapper creation, .desktop fixes, and verification.
tags: [linux, arch, cachyos, video-editing, library-conflicts, codecs, proprietary-apps, ffmpeg]
requires: [terminal, file]
trigger: user asks about installing, running, or fixing DaVinci Resolve on a Linux system (especially Arch-based / rolling-release), or about codec/media import issues on Linux (MKV, MP4, H.264, H.265, AAC not working)
---

# DaVinci Resolve on Linux (Arch/CachyOS)

Install, diagnose, and fix DaVinci Resolve on Arch-based Linux distributions. The main challenge is **bundled old glib** (2.68) in `/opt/resolve/libs/` conflicting with **system glib** (2.80+) on rolling distros.

## Install

1. Download the official `.zip` from Blackmagic Design (DaVinci Resolve *Studio* or *Free* — Linux `.zip`, not `.run`)
2. Run the installer:
   ```
   unzip DaVinci_Resolve_*.zip
   cd DaVinci_Resolve_*_Linux
   ./DaVinci_Resolve_*_Linux.run
   ```
3. Follow the GUI installer — it installs to `/opt/resolve/`

## Diagnose Launch Failure

If Resolve appears in the application menu but does not launch:

1. **Try running from terminal**:
   ```bash
   /opt/resolve/bin/resolve 2>&1
   ```

2. **Look for symbol lookup errors** — typical pattern:
   ```
   symbol lookup error: /usr/lib/libpango-1.0.so.0: undefined symbol: g_once_init_leave_pointer
   ```
   or:
   ```
   symbol lookup error: /usr/lib/libgdk_pixbuf-2.0.so.0: undefined symbol: g_task_set_static_name
   ```

3. **Verify the RPATH** loads bundled libraries first:
   ```bash
   readelf -d /opt/resolve/bin/resolve | grep -E 'RPATH|RUNPATH'
   # Output: $ORIGIN/../libs/...
   ```

4. **Check which libs are bundled vs system**:
   ```bash
   ls /opt/resolve/libs/libglib* /opt/resolve/libs/libgio* /opt/resolve/libs/libgobject* /opt/resolve/libs/libgmodule*
   ```
   Bundled glib is typically 2.68 (`.so.0.6800.4`). System is 2.80+ on rolling distros.

5. **Trace library loading** to confirm the conflict:
   ```bash
   LD_DEBUG=libs /opt/resolve/bin/resolve 2>&1 | grep -E '(libglib|libpango|libgdk_pixbuf|libgio)'
   ```
   - `libglib-2.0.so.0` loads from `/opt/resolve/libs/` (old bundled)
   - `libpango`, `libgdk_pixbuf` load from `/usr/lib/` (not bundled)
   - Result: system libs need glib >2.80 symbols → crash

## Fix: Wrapper Script

### 1. Create the wrapper

```bash
sudo tee /opt/resolve/bin/resolve-wrapper.sh > /dev/null << 'EOF'
#!/usr/bin/env bash
# Wrapper for DaVinci Resolve on Arch/CachyOS
# Forces system glib libraries to load before bundled (old) ones
export LD_PRELOAD="/usr/lib/libglib-2.0.so.0:/usr/lib/libgobject-2.0.so.0:/usr/lib/libgio-2.0.so.0:/usr/lib/libgmodule-2.0.so.0"
cd /opt/resolve
exec /opt/resolve/bin/resolve "$@"
EOF
sudo chmod +x /opt/resolve/bin/resolve-wrapper.sh
```

All four glib-family libraries must be preloaded:
- `libglib-2.0.so.0` — core glib
- `libgobject-2.0.so.0` — GObject type system (needed by gdk_pixbuf)
- `libgio-2.0.so.0` — GIO (needed by various subsystems)
- `libgmodule-2.0.so.0` — GModule (loaded by glib itself)

### 2. Update the .desktop file

```bash
sudo sed -i 's|Exec=/opt/resolve/bin/resolve %u|Exec=/opt/resolve/bin/resolve-wrapper.sh %u|' \
  /usr/share/applications/com.blackmagicdesign.resolve.desktop
```

### 3. Verify

```bash
timeout 10 /opt/resolve/bin/resolve-wrapper.sh
# Exit code 124 = timeout = success (it ran without crashing)
```

## Linux Codec Limitations

A separate (and often confusing) issue from the glib conflict: **DaVinci Resolve Free on Linux has severely limited codec support**, which manifests as:

| Symptom | Likely cause |
|---------|-------------|
| MKV files rejected or not importable | Container not well-supported; codecs inside (H.264/H.265 + AAC) are unsupported |
| MP4 imports but only audio plays, no video | Video is H.264/H.265 (unsupported), audio is PCM/MP3 (supported) |
| MP4 imports but video plays with no audio | Video codec OK, audio is AAC (not supported on Linux — even in Studio) |
| "Media Offline" on common .mp4 files | The file uses H.264/H.265 video, which the free version cannot decode |

### Why?

Blackmagic Design does not license H.264/H.265 decoding/encoding for the **Free version on Linux**. On Windows and macOS these codecs ship with the free version because platform-wide licenses already exist.

Supported codecs **on the free Linux version** (non-exhaustive):
- **Video**: DNxHD, DNxHR, Apple ProRes, Motion JPEG, Uncompressed, DV/DVCPRO
- **Audio**: PCM (WAV/AIFF), FLAC, MP3 (sometimes)

Unsupported on **any** Linux version (Free + Studio):
- **AAC audio** — not supported at all on Linux, even in the paid Studio version

### Studio version (paid) differences

| Capability | Free | Studio (Linux) |
|-----------|------|----------------|
| H.264/H.265 *decode* | ❌ | ✅ (hardware-only, **NVIDIA CUDA only**) |
| H.264/H.265 *encode* | ❌ | ✅ (hardware-only, **NVIDIA CUDA only**) |
| AAC audio | ❌ | ❌ (not supported on Linux at all) |

**Important**: Studio H.264/H.265 decode/encode on Linux uses **NVIDIA NVENC/NVDEC** via CUDA only. AMD GPUs (ROCm/VAAPI) and Intel iGPUs (QSV) are **not supported** for H.264/H.265 in Resolve on Linux, even in the Studio version. Workarounds exist via free plugins (see references).

### Transcoding Workaround

Convert unsupported media to DNxHD or ProRes before importing. **First try the lightweight remux** (just changes the container, no re-encode — preserves quality and file size):

```bash
ffmpeg -i input.mkv -f mov -c copy output.mov
```

If that fails (the codecs inside are still H.264/H.265), fall back to full transcoding:

```bash
# Single file → DNxHD + PCM in MOV container
ffmpeg -i input.mkv -c:v dnxhd -profile:v dnxhr_hq -pix_fmt yuv422p \\
  -c:a pcm_s16le -f mov output.mov

# Single file → ProRes (wider compatibility)
ffmpeg -i input.mkv -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le \\
  -c:a pcm_s16le -f mov output.mov

# Batch convert all MKVs in a folder
mkdir -p converted
for f in *.mkv; do
  name="${f%.*}"
  ffmpeg -i "$f" -c:v dnxhd -profile:v dnxhr_hq -pix_fmt yuv422p \\
    -c:a pcm_s16le -f mov "converted/${name}.mov"
done
```

**Notes**:
- `dnxhd` produces larger files than H.264 but is edit-friendly (intra-frame)
- `dnxhr_hq` profile = ~220 Mbps at 1080p — adjust profile down (`dnxhr_sq`, `dnxhr_lb`) for smaller files
- ProRes requires `prores_ks` encoder (FFmpeg), not the Apple encoder
- Always use `.mov` container — DaVinci Resolve handles MOV better than MKV on Linux
- PCM (`pcm_s16le`) for audio avoids AAC entirely

## Verify the Fix

1. **Quick smoke test**: run `timeout 15 /opt/resolve/bin/resolve-wrapper.sh` — exit code 124 means it started successfully and was killed by timeout
2. **GUI launch**: click the icon in the application menu
3. **Full launch**: `nohup /opt/resolve/bin/resolve-wrapper.sh &`

## Additional Considerations

- **Update survial**: after pacman -Syu updates glib, the wrapper continues working — it always loads *current* system glib
- **Reinstall**: if you reinstall Resolve, re-apply steps 1-2 (the wrapper and .desktop edit)
- **Icon**: verify icon path in .desktop: `Icon=/opt/resolve/graphics/DV_Resolve.png`
- **Desktop database**: `sudo update-desktop-database` if the menu doesn't refresh

## Pitfalls

- **LD_PRELOAD with only libglib is not enough**: the bundled `libgobject` also gets loaded via RPATH and provides the old symbol table. gdk_pixbuf needs `g_task_set_static_name` from the system's gobject. Preload **all four** glib-family system libs.
- **Do not modify resolve binary**: the binary has `RPATH` baked in — you can't fix it without a wrapper.
- **Do not remove bundled libs**: other apps bundled in `/opt/resolve/` may depend on the old glib. Override via LD_PRELOAD instead.
- **Do not use `LD_LIBRARY_PATH` alone**: the binaries use RPATH, which takes priority over LD_LIBRARY_PATH. LD_PRELOAD is the right mechanism because it loads before RPATH resolution.
- **Fingerprint/sudo**: modifying files under `/opt/` and `/usr/share/applications/` requires sudo. The user may need to authenticate.

## See Also

- `references/cachyos-resolve-fix.md` — reproduction recipe from the glib fix session
- `references/linux-codec-limitations.md` — detailed codec support tables, GPU matrix, and ffmpeg batch scripts
