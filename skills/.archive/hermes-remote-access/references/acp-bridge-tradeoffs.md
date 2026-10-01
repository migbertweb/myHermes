# ACP Bridge: socat vs Python asyncio

## The Problem with socat + pty

The ACP protocol is JSON-RPC 2.0 over newline-delimited stdio. It is a **binary-clean** protocol — every byte matters, no terminal translation is allowed.

`socat EXEC:"...",pty` creates a pseudo-terminal (PTY) for the subprocess, which:
- Adds `\r\n` → `\n` translation (or vice versa)
- May insert terminal escape codes
- Changes the byte stream in ways that corrupt JSON framing

**Result:** The client gets `ACP error -32603: Unhandled client method: session/new` or silent hangs because the JSON-RPC messages are malformed on the wire.

## Why Raw Pipes Work

`asyncio.create_subprocess_exec(..., stdin=PIPE, stdout=PIPE)` creates **anonymous pipes**, not PTYs. These are byte-perfect bidirectional channels:
- No translation of any kind
- No escape code injection
- The subprocess sees a clean stdin/stdout exactly as if it were piped locally

## Performance

- **socat:** ~2% CPU on idle, fork per connection
- **Python asyncio:** ~1% CPU on idle, async I/O with cooperative multitasking
- For the single-user use case (one active connection at a time), both are effectively identical in throughput.

## Portability

- **socat:** Available on all package managers. Service definition is simple.
- **Python:** Always available (std lib only, no dependencies). No install step needed on any Linux/macOS system. Also works on Windows with minor tweaks.

## Recommendation

Always use the Python asyncio bridge. It is:
- More reliable (no PTY corruption)
- Self-contained (stdlib only)
- Easier to debug (logging goes to journald via stderr)
- Configurable via environment variables (`HERMES_ACP_BIND`, `HERMES_ACP_PORT`)
