# Remote access — server (192.168.1.8)

## Current config

| Setting | Value |
|---------|-------|
| RPC port | 9091 |
| Authentication | Disabled |
| Whitelist | `127.0.0.1,::1,192.168.1.*` |
| Web UI | `http://192.168.1.8:9091/transmission/web/` |

## Connecting from the laptop (CachyOS)

### CLI
```bash
transmission-remote 192.168.1.8:9091 -l
```

### GTK app
Edit → Preferences → Remote → Add: host=`192.168.1.8`, port=`9091`,
no username/password.

### Web UI
`http://192.168.1.8:9091/transmission/web/`

### Phone apps
- **Transdrone** (Android): `192.168.1.8:9091`, no auth
- **Transmissionic** (iOS/Android): same

## If you need to add authentication

Set `rpc-authentication-required: true` in `settings.json`, then set
`rpc-username` and `rpc-password` (password is automatically hashed on
next daemon start — you write it in plain text, transmission hashes it).
