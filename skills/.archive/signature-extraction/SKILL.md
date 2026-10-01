---
name: signature-extraction
description: Extract handwritten signatures from photographed documents (ID cards, forms) and export as SVG + transparent PNG.
---

# Signature Extraction from Document Photos

Extract a handwritten signature from a photo of an ID card, form, or document. Output: clean SVG (vector) and PNG with transparent background.

## Trigger

User asks to extract a signature, firma, or handwritten element from a document image.

## Pipeline

### 1. Verify the file path exists
```bash
ls -la "<user_provided_path>"
```
User-provided paths from messaging apps (KDE Connect, WhatsApp) may have extra subdirectories. Search if not found:
```bash
search_files pattern="<filename>" path=~/Descargas target=files
```

### 2. Locate the signature with vision
Use `vision_analyze` on the original image to find the handwritten signature. Ask for bounding box as fractions of image dimensions. Printed text is NOT the signature — look for cursive, fluid strokes.

Pitfall: CPF/ID cards have signatures in different positions — cédula venezolana has it middle-left next to names, not bottom-right. Always confirm with vision first.

### 3. Crop the signature area
```bash
magick "$IMG" -crop "WxH+X+Y" +repage crop.png
magick crop.png -resize 400% crop_4x.png
```
Scale up 4x to give potrace more pixels to work with.

### 4. Color-separate handwritten ink from printed text
Handwritten signatures (blue ballpoint) differ from printed text (black toner). Use blue-channel dominance:

```python
R, G, B = arr[:,:,0], arr[:,:,1], arr[:,:,2]
blue_tint = (B > R * 0.95) | (B > G * 0.95)
dark = np.max(arr, axis=2) < 160
printed = np.min(arr, axis=2) < 80  # very dark = printed
sig = dark & blue_tint & (~printed)
```

Save as RGBA PNG with signature pixels black on transparent background.

### 5. Extract alpha mask and smooth
```bash
magick sig_color.png -alpha extract -threshold 50% -negate mask.pbm
magick mask.pbm -morphology Smooth Disk:5 -gaussian-blur 0x2 -threshold 40% mask_smooth.pbm
```

### 6. Vectorize with potrace
```bash
potrace -s --turdsize 5 -a 0.0 -O 0.05 -t 3 -o firma.svg mask_smooth.pbm
```
- `-a 0.0`: no corner detection → smoother curves
- `-O 0.05`: low optimization tolerance for curve fidelity
- `--turdsize 5`: filter small noise specks

### 7. Generate transparent PNG
```bash
magick sig_clean.png -fuzz 5% -transparent white -trim +repage firma.png
```

## Variant: image is already pre-cropped to the signature

If the user pastes a tight crop (e.g. 169×57 with only the signature and a bit of surrounding paper — no printed text), skip the locate/crop step and go straight to ink isolation:

1. Scale up 4–6× (`-resize 600%`) — pre-cropped images are often tiny.
2. Find ink pixels: `dark = brightness < 130` works for dark ink on light card.
3. Connected-component selection: when the region contains BOTH signature strokes AND card border / noise, pick the **largest** component (or top-N by size) and discard the rest.
4. Smooth alpha with `ImageFilter.GaussianBlur(radius=1.0–1.5)` before saving — kills the staircase edges that show up on low-res scans.
5. Save RGBA; the box for the user is much smaller (typically 100–150 px wide).

Pitfall: do NOT apply the blue-channel-separation trick on a pre-crop — the card border and shadow areas will also pass the blue-tint test and pollute the result. Just use brightness + component selection.

### Variant: pre-crop contains printed text + card border + signature

When the pre-cropped image still contains printed text (e.g. the "NOMBRES:" label and printed name above the signature) and/or a card border strip, **largest-component selection fails** — the card border is usually the largest connected dark region.

Filter components by position instead:

```python
for comp in components:
    min_r, max_r, min_c, max_c = comp['bbox']
    cy = comp['cy']  # vertical center
    h_c, w_c = comp['h'], comp['w']

    # Skip card border (tall, narrow, at left edge)
    if h_c > 200 and w_c < 100 and min_c < 100:
        continue
    # Skip printed text at top of crop
    if cy < 100:
        continue
    # Keep: signature zone (middle of crop)
    if 100 <= cy <= 280:
        sig_pixels.extend(comp['pixels'])
```

This collects ALL small components in the signature zone (the cursive strokes break into multiple connected pieces due to threshold gaps) while excluding the border and printed text. Key insight: a cursive signature at low resolution often fragments into 4-8 connected components — you need ALL of them, not just the largest.

### Versioned output naming

When the user asks to repeat an extraction ("repite", "hazlo de nuevo", "numeralo"), increment the version suffix: `firma_melany_v3.png`, `firma_melany_v4.png`, etc. Never overwrite a previous output unless explicitly asked.

## Pitfalls

- **Wrong crop area**: Always verify with vision first. Signature location varies by document type.
- **Potrace produces empty SVG**: The mask PBM is all-white (mean=max=65535). Threshold was too aggressive — check pixel values and lower threshold.
- **File path typos**: Messaging apps may nest files in subdirectories. Search if the user's path doesn't resolve.
- **`&` in Python heredocs**: Shell interprets `&` and `|` in inline Python. Write scripts to `.py` files instead of using `<< 'PYEOF'` heredocs for complex logic.
- **Low-res source**: Original ~478×366 JPEG will produce pixelated edges. Smoothing the mask before potrace helps, but the result won't be as clean as from a high-res scan.
- **Vision_analyze "No endpoints found" with the active model**: The fallback vision model sometimes rejects certain image sizes/encodings. Retry once, or render a small preview (`-resize 400x`) and analyze that instead.
- **Vision answers anchored to image-relative coords**: When the user provides a crop, vision returns bbox as fractions of the CROP, not the original. Multiply by the crop's actual size to get real coordinates.
- **Pre-cropped image has card border or shadow in the frame**: The card edge often scores high on edge density and gets confused with handwriting. Position-based component filtering (by y-center) resolves it cleanly — see the pre-cropped workflow reference.
- **"Largest component" is the border, not the signature**: On pre-crops that include a card edge, the border is the largest connected dark region. Don't pick by size alone — filter by vertical position (signature zone: cy 100-280).

## Output

Deliver both files to the same directory as the source image:
- `firma_nancy.svg` — vector paths, scalable
- `firma_nancy.png` — RGBA or LA mode, ~60% transparent background

## References

- `references/pipeline-commands.md` — full shell pipeline for the full-document workflow
- `references/pre-cropped-workflow.md` — workflow when the user already provides a tight crop of just the signature (no card to locate)
- `scripts/extract_signature.py` — reusable extraction script for pre-cropped images. Usage: `python3 scripts/extract_signature.py <input.jpg> <output.png> [--threshold 130] [--blur 0.8]`
