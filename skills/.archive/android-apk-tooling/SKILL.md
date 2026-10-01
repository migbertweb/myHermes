---
name: android-apk-tooling
category: software-development
description: "Modify, inspect, and rebuild Android APK files on Arch Linux — change version info, edit manifest entries, replace resources, and re-sign with a debug keystore."
---

# Android APK Tooling

Modify, inspect, and rebuild Android APK files on Arch Linux / CachyOS.

## Prerequisites

```bash
# From chaotic-aur
sudo pacman -S chaotic-aur/android-apktool chaotic-aur/android-sdk-build-tools --noconfirm
```

This installs:
- `apktool` — decompile/rebuild APKs
- `zipalign` — 4-byte alignment optimization
- `jarsigner` (comes with JDK, already in PATH)

## Workflow

### 1. Decompile

```bash
apktool d -f input.apk -o output_dir
```

### 2. Modify

**Version info (most common):** edit `apktool.yml`:
```yaml
versionInfo:
  versionCode: 50105        # internal number, must increment
  versionName: 5.1.5        # user-facing string
```

**Manifest changes:** edit `AndroidManifest.xml` directly (already decoded by apktool).

**Resources:** edit XML files under `res/` or replace images under `res/`.

### 3. Rebuild

```bash
apktool b output_dir -o output_unsigned.apk
```

### 4. Generate a debug keystore (one-time)

```bash
keytool -genkey -v -keystore debug.keystore -alias debug \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Debug, OU=Debug, O=Debug, L=, S=, C=US" \
  -storepass android -keypass android
```

Reuse this keystore for future APK modifications.

### 5. Sign

```bash
jarsigner -verbose -keystore debug.keystore \
  -storepass android -keypass android \
  output_unsigned.apk debug
```

### 6. Align

```bash
zipalign -v 4 output_unsigned.apk output_signed.apk
```

## Pitfalls

- **No `versionName`/`versionCode` in AndroidManifest.xml**: Modern Android builds define these in `build.gradle`. They appear in `apktool.yml` instead. Edit that file, not the manifest.
- **Debug signature**: APKs signed with a debug keystore will show a warning ("self-signed certificate") during verification. This is normal. Installation requires "Unknown sources" enabled on the device.
- **Over-install**: Can't install a debug-signed APK over a production-signed one without uninstalling first (different signatures). Uninstall the original app before installing the modified version.
- **apktool version**: 3.0.2+ required for Android 14 (API 34) compatibility.
- **Java version**: OpenJDK 21+ required. OpenJDK 26 works fine.
