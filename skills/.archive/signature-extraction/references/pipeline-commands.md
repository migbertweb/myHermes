# Signature Extraction Pipeline — Full Commands

Quick-reference shell pipeline for extracting a handwritten signature from a document photo.

## Prerequisites
```bash
pacman -S imagemagick potrace python-pillow python-numpy
```

## Step-by-step

```bash
IMG="/path/to/document.jpg"
WORK=/tmp/sig_extract
mkdir -p "$WORK" && cd "$WORK"

# 1. Crop signature area (coordinates from vision analysis)
magick "$IMG" -crop "210x55+10+145" +repage crop.png
magick crop.png -resize 400% crop_4x.png

# 2. Color-separate blue ink from printed black text
python3 sig_color.py   # script below

# 3. Crop to just the signature portion (below printed text)
magick sig_color_all.png -crop "840x130+0+90" +repage sig_clean.png

# 4. Extract alpha mask and smooth
magick sig_clean.png -alpha extract -threshold 50% -negate mask.pbm
magick mask.pbm -morphology Smooth Disk:5 -gaussian-blur 0x2 -threshold 40% mask_smooth.pbm

# 5. Vectorize
potrace -s --turdsize 5 -a 0.0 -O 0.05 -t 3 -o firma.svg mask_smooth.pbm

# 6. Transparent PNG
magick sig_clean.png -fuzz 5% -transparent white -trim +repage firma.png
```

## sig_color.py

```python
from PIL import Image
import numpy as np

img = Image.open('crop_4x.png')
arr = np.array(img).astype(float)
h, w = arr.shape[:2]

R, G, B = arr[:,:,0], arr[:,:,1], arr[:,:,2]

# Blue-ish ink: B stronger than R or G
blue_tint = (B > R * 0.95) | (B > G * 0.95)
dark = np.max(arr, axis=2) < 160
printed = np.min(arr, axis=2) < 80

# Signature: dark, blue-tinted, NOT printed
sig = dark & blue_tint & (~printed)

out = np.zeros((h, w, 4), dtype=np.uint8)
out[:,:,3] = 0
out[sig, 0:3] = 0
out[sig, 3] = 255
Image.fromarray(out, 'RGBA').save('sig_color_all.png')

# Also save blue channel diff for debugging
blue_diff = np.clip(B - np.maximum(R, G) + 128, 0, 255)
Image.fromarray(blue_diff.astype(np.uint8)).save('sig_blue_diff.png')
```

## Debugging

- Check if PBM has black pixels: `magick mask.pbm -format "mean=%[mean] min=%[min]" info:`
  - mean=65535 = all white → threshold too aggressive
  - mean < 60000 = has dark pixels
- Check PNG transparency: `python3 -c "from PIL import Image; import numpy as np; a=np.array(Image.open('firma.png')); print((a[:,-1]==0).sum(), 'transparent')"`
