---
name: hyperframes-asset-cleaning
description: Use to clean embedded text from assets for HyperFrames.
---

# HyperFrames Asset Cleaning

When adding sharp, animated HTML text over an image that already contains embedded text (burned-in), CSS masks and scrims often fail by creating "black blocks" or leaving "ghosting" (residual glows). The professional approach is to clean the asset at the pixel level before it enters the composition.

## Workflow: Radial Power-Masking

1. **Sample Natural Background**: 
   - Do not use pure black. Sample the RGB tone from the natural image area immediately adjacent to the text block.
2. **Create a Radial Mask**:
   - Use a Pillow/NumPy script to generate a grayscale mask.
   - Draw an ellipse centered on the text block.
   - Apply a heavy Gaussian Blur ($\approx 45\text{--}60\text{px}$) to create a soft transition.
3. **Apply a Power Curve**:
   - Transform the mask using a power function (e.g., $mask^{2.2}$ or $mask^{3.0}$). 
   - This ensures the center (where the text is) remains fully opaque to kill the glow, while the edges feather out much more aggressively, blending seamlessly into the background.
4. **Composite**:
   - Blend the sampled background color with the original image using the power-mask.
5. **Numerical Verification**:
   - Before rendering, calculate the mean and max brightness of the target zone. 
   - Ensure "bright pixels" (e.g., value $> 80$ in grayscale) are reduced to $< 5\%$ to prevent "ghosting" when the HTML glow is applied.

## Pitfalls
- **Rectangular Blurs**: Avoid rectangular masks; they create visible edges. Always use radial/elliptical masks.
- **Opaque Scrims**: Avoid using `background: rgba(0,0,0,0.5)` in CSS over the whole area; it kills the image's depth. Clean the asset first, then use minimal CSS for legibility.
- **Edge Clipping**: Ensure the mask doesn't overlap critical elements (faces, logos) by using precise coordinate slicing.
