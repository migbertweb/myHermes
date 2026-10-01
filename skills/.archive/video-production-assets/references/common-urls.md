# Common Wikimedia Commons Direct URLs

## ThinkPad Photos (all CC-licensed)

### IBM Era
| File | Direct URL | Notes |
|------|-----------|-------|
| IBM ThinkPad 701 Butterfly | `https://upload.wikimedia.org/wikipedia/commons/0/0a/IBM_ThinkPad_701_Butterfly_05.JPG` | Iconic sliding keyboard |
| IBM Lenovo ThinkPad T60 | `https://upload.wikimedia.org/wikipedia/commons/a/a9/IBM_Lenovo_ThinkPad_T60.jpg` | First IBM/Lenovo co-branded |
| ThinkPad T61 with Linux Mint | `https://upload.wikimedia.org/wikipedia/commons/3/35/ThinkPad_T61_mit_Linux_Mint_%2827544137421%29.jpg` | Running Linux Mint out of box |
| ThinkPads size comparison | `https://upload.wikimedia.org/wikipedia/commons/3/38/ThinkPads_size_comparison_screens_T430s_X40_T60_%2832237287638%29.jpg` | T430s vs X40 vs T60 |
| TrackPoint macro (PCB) | `https://upload.wikimedia.org/wikipedia/commons/b/b8/Pointing_stick_of_a_Lenovo_ThinkPad_keyboard-0899.jpg` | PCB-level closeup |
| IBM ThinkPad badge (mono SVG) | `https://upload.wikimedia.org/wikipedia/commons/1/14/IBM_ThinkPad_logo_askew_badge_monochrome.svg` | SVG vector badge |
| IBM ThinkPad badge (color PNG) | `https://upload.wikimedia.org/wikipedia/commons/b/be/IBM_ThinkPad_Logo_as_used_on_some_older_ThinkPad_cases.png` | Blue IBM badge on cases |

### Lenovo Era
| File | Direct URL | Notes |
|------|-----------|-------|
| Lenovo ThinkPad X1 Carbon | `https://upload.wikimedia.org/wikipedia/commons/5/5a/Lenovo_ThinkPad_X1_Carbon_014_%2810774123843%29.jpg` | X1 Carbon (2013, but good generic shot) |
| ThinkPad X220 | `https://upload.wikimedia.org/wikipedia/commons/9/90/ThinkPad_X220.jpg` | Classic 12" business laptop |
| ThinkPad X220 7-row keyboard | `https://upload.wikimedia.org/wikipedia/commons/c/c3/Lenovo_ThinkPad_X220_7-row_keyboard_US_International_layout.jpg` | The coveted 7-row keyboard |
| ThinkPad T430 keyboard | `https://upload.wikimedia.org/wikipedia/commons/1/18/ThinkPad_T430_%28keyboard%29.jpg` | T430 with classic+chiclet hybrid |
| ThinkPad T410 | `https://upload.wikimedia.org/wikipedia/commons/0/04/Lenovo_ThinkPad_T410_laptop_with_Intel_Core_i5C%2C_c._2011.jpg` | T410 with Core i5 |
| Lenovo ThinkPad T440p | `https://upload.wikimedia.org/wikipedia/commons/6/64/Lenovo_ThinkPad_T440p.png` | Controversial clickpad model |

### ThinkPads + Linux
| File | Direct URL | Notes |
|------|-----------|-------|
| X230 with Trisquel Linux | `https://upload.wikimedia.org/wikipedia/commons/7/76/Trisquel_10.0_running_in_Lenovo_Thinkpad_x230.jpg` | Linux on screen, full setup |
| X200 with Libreboot | `https://upload.wikimedia.org/wikipedia/commons/b/b6/Lenovo_Thinkpad_x200_with_Libreboot.jpg` | Libreboot BIOS replacement icon |
| T61 with Linux Mint | (same as IBM era T61 entry) | |

## Linux / Tech Logos

| Logo | Direct URL | Format |
|------|-----------|--------|
| Tux (Linux mascot) | `https://upload.wikimedia.org/wikipedia/commons/a/af/Tux.png` | PNG |
| Ubuntu | `https://upload.wikimedia.org/wikipedia/commons/9/9d/Ubuntu_logo.svg` | SVG |
| Arch Linux | `https://upload.wikimedia.org/wikipedia/commons/f/f9/Archlinux-logo-standard-version.svg` | SVG |
| Debian | `https://upload.wikimedia.org/wikipedia/commons/4/4a/Debian-OpenLogo.svg` | SVG |
| Fedora | `https://upload.wikimedia.org/wikipedia/commons/3/3f/Fedora_logo.svg` | SVG |
| IBM | `https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg` | SVG |
| Lenovo | `https://upload.wikimedia.org/wikipedia/commons/b/b8/Lenovo_logo_2015.svg` | SVG |

## URL Extraction Technique

When a direct URL is unknown for a specific file, extract it from the Commons page:

1. Navigate to `https://commons.wikimedia.org/wiki/File:Filename.jpg`
2. Run this in browser console:
   ```js
   Array.from(document.querySelectorAll('a[href*="upload.wikimedia.org/wikipedia/commons/"]'))
     .filter(a => !a.href.includes('thumb'))
     .slice(0,3)
     .map(a => a.href)
   ```
3. Use the first result (non-thumbnail) as the direct download URL

The hash directories (e.g., `5/5a/`) are derived from the MD5 hash of the filename and cannot be reliably guessed.
