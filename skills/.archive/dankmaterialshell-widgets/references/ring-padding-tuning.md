# Ring Padding Tuning

## The Problem

The `ResourceRingIcon` component wraps a `DankIcon` inside a circular Canvas ring. The ring's outer dimensions are `barIconSize + padding`. If the padding is too large, the ring extends beyond the bar edges (especially on thin bars). If the padding is too small, the ring stroke clips into the icon.

## The Formula

```
ringSize = iconSize + padding
```

Where:
- `padding` = total extra pixels added to the icon size for the ring diameter
- Effective margin per side = `padding / 2`

## Recommended Values

| Padding | Margin/side | Best for |
|---------|-------------|----------|
| `+ 12`  | 6px         | Thick bars (40px+), roomy look |
| `+ 8`   | 4px         | Medium bars (30-40px), balanced |
| `+ 6`   | 3px         | Thin bars (< 30px), tight fit |

## Canvas Ring Geometry

The ring is drawn with:
```qml
var r = w / 2 - 2          // arc radius
ctx.lineWidth = 3           // stroke thickness
```

So the outer edge of the ring stroke is at `w/2 - 2 + 1.5 = w/2 - 0.5` from center.

For `padding = 8`: `w = iconSize + 8`, `w/2 = iconSize/2 + 4`
- Outer ring edge from center = `iconSize/2 + 4 - 0.5 = iconSize/2 + 3.5`
- Icon edge from center = `iconSize/2`
- Gap between icon and ring = `3.5px`
