# Pre-cropped Signature Workflow

When the user provides a tight crop (already containing the signature and a bit of surrounding paper, not the full document), the locate/crop/color-separate steps from the main pipeline don't apply. Skip directly to ink isolation.

## When to use this variant

- Source image is small (typically <500 px on its longest side)
- Image shows the signature and some surrounding paper, but no full document
- May still include printed text labels, card borders, or fingerprint — position-based component filtering handles these
- User explicitly pastes a crop or says "this image has the signature"

## Pipeline

```bash
SRC="/path/to/cropped.jpg"
WORK=/tmp/sig_pre
mkdir -p "$WORK" && cd "$WORK"

# 1. Scale up — pre-crops are usually 100-300 px wide
magick "$SRC" -resize 600% -strip source_big.png
```

Then run a Python script (write to file, NOT inline heredoc — `&` and `|` in mask expressions break the shell) that:

1. Loads the scaled image
2. Builds a brightness mask: `dark = brightness < 130`
3. Finds connected components with BFS (8-connected, including diagonals)
4. Selects signature components by **position** (y-center 100-280 = signature zone), not just largest — see below for why
5. Builds RGBA with the chosen component black, everything else transparent
6. Trims to bounding box + small margin
7. Smooths edges with `PIL.ImageFilter.GaussianBlur(radius=1.0)` on the RGBA

```python
from PIL import Image, ImageFilter
import numpy as np
from collections import deque

img = Image.open('source_big.png')
arr = np.array(img).astype(float)
h, w = arr.shape[:2]

brightness = arr.mean(axis=2)
dark = brightness < 130

# Connected components — collect ALL in signature zone, not just largest
visited = np.zeros((h, w), dtype=bool)
components = []
for r0 in range(h):
    for c0 in range(w):
        if dark[r0, c0] and not visited[r0, c0]:
            comp = []
            q = deque([(r0, c0)])
            visited[r0, c0] = True
            min_r, max_r, min_c, max_c = r0, r0, c0, c0
            while q:
                cr, cc = q.popleft()
                comp.append((cr, cc))
                min_r = min(min_r, cr); max_r = max(max_r, cr)
                min_c = min(min_c, cc); max_c = max(max_c, cc)
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < h and 0 <= nc < w and dark[nr, nc] and not visited[nr, nc]:
                            visited[nr, nc] = True
                            q.append((nr, nc))
            components.append({
                'pixels': comp,
                'size': len(comp),
                'bbox': (min_r, max_r, min_c, max_c),
                'cy': (min_r + max_r) / 2,
                'h': max_r - min_r + 1,
                'w': max_c - min_c + 1,
            })

# Filter by position: signature zone only
sig_pixels = []
for comp in components:
    min_r, max_r, min_c, max_c = comp['bbox']
    cy = comp['cy']
    h_c, w_c = comp['h'], comp['w']
    if h_c > 200 and w_c < 100 and min_c < 100:
        continue  # card border
    if cy < 100:
        continue  # printed text
    if 100 <= cy <= 280:
        sig_pixels.extend(comp['pixels'])

mask = np.zeros((h, w), dtype=bool)
for r, c in sig_pixels:
    mask[r, c] = True

# Trim to bbox + margin
ys, xs = np.where(mask)
mr1, mr2, mc1, mc2 = ys.min(), ys.max(), xs.min(), xs.max()
margin = 8
trimmed = mask[max(0, mr1-margin):mr2+margin+1, max(0, mc1-margin):mc2+margin+1]

# RGBA
out = np.zeros((*trimmed.shape, 4), dtype=np.uint8)
out[trimmed, 3] = 255
result = Image.fromarray(out, 'RGBA')

# Smooth to kill staircase edges from low-res source
smoothed = result.filter(ImageFilter.GaussianBlur(radius=0.8))
smoothed.save('firma_pre.png')
```

## Why position-based component selection (not just largest)

A pre-cropped signature often includes:
- The card border (long thin strip on one side) — **often the LARGEST component**
- Printed text labels (e.g. "NOMBRES:", "MELANY MARIANA") at the top of the crop
- A fingerprint
- Shading from a lamination seam or a flash highlight

All of these also pass the brightness test. Simply picking the largest component **fails when a card border or printed text dominates**.

Instead, filter by vertical position (y-center):
- **Card border**: tall (>200px) + narrow (<100px) + at left edge (min_c < 100) → skip
- **Printed text**: cy < 100 (top of crop) → skip
- **Signature zone**: 100 ≤ cy ≤ 280 → keep ALL components in this range

The signature at low resolution fragments into 4-8 connected components (threshold gaps break cursive strokes). You need to collect ALL of them, not just one. Combine their pixels into a single mask.

### Position-filtered component selection code

```python
from collections import deque

# ... after building dark mask and finding components with BFS ...

sig_pixels = []
for comp in components:
    min_r, max_r, min_c, max_c = comp['bbox']
    cy = comp['cy']
    h_c, w_c = comp['h'], comp['w']

    # Skip card border (tall, narrow, at left edge)
    if h_c > 200 and w_c < 100 and min_c < 100:
        continue
    # Skip printed text at top of crop
    if cy < 100:
        continue
    # Keep: signature zone
    if 100 <= cy <= 280:
        sig_pixels.extend(comp['pixels'])
```

Then build the mask from `sig_pixels` (combined), trim, and save as before.

## Smooth blur is non-negotiable

Pre-cropped images are usually 100-300 px wide. At 6× scale, edges look like stairsteps. A Gaussian blur on the RGBA output (not on the mask) softens the edge anti-aliasing into something that looks natural at any zoom.

radius=1.0: light softening, preserves detail
radius=1.5: smoother, slightly loses fine details
radius=2.0: too blurry, only use for very low-res sources

## Output

- `firma_pre.png` — RGBA, ~120-150 px wide, ~17% opaque pixels, rest transparent
- Save alongside the source: `cp firma_pre.png "<source_dir>/firma_<name>.png"`

## Pitfalls specific to this variant

- **Don't apply blue-channel separation here**: the card border and shadows also pass `B > R*0.95`, polluting the result. Brightness + component selection is more reliable.
- **Threshold too aggressive**: if `dark = brightness < 100` produces 0 components, raise to 130 or 150. Inspect the source's actual ink vs background color first.
- **8-connectivity matters**: include diagonals in BFS. Without them, a thin cursive stroke breaks into pieces and the largest component is a fragment.
