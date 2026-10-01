# Node.js Debugging (node inspect + CDP)

## Quick Reference

| Tool | Use case | Start command |
|------|----------|--------------|
| `node inspect` | Built-in CLI debugger, zero install | `node inspect script.js` |
| CDP (`chrome-remote-interface`) | Automated/programmatic | `npm i -g chrome-remote-interface` |
| `--inspect` | Attach to running process | `kill -SIGUSR1 <pid>` then `node inspect -p <pid>` |
| `--inspect-brk` | Pause on first line | `node --inspect-brk script.js` |

## `node inspect` REPL Commands (at `debug>` prompt)

| Command | Action |
|---------|--------|
| `c` / `cont` | continue |
| `n` / `next` | step over |
| `s` / `step` | step into |
| `o` / `out` | step out |
| `pause` | pause running code |
| `sb('file.js', 42)` | set breakpoint |
| `cb('file.js', 42)` | clear breakpoint |
| `bt` | backtrace |
| `list(5)` | show 5 lines of source |
| `watch('expr')` | auto-evaluate expr on every pause |
| `repl` | drop into REPL in current scope (Ctrl+C to exit) |
| `exec expr` | evaluate expression once |
| `.exit` | quit debugger |

## Attaching to a Running Process

```bash
# Enable inspector on existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# Attach
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

To start with inspector:
```bash
node --inspect script.js           # listen, keep running
node --inspect-brk script.js       # listen AND pause on first line
```

For TypeScript via tsx:
```bash
node --inspect-brk --import tsx script.ts
```

## Programmatic CDP (for automation)

Install: `npm i -g chrome-remote-interface`

Driver script skeleton:
```javascript
const CDP = require('chrome-remote-interface');
(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);
    // Walk scopes, evaluate expressions, then resume
    await Debugger.resume();
  });

  await Debugger.enable();
  await Debugger.setBreakpointByUrl({ urlRegex: '.*app\\.tsx$', lineNumber: 119 });
  await Runtime.runIfWaitingForDebugger();
})();
```

Run: `NODE_PATH=/tmp/cdp-tools/node_modules node /tmp/cdp-debug.js`

## Hermes-Specific: Debugging ui-tui (Ink + tsx)

### Debugging a component under dev
```bash
cd /path/to/hermes-agent/ui-tui
npm run build
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
```
Then: `sb('dist/app.js', 220)`, `cont`, `repl` → inspect props/state.

### Debugging a running `hermes --tui`
```bash
hermes --tui &
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)
kill -SIGUSR1 "$TUI_PID"
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'
node inspect ws://127.0.0.1:9229/<uuid>
```

### Debugging `_SlashWorker` / PTY child processes
Those are Python — use the `python-debugpy` reference instead.

### Running Vitest tests under the debugger
```bash
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

### Heap Snapshots & CPU Profiles
```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));
```

```javascript
// Heap snapshot
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

## Pitfalls

1. **Wrong line numbers in TS source.** Breakpoints hit emitted JS. Use `--enable-source-maps` with CDP.
2. **`--inspect` vs `--inspect-brk`.** Use `--inspect-brk` when you need to set breakpoints before any code runs.
3. **Port collisions.** Default is `9229`. Use `--inspect=0` (random port) for multiple processes.
4. **Child processes.** `--inspect` on a parent does NOT inspect children. Use `NODE_OPTIONS='--inspect-brk'`.
5. **Background kills.** If you Ctrl+C out of `node inspect` while target is paused, the target stays paused.
6. **Security.** Never bind `--inspect=0.0.0.0` — exposes arbitrary code execution.

## Verification Checklist

- [ ] `curl -s http://127.0.0.1:9229/json/list` returns the target you expect
- [ ] First breakpoint actually hits
- [ ] Source listing shows the right file (mismatch = sourcemap issue)
- [ ] `exec process.pid` in `repl` returns the PID you meant to attach to
