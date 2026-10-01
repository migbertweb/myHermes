# Contributing

Thanks for improving Mnemosyne Dashboard.

## Local development

Use Python 3.11+ and Node 20+ for the JavaScript syntax check.

```bash
python -m pip install --upgrade pytest ruff
python -m ruff check .
python -m pytest -q
python -m compileall -q .
node --check static/app.js
```

## Safety invariants

Please keep these invariants unless a change explicitly documents and tests a different security model:

- The dashboard binds to `0.0.0.0` by default for easy LAN access.
- SQLite is opened through a read-only URI (`mode=ro`).
- Memory admin/editing is disabled by default; LAN/non-local admin mode must stay password-gated.
- Static assets are served only from `static/`.
- External JavaScript/CSS/CDN dependencies are avoided.
- LAN exposure is the default and should be documented with auth/firewall guidance.

## Pull request checklist

- [ ] Ruff passes.
- [ ] Pytest passes.
- [ ] Python compile check passes.
- [ ] `node --check static/app.js` passes.
- [ ] README/config docs updated for user-facing changes.
- [ ] Security notes updated if the network/auth/read-only model changes.
