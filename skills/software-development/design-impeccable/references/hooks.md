# Hooks

Optional design detector hook for project.

## Setup
Run once after install:
```bash
node ~/.hermes/skills/software-development/design-impeccable/scripts/pin.mjs pin detect
```

The hook auto-runs detector after direct UI file edits and surfaces findings as system reminders where supported.

## Management
- List: `npx impeccable ignores list`
- Add file ignore: `npx impeccable ignores add-file "src/legacy/**"`
- Add value ignore: `npx impeccable ignores add-value overused-font Inter --reason "Brand font"`

## Debug
Set `hook.auditLog` in `.impeccable/config.json` to a path, or env `IMPECCABLE_HOOK_LOG`, to write NDJSON per invocation.
