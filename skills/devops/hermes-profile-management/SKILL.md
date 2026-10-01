---
name: hermes-profile-management
description: "Use when creating or setting up named Hermes profiles."
version: 1.0.0
created_by: agent
metadata:
  hermes:
    tags: [hermes, profile, devops, configuration, mcp, skills]
---

# Hermes Profile Management

Procedures for creating, provisioning, and customizing named Hermes Agent profiles (`~/.hermes/profiles/<name>/`).

## Overview

Each Hermes profile operates as an isolated environment with its own `config.yaml`, `.env`, `sessions/`, `skills/`, and memory. However, newly created profiles only inherit default/builtin configurations by default. Setting up a specialized profile (e.g. `video-editor`, `devops-chief`) requires provisioning its MCP servers, local skills, and environment variables.

## Workflow for Provisioning a Profile

### 1. Profile Creation & Alias Setup
```bash
hermes profile create <profile-name>
```
This generates the directory structure at `~/.hermes/profiles/<profile-name>/` and creates a CLI wrapper alias at `~/.local/bin/<profile-name>`.

### 2. Environment Variables Sync
Check if `~/.hermes/profiles/<profile-name>/.env` exists. If new or incomplete, sync API keys from the primary `~/.hermes/.env`:
```python
import os, shutil

main_env = os.path.expanduser('~/.hermes/.env')
prof_env = os.path.expanduser(f'~/.hermes/profiles/{profile}/.env')

if os.path.exists(main_env) and not os.path.exists(prof_env):
    shutil.copy(main_env, prof_env)
```

### 3. MCP Servers Sync
By default, a new profile has an empty `mcp_servers: {}` in its `config.yaml`. To provision MCP servers from the main config or specific tools:
1. Load `~/.hermes/config.yaml` and `~/.hermes/profiles/<profile>/config.yaml`.
2. Copy relevant `mcp_servers` entries into the profile's `config.yaml`.
3. Verify connection:
   ```bash
   hermes -p <profile> mcp list
   hermes -p <profile> mcp test <server-name>
   ```

### 4. Custom & Local Skills Symlinking
New profiles only load builtin skills shipped with Hermes. Custom/local skills in `~/.hermes/skills/` (and symlinked skill repos) are NOT automatically present in `~/.hermes/profiles/<profile>/skills/`.

To expose custom/local skills to the new profile:
```python
import os

source_base = os.path.expanduser('~/.hermes/skills')
target_base = os.path.expanduser(f'~/.hermes/profiles/{profile}/skills')

# Symlink relative skill paths (e.g., 'creative/remotion-video', 'video')
for rel_path in skill_list:
    src = os.path.join(source_base, rel_path)
    dest = os.path.join(target_base, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(src) and not os.path.exists(dest):
        os.symlink(src, dest)
```
Verify skills are registered:
```bash
hermes -p <profile> skills list
```

## Verification Checklist

- [ ] Profile config created and valid YAML (`python3 -c "import yaml; yaml.safe_load(open('...'))"`).
- [ ] `.env` populated with required credentials.
- [ ] `hermes -p <profile> mcp list` shows all expected MCP servers as `✓ enabled`.
- [ ] `hermes -p <profile> mcp test <server>` passes for each server.
- [ ] `hermes -p <profile> skills list` includes expected local/custom skills.
