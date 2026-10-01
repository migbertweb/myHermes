#!/usr/bin/env python3
"""Corta un grid 2x2 de avatares PNGTuber, quita fondo blanco y exporta PNG con alpha.
Uso: python3 cortar_avatares.py <imagen_grid> <dir_salida> [pad]"""
import sys, os
from collections import deque
from PIL import Image, ImageFilter
import numpy as np

def keying(im_rgb):
    """Devuelve (RGBA_image_recortada, bbox) quitando el fondo blanco conectado al borde."""
    a = np.asarray(im_rgb).astype(np.int16)
    h, w, _ = a.shape
    dist = np.sqrt(((a - 255) ** 2).sum(axis=2))
    white = dist < 28  # candidato a fondo (casi blanco)

    # flood fill desde los 4 bordes
    visited = np.zeros_like(white)
    q = deque()
    for i in range(h):
        if white[i, 0] and not visited[i, 0]: visited[i, 0] = 1; q.append((i, 0))
        if white[i, w-1] and not visited[i, w-1]: visited[i, w-1] = 1; q.append((i, w-1))
    for j in range(w):
        if white[0, j] and not visited[0, j]: visited[0, j] = 1; q.append((0, j))
        if white[h-1, j] and not visited[h-1, j]: visited[h-1, j] = 1; q.append((h-1, j))
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < h and 0 <= nj < w and white[ni, nj] and not visited[ni, nj]:
                visited[ni, nj] = 1
                q.append((ni, nj))

    keep = ~visited
    ys, xs = np.where(keep)
    if len(xs) == 0:
        return None, None
    pad = 14
    x1, x2 = max(0, xs.min() - pad), min(w, xs.max() + pad + 1)
    y1, y2 = max(0, ys.min() - pad), min(h, ys.max() + pad + 1)

    alpha = np.where(visited, 0, 255).astype(np.uint8)
    rgba = np.dstack([a.astype(np.uint8), alpha])
    out = Image.fromarray(rgba[y1:y2, x1:x2], 'RGBA')
    # suavizar bordes del alpha
    a_ch = out.split()[3].filter(ImageFilter.GaussianBlur(1.0))
    out.putalpha(a_ch)
    return out, (x1, y1, x2, y2)

def main():
    src, outdir = sys.argv[1], sys.argv[2]
    pad = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    os.makedirs(outdir, exist_ok=True)
    img = Image.open(src).convert('RGB')
    W, H = img.size
    print(f"grid: {W}x{H}")

    names = ['cerrada_1_dedo', 'abierta_1_bienvenida', 'abierta_2_enfasis', 'cerrada_2_sereno']
    quadrants = [(0, 0), (W // 2, 0), (0, H // 2), (W // 2, H // 2)]
    results = []
    for (x0, y0), name in zip(quadrants, names):
        crop = img.crop((x0, y0, x0 + W // 2, y0 + H // 2))
        out, bbox = keying(crop)
        if out is None:
            print(f"!! {name}: sin contenido"); continue
        path = os.path.join(outdir, f'avatar_{name}.png')
        out.save(path)
        results.append((name, path, out.size, bbox))
        print(f"OK {name}: {out.size} bbox={bbox}")

    # collage de verificacion sobre fondo damero para ver el alpha
    cols = 4
    cell_w = max(r[2][0] for r in results) + 24
    cell_h = max(r[2][1] for r in results) + 24
    canvas = Image.new('RGB', (cols * cell_w, cell_h), 'white')
    px = canvas.load()
    for y in range(canvas.height):
        for x in range(canvas.width):
            if ((x // 16) + (y // 16)) % 2:
                px[x, y] = (200, 200, 200)
    for i, (name, path, size, bbox) in enumerate(results):
        im = Image.open(path)
        canvas.paste(im, (i * cell_w + 12, 12), im)
    vp = os.path.join(outdir, 'verificacion_alpha.png')
    canvas.save(vp)
    print("collage:", vp)

if __name__ == '__main__':
    main()
