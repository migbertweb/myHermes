---
name: davinci-resolve-arch-fix
description: Fix DaVinci Resolve launch issues on Arch Linux / CachyOS — resolves glib symbol lookup errors (g_once_init_leave_pointer, g_task_set_static_name) caused by bundled old glib (2.68) conflicting with system glib (2.88+).
---

# DaVinci Resolve — Fix glib symbol lookup errors on Arch/CachyOS

## Symptoms
- `.desktop` entries present, app icon shows in menu
- DaVinci Resolve doesn't launch when clicked
- Running `/opt/resolve/bin/resolve` gives:
  ```
  symbol lookup error: /usr/lib/libpango-1.0.so.0: undefined symbol: g_once_init_leave_pointer
  ```
  or:
  ```
  symbol lookup error: /usr/lib/libgdk_pixbuf-2.0.so.0: undefined symbol: g_task_set_static_name
  ```

## Root Cause
DaVinci Resolve bundles its own glib (version **2.68**) in `/opt/resolve/libs/`. The binary's RPATH loads these bundled libs first. System libraries (`libpango`, `libgdk_pixbuf`) are loaded from the system and require glib ≥ 2.80+, but the old bundled glib is already loaded → missing symbol crash.

Bundled glib files: `libglib-2.0.so.0.6800.4`, `libgobject-2.0.so.0.6800.4`, `libgio-2.0.so.0.6800.4`, `libgmodule-2.0.so.0.6800.4`

## Fix

### 1. Create the wrapper script

```bash
sudo tee /opt/resolve/bin/resolve-wrapper.sh > /dev/null << 'WRAPPER'
#!/usr/bin/env bash
# Wrapper for DaVinci Resolve on Arch/CachyOS
# Forces system glib libraries instead of bundled old ones
export LD_PRELOAD="/usr/lib/libglib-2.0.so.0:/usr/lib/libgobject-2.0.so.0:/usr/lib/libgio-2.0.so.0:/usr/lib/libgmodule-2.0.so.0"
cd /opt/resolve
exec /opt/resolve/bin/resolve "$@"
WRAPPER
sudo chmod +x /opt/resolve/bin/resolve-wrapper.sh
```

### 2. Update the .desktop file

```bash
sudo sed -i 's|Exec=/opt/resolve/bin/resolve %u|Exec=/opt/resolve/bin/resolve-wrapper.sh %u|' \
  /usr/share/applications/com.blackmagicdesign.resolve.desktop
```

### 3. Refresh desktop database (optional)

```bash
sudo update-desktop-database
```

## Verification
Run the wrapper:
```bash
/opt/resolve/bin/resolve-wrapper.sh
```
The app should open normally. A timeout (exit code 124) after 10+ seconds means it started successfully.

## Notes
- Works on CachyOS and any Arch-based distribution
- The 4 preloaded libraries (`libglib-2.0`, `libgobject-2.0`, `libgio-2.0`, `libgmodule-2.0`) override the bundled versions via `LD_PRELOAD`
- If DaVinci Resolve is reinstalled, the wrapper is preserved (it's in the install directory), but the `.desktop` file may need updating again if the installer resets it
