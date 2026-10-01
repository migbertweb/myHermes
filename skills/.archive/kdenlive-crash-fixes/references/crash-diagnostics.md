# Kdenlive protobuf crash — reference diagnostics

## Full crash output
```
:::::::::: CREATING SPLASH SCREEN SPLASH
qt.qpa.services: Failed to register with host portal QDBusError("org.freedesktop.portal.Error.Failed", "Could not register app ID: Connection already associated with an application ID")
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
E0000 00:00:1783780361.322760  207255 descriptor_database.cc:683] File already exists in database: versions.proto
F0000 00:00:1783780361.322842  207255 descriptor.cc:2531] Check failed: GeneratedDatabase()->Add(encoded_file_descriptor, size)
*** Check failure stack trace: ***
zsh: abort (core dumped)  kdenlive
```

## Library dependency diagnostics
### MLT modules linking protobuf
`libmltopencv.so` → `libprotobuf.so.35.1.0`

### frei0r plugins linking protobuf
All `.so` files in `/usr/lib/frei0r-1/` link:
- `libprotobuf.so.35.1.0`
- `libabsl_log_internal_structured_proto.so.2605.0.0`
- `libabsl_log_internal_proto.so.2605.0.0`

### Package versions at time of fix
- `kdenlive 26.04.3-1.1`
- `mlt 7.40.0-2.1`
- `opencv 5.0.0-1.1`
- `protobuf 35.1-1.1`
- `frei0r-plugins 3.2.3-2.1` → downgraded to `3.2.2-1`

## Working output after fix
```
kdenlive 26.04.3
mlt_repository_init: failed to dlopen /usr/lib/mlt-7/libmltmovit.so
  (libmovit.so.8: no se puede abrir el fichero del objeto compartido: No existe el fichero o el directorio)
mlt_repository_init: failed to dlopen /usr/lib/mlt-7/libmltrtaudio.so
  (librtaudio.so.7: no se puede abrir el fichero del objeto compartido: No existe el fichero o el directorio)
mlt_repository_init: failed to dlopen /usr/lib/mlt-7/libmltsox.so
  (libsox_ng.so.3: no se puede abrir el fichero del objeto compartido: No existe el fichero o el directorio)
Failed to open VDPAU backend libvdpau_nvidia.so: no se puede abrir el fichero del objeto compartido: No existe el fichero o el directorio
```
These dlopen warnings are harmless — missing optional modules, not crash-causing errors.

## Community references
- CachyOS Reddit fix: https://www.reddit.com/r/cachyos/comments/1upy29d/fix_kdenlive_not_launching_working/
- Arch BBS thread: https://bbs.archlinux.org/viewtopic.php?id=296777
- Previous similar issue (caffe.proto, not versions.proto): KaOS forum — opencv rebuild without protobuf fixed it
