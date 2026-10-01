# NothingLess / Ambxst Compatibility Analysis

## Summary

**NothingLess is NOT a DMS plugin.** It is a **fork of the Ambxst shell** — a complete Quickshell-based desktop shell, not a plugin for DankMaterialShell. Porting features requires reimplementing them using DMS Plugin API, NOT importing NothingLess modules.

## Architecture Comparison

| Project | Base | Strategy | Plugin system |
|---------|------|----------|--------------|
| **Ambxst** | Quickshell | Standalone shell | None — monolithic QML modules |
| **NothingLess** | Ambxst fork | Fork of Ambxst with notch focus | None — modules imported directly |
| **DankMaterialShell** | Quickshell | Bar + plugin system | PluginComponent, PluginSettings |

## NothingLess Modules That Don't Exist in DMS

| Module path (NothingLess) | DMS equivalent |
|---|---|
| `qs.modules.notch` | Does not exist — reimplement via PluginComponent + popoutContent |
| `qs.modules.theme` | DMS has `Theme.*` but with different API surface |
| `qs.modules.components` | Partial overlap with DMS components |
| `qs.modules.animations` / `Anim.qml` | No equivalent — use `Behavior on scale/opacity` with `Easing.OutBack` |
| `Colors.overBackground` | Does not exist — use `Theme.surfaceText` |

## Key Translational Differences

### Animations

NothingLess uses `Anim.qml` with custom spring functions. Map to DMS:

| NothingLess | DMS Plugin Equivalent |
|---|---|
| `Anim.springSnappy()` | `NumberAnimation { easing.type: Easing.OutBack; easing.overshoot: 1.2 }` |
| `Anim.emphasizedNormal` | `duration: 350` with OutBack |
| `Anim.spring()` | `easing.overshoot: 1.5` |

### The Notch (Dynamic Island)

NothingLess's notch is a **standalone window** using Quickshell's Window API with layer shell. DMS plugins are **bar-attached** via PluginComponent's `horizontalBarPill`/`popoutContent`. The visual effect (pill + expanding popout) can be replicated but the architecture is fundamentally different:

- NothingLess notch → can be positioned anywhere, always visible
- DMS popout → anchored to the bar widget, only visible when expanded

### Scale Animation Pitfall

NothingLess uses `transform: Scale { ... }` in its QML. When porting this pattern, **do NOT apply `Behavior` to `Scale` properties inside `transform:`**. QML's behavior system cannot target sub-properties of transform objects by id. Instead, use the Item's native `scale` property:

```qml
// ✅ Works in DMS
scale: isExpanded ? 1.0 : 0.85
transformOrigin: Item.Top
Behavior on scale { NumberAnimation { easing.type: Easing.OutBack; ... } }

// ❌ Crashes in DMS — "Cannot assign to non-existent property"
transform: Scale { id: s; xScale: 0.85 }
Behavior on s.xScale { ... }
```

## Conclusion

If a user asks about "making NothingLess work in DMS" or "installing NothingLess dependencies", the answer is:

1. NothingLess is a **fork of Ambxst**, not a plugin — you replace DMS with it, not add to it
2. DMS-compatible features must be **reimplemented** using PluginComponent + PluginSettings
3. The NothingLess source is useful as a **design reference** (layout, easing values, color schemes) but the QML patterns often need translation
