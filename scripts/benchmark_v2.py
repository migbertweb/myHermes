#!/usr/bin/env python3
"""Benchmark opencode-go vs deepseek providers using Hermes CLI."""

import subprocess
import time
import json
import re

PROMPT = "Escribe exactamente 3 líneas sobre la teoría de la relatividad en español. No agregues ni una palabra más."

def test_provider(provider, model):
    """Run a single query and measure performance."""
    cmd = [
        "hermes", "chat", "-q", PROMPT,
        "--provider", provider,
        "--model", model,
        "-Q"  # quiet mode (suppress banner)
    ]

    t0 = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=90
    )
    elapsed = time.time() - t0

    stdout = result.stdout
    stderr = result.stderr

    # Extract the response content (after the banner/query lines)
    # Hermes output format varies, look for the response text
    output = stdout + stderr

    # Try to find token usage in the output (if verbose mode)
    token_match = re.search(r'(\d+)\s+tokens?\s+(sent|used|in).*?(\d+)\s+tokens?\s+(received|out|generated)', output, re.IGNORECASE)
    prompt_tokens = token_match.group(1) if token_match else "N/A"
    completion_tokens = token_match.group(3) if token_match else "N/A"

    # Extract the actual response - look for text after typical hermes output
    # Clean up the output
    lines = output.strip().split('\n')
    # Filter out status messages and banners
    content_lines = [l for l in lines if l.strip() and not l.startswith('\x1b') and not l.startswith('Query:') and not 'Initializing' in l and not '╭' in l and not '╰' in l and not '─' in l and not '│' in l]

    response_text = ' '.join(content_lines[-5:]) if content_lines else output[-200:]

    return {
        "provider": provider,
        "model": model,
        "time_seconds": round(elapsed, 2),
        "exit_code": result.returncode,
        "response_clean": response_text[:150],
        "raw_length": len(output),
        "error": stderr if result.returncode != 0 else None,
    }


results = []

print("=" * 60)
print("BENCHMARK: opencode-go vs deepseek (directo)")
print("=" * 60)

# Test 1: opencode-go
print("\n⏳ opencode-go...", end=" ", flush=True)
try:
    r1 = test_provider("opencode-go", "deepseek-v4-flash")
    results.append(r1)
    print(f"{r1['time_seconds']}s" if not r1['error'] else f"ERROR ({r1['exit_code']})")
except subprocess.TimeoutExpired:
    print("TIMEOUT (>90s)")
    results.append({"provider": "opencode-go", "model": "deepseek-v4-flash", "time_seconds": ">90", "error": "timeout"})

# Test 2: deepseek
print("⏳ deepseek (directo)...", end=" ", flush=True)
try:
    r2 = test_provider("deepseek", "deepseek-v4-flash")
    results.append(r2)
    print(f"{r2['time_seconds']}s" if not r2['error'] else f"ERROR ({r2['exit_code']})")
except subprocess.TimeoutExpired:
    print("TIMEOUT (>90s)")
    results.append({"provider": "deepseek", "model": "deepseek-v4-flash", "time_seconds": ">90", "error": "timeout"})

# Print comparison table
print("\n" + "=" * 60)
print(f"{'PROVEEDOR':<22} {'TIEMPO':<12} {'ESTADO':<12}")
print("-" * 60)
for r in results:
    status = "✅ OK" if not r.get('error') else f"❌ {r.get('error', 'unknown')}"
    t = r['time_seconds']
    print(f"{r['provider']:<22} {str(t)+'s':<12} {status:<12}")
print("=" * 60)
