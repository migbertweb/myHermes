# Session: Fix DaVinci Resolve on CachyOS (June 4, 2026)

## Environment
- **OS**: CachyOS (rolling, Arch-based)
- **glib version**: system 2.88.0.1, bundled 2.68.0.4
- **Resolve install**: from official `.zip`, installed to `/opt/resolve/`
- **Installed by**: user as `migbert` (not root)

## Symptoms
- Icon appears in application menu under "DaVinci Resolve"
- Clicking does nothing — no window, no error dialog
- Running from terminal shows:

```
/opt/resolve/bin/resolve: symbol lookup error: /usr/lib/libpango-1.0.so.0: undefined symbol: g_once_init_leave_pointer
```

## Root Cause

The DaVinci Resolve binary has RPATH set to `$ORIGIN/../libs/` and `$ORIGIN/../libs/Fusion/`. It bundles its own glib 2.68 in `/opt/resolve/libs/`:
```
libglib-2.0.so.0.6800.4
libgio-2.0.so.0.6800.4
libgobject-2.0.so.0.6800.4
libgmodule-2.0.so.0.6800.4
```

It does NOT bundle pango or gdk_pixbuf, so those load from the system (`/usr/lib/`). The system's pango (1.57) and gdk_pixbuf (2.44) need glib symbols from ≥2.80:
- `g_once_init_leave_pointer` → glib ≥2.80
- `g_task_set_static_name` → glib ≥2.76

But the old bundled glib (2.68) loads first via RPATH, so these symbols are undefined.

## Fix Applied

### Wrapper script: `/opt/resolve/bin/resolve-wrapper.sh`

```bash
#!/usr/bin/env bash
export LD_PRELOAD="/usr/lib/libglib-2.0.so.0:/usr/lib/libgobject-2.0.so.0:/usr/lib/libgio-2.0.so.0:/usr/lib/libgmodule-2.0.so.0"
cd /opt/resolve
exec /opt/resolve/bin/resolve "$@"
```

### Desktop file edited
`/usr/share/applications/com.blackmagicdesign.resolve.desktop`:
```diff
-Exec=/opt/resolve/bin/resolve %u
+Exec=/opt/resolve/bin/resolve-wrapper.sh %u
```

## Verification
```
$ timeout 15 /opt/resolve/bin/resolve-wrapper.sh
[timeout after 15s, exit 124]
```
Exit 124 = it ran successfully without crashing, killed by timeout.

## Commands Used in Diagnosis

```bash
# Check binary existence and type
file /opt/resolve/bin/resolve

# List installation
ls -la /opt/resolve/

# Check RPATH
readelf -d /opt/resolve/bin/resolve | grep RPATH

# Trace library loading
LD_DEBUG=libs /opt/resolve/bin/resolve 2>&1 | grep -E 'lib(glib|pango|gdk_pixbuf|gio)'

# Find missing symbols
ldd /opt/resolve/bin/resolve 2>&1 | grep "not found"

# Check library versions
ls -la /opt/resolve/libs/libglib-2.0.so*
ls -la /usr/lib/libglib-2.0.so*
ls -la /usr/lib/libpango-1.0.so*
ls -la /usr/lib/libgdk_pixbuf-2.0.so*

# Check system package ownership
pacman -Qo /usr/lib/libgdk_pixbuf-2.0.so.0
```
