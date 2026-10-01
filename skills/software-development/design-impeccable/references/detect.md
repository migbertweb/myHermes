# Detect

Deterministic anti-pattern detection.

## CLI
- `npx impeccable detect <paths>` — scan files or directory
- `npx impeccable detect --json .` — machine-readable output
- `npx impeccable ignores add-file "src/legacy/**"`
- `npx impeccable ignores add-value overused-font Inter --reason "Brand font"`

## Inline ignores
- File-level: `/* impeccable-disable */`
- Line-level: `// impeccable-disable-line` or `/* impeccable-disable-line */`
- Next-line: `// impeccable-disable-next-line`

## Config
Respects `.impeccable/config.json` and `.impeccable/config.local.json`:
- `detector.ignoreRules`
- `detector.ignoreFiles`
- `detector.ignoreValues`
- `detector.designSystem.enabled`

## When to use
- After adding a component or route.
- Before shipping.
- When UI feels “off” but you can’t name it.
