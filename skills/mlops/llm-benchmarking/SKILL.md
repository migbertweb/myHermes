---
name: llm-benchmarking
description: Workflow for comparing LLM providers (latency, token usage, and cost) using a controlled, repeatable benchmark script.
---

# LLM Benchmarking

This skill provides a systematic approach to comparing different LLM providers or models to determine which offers the best performance (latency) and economic value for a specific use case.

## Workflow

1. **Define the Target Prompt**: Use a consistent, deterministic prompt that requires a fixed output length (e.g., "Write exactly 3 lines...") to ensure fair comparison.
2. **Isolate API Calls**: Implement the benchmark using a script that bypasses high-level agent wrappers if possible, or uses a minimal client to measure raw network + inference latency.
3. **Sample Size**: Perform at least 3 sequential runs per provider to account for transient network spikes and cold-start latency.
4. **Metrics to Capture**:
   - **Latency**: Total time from request to full response (seconds).
   - **Token Usage**: Input tokens and output tokens as reported by the API.
   - **Cost**: Calculate the actual monetary cost per query based on provider pricing.
   - **Correctness**: Verify that the model followed the constraints (e.g., line count, language).

## Pitfalls & Lessons

- **User-Agent Requirements**: Some providers (e.g., `opencode.ai`) may return `403 Forbidden` if a standard programmatic User-Agent is used. Always include a browser-like `User-Agent` header (e.g., `Mozilla/5.0`).
- **Token Accounting**: Different providers may report token counts differently for the same model, or include hidden system prompts. Always compare raw output length vs. reported tokens.
- **Environment Variables**: When scripting benchmarks, ensure API keys are loaded correctly from `.env` files. Shell-level `source` may not propagate to Python scripts unless handled explicitly.

## Verification
- A successful benchmark should produce a summary table comparing Average/Min/Max latency and a "Cost per 1,000 queries" estimate.

## Linked Resources
- `scripts/benchmark_final.py`: A known-good Python implementation for comparing OpenAI-compatible endpoints.
