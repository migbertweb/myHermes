---
name: nautilus-extensions
description: Guidelines for extending the Nautilus (GNOME Files) context menu using Python and shell scripts.
category: software-development
---

# Nautilus Extensions (GNOME)

Guidelines for extending the Nautilus (GNOME Files) context menu using Python and shell scripts.

## Trigger Conditions
- User wants to add custom actions to the right-click menu in Nautilus.
- User needs top-level menu entries (not hidden in "Scripts" submenu).
- User is on a GNOME-based desktop (Ubuntu, Fedora, CachyOS, etc.).

## Implementation Methods

### 1. Python Extensions (Top-Level Menu)
Best for integrated, high-visibility actions.
- **Dependency:** `python-nautilus` (Arch) or `python3-nautilus` (Debian/Ubuntu).
- **Directory:** `~/.local/share/nautilus-python/extensions/`
- **Core API:** 
    - `get_file_items(files)`: Handles right-clicks on files/folders.
    - `get_background_items(folder)`: Handles right-clicks on empty space.
- **Verification:** Restart Nautilus with `nautilus -q`.

**Pitfalls:**
- **Duplication:** If both `get_file_items` and `get_background_items` are implemented with different `MenuItem` names or similar labels, Nautilus may display both simultaneously when right-clicking a folder.
- **Fix:** Use a consistent `name` for the `MenuItem` and a shared helper method to generate the item, ensuring the menu behaves predictably across different click contexts.
- **LSP Warnings:** Pyright/IDE may flag `Nautilus` or `GObject` imports as unknown; these are resolved at runtime by the Nautilus process.

### 2. Nautilus Scripts (Submenu)
Best for quick-and-dirty automation where a sub-menu is acceptable.
- **Directory:** `~/.local/share/nautilus/scripts/`
- **Requirement:** Files must be executable (`chmod +x`).
- **Available Variables:** `$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS`, `$NAUTILUS_SCRIPT_CURRENT_URI`.

## Workflow
1. Identify if the action needs to be top-level (Python) or can be in a submenu (Script).
2. Install dependencies if using Python.
3. Implement the logic in the respective directory.
4. Ensure the script/extension is executable.
5. Restart Nautilus via `nautilus -q`.

## References
- See `templates/vscodium_open.py` for a production-ready implementation of a "Open with Editor" action.
