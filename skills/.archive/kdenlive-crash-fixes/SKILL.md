---
name: kdenlive-crash-fixes
description: Fix Kdenlive startup crashes on Arch Linux / CachyOS — resolves protobuf descriptor conflicts (versions.proto) between frei0r-plugins and opencv when both register the same protobuf descriptors via MLT.
---

# Kdenlive — Fix protobuf descriptor crashes on Arch/CachyOS

## Symptoms
- Kdenlive shows the splash screen then immediately crashes with:
  ```
  E0000 ... descriptor_database.cc:683] File already exists in database: versions.proto
  F0000 ... descriptor.cc:2531] Check failed: GeneratedDatabase()->Add(encoded_file_descriptor, size)
  *** Check failure stack trace: ***
  ```
- The app may prompt to reset config on next launch, but resetting doesn't fix it.
- AppImage version may still work because it bundles its own library stack.

## Root Cause
MLT (the multimedia engine Kdenlive uses) loads `libmltopencv.so` which links protobuf via OpenCV. When `frei0r-plugins` ≥ 3.2.3 is also loaded (which also links protobuf), both libraries try to register the same protobuf descriptor file (`versions.proto`) into the global protobuf descriptor database. The second registration triggers a fatal `CHECK` failure → abort.

Stack trace path:
```
mlt_register → mlt_repository_init → mlt_factory_init → Mlt::Factory::init()
```

Conflicting libraries:
- `/usr/lib/mlt-7/libmltopencv.so` (links `libprotobuf.so` via OpenCV)
- `/usr/lib/frei0r-1/*.so` (links `libprotobuf.so` directly in frei0r 3.2.3+)

## Fix

### 1. Verify the conflicting libraries
```bash
for f in /usr/lib/mlt-7/*.so; do
  if ldd "$f" 2>/dev/null | grep -q protobuf; then
    echo "$(basename $f) -> $(ldd "$f" 2>/dev/null | grep protobuf | head -1)"
  fi
done
ldd /usr/lib/frei0r-1/*.so 2>/dev/null | grep protobuf
```

### 2. Downgrade frei0r-plugins to 3.2.2
```bash
# Download from Arch Archive
curl -sL --max-redirs 5 -o /tmp/frei0r-plugins-3.2.2-1-x86_64.pkg.tar.zst \
  "https://archive.archlinux.org/packages/f/frei0r-plugins/frei0r-plugins-3.2.2-1-x86_64.pkg.tar.zst"

# Install (downgrade)
sudo pacman -U /tmp/frei0r-plugins-3.2.2-1-x86_64.pkg.tar.zst
```

### 3. Pin the package so `-Syu` doesn't re-upgrade it
```bash
sudo sed -i 's/^#IgnorePkg   =$/IgnorePkg   = frei0r-plugins/' /etc/pacman.conf
```

## Verification
```bash
kdenlive --version
timeout 10 kdenlive 2>&1 | head -10
```
If it shows only harmless dlopen warnings (movit, rtaudio, sox missing) and doesn't crash with the protobuf error, the fix worked.

## When to unpin
When either:
- `frei0r-plugins` 3.2.3+ is rebuilt without protobuf linkage, OR
- MLT is updated to handle the descriptor conflict gracefully

Remove the package from `IgnorePkg` in `/etc/pacman.conf` and run `sudo pacman -Syu` to re-upgrade normally.

## Alternative approaches
- **AppImage**: Download from [kdenlive.org/download](https://kdenlive.org/en/download) — bundles its own libs, works regardless of system package state.
- **Flatpak**: 3GB+ install but fully isolated from system library conflicts.
- **Disable MLT opencv module**: Rename `libmltopencv.so` to `.so.disabled` in `/usr/lib/mlt-7/` — but this loses OpenCV-based effects in Kdenlive.

## Pitfalls
- The Arch Archive URL for 3.2.2-1 requires the correct pkgrel suffix. Do NOT use `3.2.2-2` — that version may not be available on the archive mirrors.
- The `IgnorePkg` sed depends on pacman.conf having `#IgnorePkg   =` as a commented-out line (default Arch config). Adjust whitespace/spacing to match your file.
- This fix is specific to **Arch Linux / CachyOS** with the distro-packaged `frei0r-plugins`. Other distros (Ubuntu, Fedora) have different versioning and may not have this conflict.
