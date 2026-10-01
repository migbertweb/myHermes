---
name: video-production-assets
description: >-
  Sourcing free multimedia assets (images, video, music) for video
  production on YouTube and other platforms. Covers Wikimedia Commons
  direct-download patterns, royalty-free stock footage sources, audio/music
  sourcing, and organizational conventions for video project directories.
trigger: >-
  When the user needs to find, download, or organize images, video clips, or
  music for a video/audio project especially when they say "busca imagenes",
  "find images", "download footage", "B-roll", "material multimedia",
  "thumbnail images", or "musica de fondo".
---

# Video Production Assets — Sourcing & Organization

## Asset Types

### 1. Images (CC / Public Domain / Royalty-Free)

| Source | License | Best for | Method |
|--------|---------|----------|--------|
| Wikimedia Commons (commons.wikimedia.org) | CC / Public Domain | Logos, historical photos, tech equipment | Direct download via curl |
| Pexels (pexels.com) | Free | Stock photos of people, tech, offices | Download from page |
| Pixabay (pixabay.com) | Free | Photos, vectors, illustrations | Direct download |
| Unsplash (unsplash.com) | Free | High-quality stock photography | API or page download |

### 2. Video B-Roll (Royalty-Free)

| Source | Best for |
|--------|----------|
| Pexels Videos (pexels.com/videos/) | People typing, office, tech scenes |
| Mixkit (mixkit.co/free-stock-video/) | Laptop typing, lifestyle, abstract |
| Pixabay Videos (pixabay.com/videos/) | Laptop, office, nature backgrounds |

### 3. Background Music (Royalty-Free)

| Source | Best for |
|--------|----------|
| Mixkit Music (mixkit.co/free-stock-music/technology/) | Lofi, electronic, beats |
| Pixabay Music (pixabay.com/music/search/genre/electronic/) | Electronic, ambient |
| Free Music Archive (freemusicarchive.org) | Wide variety of CC genres |

## Workflow

### Step 1: Plan the asset inventory

Create a checklist by video segment:

```
Segment         | Needs                             | Source
Intro           | Hook image (ThinkPad classic)      | Wikimedia Commons
History         | IBM era photos, logos              | Wikimedia Commons
Linux section   | Tux, distro logos, ThinkPad+Linux  | Wikimedia Commons
B-roll          | Hands typing, office scenes        | Pexels / Mixkit
Music           | Background track                   | Mixkit / Pixabay Music
```

### Step 2: Download images from Wikimedia Commons

1. Search for the file on commons.wikimedia.org
2. Navigate to the file page (e.g., `https://commons.wikimedia.org/wiki/File:Filename.jpg`)
3. Open browser console and run:
   ```js
   Array.from(document.querySelectorAll('a[href*="upload.wikimedia.org/wikipedia/commons/"]'))
     .filter(a => !a.href.includes('thumb'))
     .slice(0,3)
     .map(a => a.href)
   ```
4. This returns the **direct download URL(s)** (pattern: `hash1/hash2/filename`)
5. Download with curl:
   ```bash
   curl -sL -o "thinkpad-filename.jpg" \
     -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
     "https://upload.wikimedia.org/wikipedia/commons/a/a9/Actual_URL.jpg"
   ```

### Step 3: Handle rate limiting

Wikimedia Commons returns **HTTP 429 (Too Many Requests)** after about 50 requests from one IP within a short window. The response includes a `retry-after` header (typically 600s / 10 min).

**Symptoms:** Downloaded files are HTML documents instead of images.

**Solutions:**
- Wait for the `retry-after` duration before retrying
- Provide a `links-material-adicional.md` file in the project folder with direct URLs the user can download manually
- Reduce batch size to 5-10 files per batch with 10s pauses
- Use different User-Agent strings between batches

### Step 4: Convert SVG logos to PNG

Video editors (DaVinci Resolve, Premiere, Shotcut) handle PNG better than SVG.

```bash
# ImageMagick
convert -background none -resize 800x800 logo.svg logo.png

# With librsvg (better SVG rendering)
rsvg-convert -w 800 -h 800 logo.svg -o logo.png
```

### Step 5: Organize the project directory

```
~/Musica/youtube/<project-name>/
  guion-<project>.md                # Script
  thinkpad-guion-completo.mp3        # Final TTS audio
  thinkpad-parte1-*.mp3              # Individual segments
  links-material-adicional.md        # Manual-download links + B-roll/music sources
  imagenes/
    thinkpad-*.jpg                   # Photos
    tux-linux.png                    # Logos (PNG)
    *.svg                            # Vectors (keep originals)
  videos/
    *.mp4                            # B-roll footage
```

## Pitfalls

- **Wikimedia Commons URLs are NOT guessable.** The hash directories (e.g., `a/a9/`) come from the MD5 of the filename. Always use the browser console to extract them. Never hardcode or guess.
- **Pexels direct download URLs redirect.** `curl -L` is essential. The file link at `pexels.com/video/<id>/download/` returns HTML, not video. Visit the page in a browser and use the actual download button, or use their API.
- **Wikipedia vs. Commons.** Files on `en.wikipedia.org` usually link to Commons. Get the URL from the Commons page, not the Wikipedia page.
- **SVG conversion failure.** Some Wikimedia SVGs are text-only or raster-embedded. Check with `head -1 file.svg`. Should start with `<?xml` or `<svg`. If it starts with `<!DOCTYPE html>`, it is a rate-limit or 404 page, not an SVG.
- **Rate limits are IP-based.** If downloading from a server behind NAT, other users hitting Wikimedia from the same IP exhaust the pool faster. Space requests out.
- **Format mismatch for video editors.** Some editors choke on `.webp` or `.avif`. Prefer `.jpg`, `.png`, or `.mp4`. Convert as needed.
