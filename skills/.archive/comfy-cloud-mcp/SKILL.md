---
name: comfy-cloud-mcp
description: Interaction with ComfyUI via Cloud MCP servers.
category: mlops
---

# Comfy Cloud MCP Interaction

Use when interacting with ComfyUI functionalities via the Model Context Protocol (MCP) through the `mcp__comfy_cloud__*` tools.

## Workflow

1.  **Search Templates**: Use `mcp__comfy_cloud__search_templates(q="<query>")` to find available workflow templates (e.g., "text to image", "image to video").
2.  **Inspect Schema**: Use `mcp__comfy_cloud__get_template_schema(template_id="<template_name>")` to identify addressable inputs and slots.
3.  **Run Template**: Execute with `mcp__comfy_cloud__run_template`.
    - **`name`**: Template name from search results.
    - **`confirm=True`**: Mandatory if the workflow consumes paid credits.
    - **`wait_for_output=True`**: One-shot mode to receive the result directly.
    - **`client_os="linux"`**: Required for `wait_for_output` to generate correct shell download commands.

## Pitfalls & Solutions

### Input Resolution Errors (Slots vs. Nodes)
- **Symptom**: `get_template_schema` returns a slot (e.g., `30.value`), but `run_template` fails with `input_overrides did not resolve to any node in the executed graph: "30"`.
- **Root Cause**: The slot is a proxy for a node within a flattened subgraph.
- **Solution**: Use the flattened internal ID provided in the error message. For example, if the error suggests `{"30:19": {"value": ...}}`, apply this as an `input_override` instead of a `slot_override`.

### Subscription Wall
- **Symptom**: Error: `POST /api/prompt failed: A cloud subscription is required to queue workflows.`
- **Solution**: This MCP is a gateway to a paid service. If a subscription is unavailable, transition to a local self-hosted installation of **ComfyUI** or **Automatic1111 Stable Diffusion WebUI** on your own GPU hardware.
