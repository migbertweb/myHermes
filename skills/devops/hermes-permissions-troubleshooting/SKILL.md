---
name: hermes-permissions-troubleshooting
description: Diagnose and fix permission denied errors (Errno 13) and ownership mismatches in Hermes Agent installation and data directories.
---

# Hermes Permissions Troubleshooting

When Hermes Agent or its CLI is executed via `sudo` or as a different user, it may create files in `~/.hermes/` with `root` ownership. This leads to `Permission denied` (Errno 13) when the agent later runs as the standard user.

## Common Error Signals
- `Exception [Errno 13] Permission denied: '/home/piro/.hermes/.hermes_history'`
- `Permission denied` when writing to `kanban.db`, `state.db`, or `devices.json`.
- Failed `write_file` or `patch` calls on configuration files.

## Diagnosis Workflow

1. **Identify the offending file:**
   Look at the traceback for the absolute path of the file causing the `Permission denied` error.

2. **Check ownership and permissions:**
   Run `ls -lah <file_path>` to check Uid/Gid.
   Example output: `-rw-r--r-- 1 root root ...` indicates the file is owned by root.

3. **Scan for other root-owned files in the home directory:**
   Since root-owned files often come in batches (e.g., after a `sudo` run), scan the entire `.hermes` directory:
   ```bash
   find ~/.hermes -not -user $(whoami) -ls
   ```

## Resolution Steps

### 1. Targeted Fix (Single File)
If only one file is affected:
```bash
sudo chown $(whoami):$(whoami) <file_path>
```

### 2. Bulk Fix (Entire Directory)
If multiple files are affected, recursively restore ownership to the current user:
```bash
sudo find ~/.hermes -not -user $(whoami) -exec chown $(whoami):$(whoami) {} \;
```

## Pitfalls & Notes
- **Avoid running the CLI as sudo:** Unless specifically required for system-level tasks, avoid `sudo hermes ...` as this is the primary cause of this issue.
- **Hidden files:** Remember that `.hermes_history` is a hidden file; `ls -a` is required to see it.
- **Recursive ownership:** Be careful using `chown -R` on system directories; always target the specific user home directory (`~/.hermes`).
