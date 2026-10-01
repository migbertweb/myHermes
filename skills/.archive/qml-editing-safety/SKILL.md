---
name: qml-editing-safety
description: \"Guidelines for safely editing QML and JavaScript files via CLI tools like sed to prevent syntax corruption.\"
version: 1.0.0
author: Viernes
license: MIT
platforms: [linux, macos, windows]
---

# QML Editing Safety

Editing QML and JavaScript files via `sed` or other regex-based line editors is highly risky because these languages rely heavily on balanced braces `{}` and parentheses `()`. A single incorrect regex replacement or a blind line deletion can corrupt the entire file structure, leading to plugins failing to load without clear error messages.

## Core Principles

1. **Prefer Holistic Edits over Line-Based Edits**:
   - Avoid using `sed` for complex structural changes (like removing blocks of code).
   - If the file is small enough, read the entire file, perform the edit in Python (where you can validate the result), and write the whole file back using `write_file`.

2. **The \"Brace-Count\" Trap**:
   - Never use `sed` to delete \"everything from X to the next `}`\". This frequently deletes nested braces, leaving the final file with mismatched closures.
   - **Pitfall**: `sed '/pattern/,/}/d'` is dangerous in QML because a `Rectangle` inside another `Rectangle` will cause the deletion to stop at the first nested closing brace, not the block's actual end.

3. **Validation Workflow**:
   - After any automated edit to a UI file (QML, JS), immediately verify the file content via `read_file` or `cat`.
   - If the plugin is for a shell like DMS, check the logs or try to reload the plugin immediately.

## Safe Modification Patterns

### Changing a String/Value (Safe)
Use `sed` for simple find-and-replace of unique strings.
`sed -i 's/old_string/new_string/g' file.qml`

### Removing a specific Element (Caution)
If you must remove an element, target a unique identifier or a very specific block that does not contain nested structures. If nested structures exist, **do not use sed**. Use a Python script to parse the block or rewrite the file.

## Recovery Strategy
If a file is corrupted:
1. Revert to the last known good state from a git commit if available.
2. If no backup exists, read the corrupted file and manually identify missing/extra closing braces by tracing the indentation levels.
