#!/usr/bin/env python3
"""Extract a handwritten signature from a pre-cropped document image.

Usage:
    python3 extract_signature.py <input.jpg> <output.png> [--blur 0.8] [--threshold 130] [--margin 8]

The script:
1. Scales the input 6x for better pixel resolution
2. Finds dark pixels (ink) via brightness threshold
3. Finds connected components with BFS (8-connected)
4. Filters by position: keeps components in the signature zone (cy 100-280),
   skips card borders (tall+narrow+left) and printed text (cy < 100)
5. Builds an RGBA PNG with the signature in black on transparent background
6. Smooths edges with Gaussian blur

Requires: Pillow, numpy, ImageMagick (for the initial resize)
"""
import sys
import subprocess
import argparse
import tempfile
import os
from pathlib import Path

from PIL import Image, ImageFilter
import numpy as np
from collections import deque


def scale_up(src_path, work_dir, scale=600):
    """Scale up the source image using ImageMagick for better processing."""
    big_path = os.path.join(work_dir, "source_big.png")
    subprocess.run(
        ["magick", src_path, "-resize", f"{scale}%", "-strip", big_path],
        check=True, capture_output=True
    )
    return big_path


def find_components(dark_mask):
    """Find connected components in a binary mask using BFS (8-connected)."""
    h, w = dark_mask.shape
    visited = np.zeros((h, w), dtype=bool)
    components = []

    for r in range(h):
        for c in range(w):
            if dark_mask[r, c] and not visited[r, c]:
                comp = []
                q = deque([(r, c)])
                visited[r, c] = True
                min_r, max_r, min_c, max_c = r, r, c, c
                while q:
                    cr, cc = q.popleft()
                    comp.append((cr, cc))
                    min_r = min(min_r, cr)
                    max_r = max(max_r, cr)
                    min_c = min(min_c, cc)
                    max_c = max(max_c, cc)
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < h and 0 <= nc < w:
                                if dark_mask[nr, nc] and not visited[nr, nc]:
                                    visited[nr, nc] = True
                                    q.append((nr, nc))
                h_c = max_r - min_r + 1
                w_c = max_c - min_c + 1
                components.append({
                    "pixels": comp,
                    "size": len(comp),
                    "bbox": (min_r, max_r, min_c, max_c),
                    "cy": (min_r + max_r) / 2,
                    "h": h_c,
                    "w": w_c,
                })
    return components


def filter_signature_components(components):
    """Filter components by position to keep only signature strokes.

    Heuristics:
    - Card border: tall (>200px), narrow (<100px), at left edge → skip
    - Printed text: cy < 100 (top of crop) → skip
    - Signature zone: 100 <= cy <= 280 → keep ALL
    """
    sig_pixels = []
    for comp in components:
        min_r, max_r, min_c, max_c = comp["bbox"]
        cy = comp["cy"]
        h_c, comp_w = comp["h"], comp["w"]

        # Skip card border
        if h_c > 200 and comp_w < 100 and min_c < 100:
            continue
        # Skip printed text at top
        if cy < 100:
            continue
        # Keep signature zone
        if 100 <= cy <= 280:
            sig_pixels.extend(comp["pixels"])
    return sig_pixels


def build_rgba(mask, blur_radius=0.8):
    """Build an RGBA image from a boolean mask: black where True, transparent elsewhere."""
    out = np.zeros((*mask.shape, 4), dtype=np.uint8)
    out[mask, 0:3] = 0       # black
    out[mask, 3] = 255        # opaque
    result = Image.fromarray(out, "RGBA")
    if blur_radius > 0:
        result = result.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return result


def extract_signature(src_path, output_path, threshold=130, margin=8, blur=0.8):
    """Main extraction pipeline."""
    work_dir = tempfile.mkdtemp(prefix="sig_extract_")
    try:
        # 1. Scale up
        big_path = scale_up(src_path, work_dir)

        # 2. Load and threshold
        img = Image.open(big_path)
        arr = np.array(img).astype(float)
        h, w = arr.shape[:2]
        print(f"Source (scaled): {w}x{h}")

        brightness = arr.mean(axis=2)
        dark = brightness < threshold
        print(f"Dark pixels: {np.sum(dark)}")

        # 3. Find components
        components = find_components(dark)
        print(f"Components found: {len(components)}")

        # 4. Filter by position
        sig_pixels = filter_signature_components(components)
        print(f"Signature pixels: {len(sig_pixels)}")

        if not sig_pixels:
            # Fallback: use largest component
            components.sort(key=lambda c: c["size"], reverse=True)
            sig_pixels = components[0]["pixels"]
            print(f"Fallback: using largest component ({len(sig_pixels)} px)")

        # 5. Build mask
        mask = np.zeros((h, w), dtype=bool)
        for r, c in sig_pixels:
            mask[r, c] = True

        # 6. Trim to bbox + margin
        ys, xs = np.where(mask)
        r1 = max(0, ys.min() - margin)
        r2 = min(h, ys.max() + margin + 1)
        c1 = max(0, xs.min() - margin)
        c2 = min(w, xs.max() + margin + 1)
        trimmed = mask[r1:r2, c1:c2]
        print(f"Output size: {c2 - c1}x{r2 - r1}")

        # 7. Build RGBA + smooth
        result = build_rgba(trimmed, blur_radius=blur)
        result.save(output_path)
        print(f"Saved: {output_path}")

    finally:
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract handwritten signature from document image")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--threshold", type=int, default=130, help="Brightness threshold for ink (default: 130)")
    parser.add_argument("--margin", type=int, default=8, help="Margin around signature in px (default: 8)")
    parser.add_argument("--blur", type=float, default=0.8, help="Gaussian blur radius for edge smoothing (default: 0.8)")
    args = parser.parse_args()

    extract_signature(args.input, args.output, threshold=args.threshold, margin=args.margin, blur=args.blur)
