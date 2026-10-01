#!/usr/bin/env python3
"""Bridge TCP connections to hermes acp subprocess.

Connects TCP clients to a local hermes acp process via clean stdio
(pipes, no PTY), preserving the ACP JSON-RPC protocol intact.

Usage on server:
  python3 hermes-acp-bridge.py

Or as a systemd service:
  [Service]
  ExecStart=/usr/bin/python3 /path/to/hermes-acp-bridge.py

See SKILL.md §4 for the full setup guide.
"""

import asyncio
import logging
import os
import shutil
import sys

HERMES_ACP = shutil.which("hermes") or "/home/piro/.local/bin/hermes"
BIND_ADDRESS = os.environ.get("HERMES_ACP_BIND", "192.168.1.8")
BIND_PORT = int(os.environ.get("HERMES_ACP_PORT", "8000"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)


async def bridge(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Bridge TCP ↔ hermes acp subprocess per connection."""
    peername = writer.get_extra_info("peername")
    logging.info("New connection from %s", peername)

    proc = await asyncio.create_subprocess_exec(
        HERMES_ACP,
        "acp",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def forward_tcp_to_subprocess() -> None:
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                proc.stdin.write(data)
                await proc.stdin.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass

    async def forward_subprocess_to_tcp() -> None:
        try:
            while True:
                data = await proc.stdout.read(65536)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    async def log_stderr() -> None:
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            logging.info(
                "[acp:%s] %s", peername, line.decode(errors="replace").rstrip()
            )

    tasks = [
        asyncio.create_task(forward_tcp_to_subprocess()),
        asyncio.create_task(forward_subprocess_to_tcp()),
        asyncio.create_task(log_stderr()),
    ]

    try:
        await asyncio.gather(*tasks)
    except Exception:
        pass
    finally:
        for t in tasks:
            t.cancel()
        try:
            proc.kill()
        except Exception:
            pass
        try:
            writer.close()
        except Exception:
            pass
        logging.info("Connection from %s closed", peername)


async def main() -> None:
    tcp_server = await asyncio.start_server(
        bridge, host=BIND_ADDRESS, port=BIND_PORT
    )
    logging.info("ACP bridge listening on %s:%s", BIND_ADDRESS, BIND_PORT)
    async with tcp_server:
        await tcp_server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
