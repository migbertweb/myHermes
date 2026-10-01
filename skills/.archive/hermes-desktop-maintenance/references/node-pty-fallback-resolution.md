# node-pty Native Module Resolution

## Load order

Node-pty's `utils.js` (`loadNativeModule()`) checks these paths relative to the
package root, in order:

1. `build/Release/pty.node`
2. `build/Debug/pty.node`
3. `prebuilds/<platform>-<arch>/pty.node`

Fails with: `Error: Failed to load native module: pty.node, checked: build/Release, build/Debug, prebuilds/linux-x64`

## Published prebuilds per platform (node-pty v1.1.0)

| Platform     | Arch   | Prebuilt? |
|-------------|--------|-----------|
| darwin      | x64    | Yes       |
| darwin      | arm64  | Yes       |
| win32       | x64    | Yes       |
| win32       | arm64  | Yes       |
| linux       | x64    | **No**    |
| linux       | arm64  | **No**    |

## Hermes Desktop path structure (packaged)

```
release/linux-unpacked/resources/
├── app.asar                          # contains JS code
│   └── dist/node_modules/node-pty/
│       ├── lib/utils.js              # the JS that calls loadNativeModule
│       ├── lib/unixTerminal.js
│       └── package.json
└── app.asar.unpacked/                # native binaries extracted here
    └── dist/node_modules/node-pty/
        └── build/Release/pty.node    # ← what was missing
```

## Shell-state warnings (benign)

These appear on every launch on this machine and are NOT errors:

- `setopt: can't change option: monitor` — from zsh gitstatus plugin
- `gitstatus failed to initialize` — same, oh-my-zsh gitstatus
- `fs.Stats constructor is deprecated` — Electron 40 deprecation
- `dbus/object_proxy.cc: UnitExists` — Chromium sandbox on Linux
