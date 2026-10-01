---
name: obs-asset-design
description: "Use for circular webcam masks, shadows, and neon borders."
argument-hint: "[asset-type] [color] [dimensions]"
license: MIT
metadata:
  author: migbert-agent
  version: "1.0.0"
---

# OBS Asset Design

Procedural generation of image assets for OBS Studio to achieve professional-grade webcam overlays.

## When to Use
- Creating a circular webcam crop (Image Mask).
- Adding depth to a circular webcam (Drop Shadows).
- Creating stylized accent rings (Neon Borders).

## Core Workflow

### 1. Generation (Programmatic)
Avoid AI image generators for masks as they produce "fuzzy" edges. Use programmatic generation (Python/PIL) for mathematical precision.

#### The Alpha Mask (The Crop)
- **Requirement**: Pure white circle on pure black background.
- **OBS Setting**: `Image Mask/Blend` $\rightarrow$ `Alpha Mask (Alpha Channel)`.
- **Logic**: `RGB (0,0,0)` background $\rightarrow$ `RGB (255,255,255)` ellipse.

#### The Shadow (The Depth)
- **Requirement**: Soft, transparent radial gradient.
- **Logic**: Grayscale 'L' image $\rightarrow$ Ellipse $\rightarrow$ `GaussianBlur(radius=50)` $\rightarrow$ Use as alpha channel for solid black RGBA image.

#### The Neon Border (The Accent)
- **Requirement**: Glowing ring with a bright core.
- **Logic**: Layering via `Image.alpha_composite`:
    1. **Glow**: Thicker ring $\rightarrow$ Gaussian Blur.
    2. **Ring**: Solid neon color line.
    3. **Core**: Thin white/bright line for "light tube" effect.

### 2. OBS Implementation
1. **Masking**: Apply the mask filter to the Video Capture Device.
2. **Shadow**: Add the shadow image as a source *below* the camera.
3. **Border**: Add the border image as a source *above* the camera.
4. **Grouping**: Group all three sources to move them as a single unit.

## Pitfalls
- **Edge Aliasing**: If the mask isn't pure black/white, the edges of the webcam will look jagged.
- **Alignment**: Assets must share exact square dimensions (e.g., 1080x1080) to align automatically.
- **Layer Order**: Putting the shadow above the camera will block the video feed.
