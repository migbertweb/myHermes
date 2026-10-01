# Audio Language Verification

Use `ffprobe` (from ffmpeg) to check the audio language tracks in
downloaded video files without having to watch them.

## Basic command

```bash
ffprobe -v error -select_streams a \
  -show_entries stream=index,codec_name,language:stream_tags=language \
  -of json "/path/to/video.mkv"
```

## Output format

```json
{
  "programs": [],
  "streams": [
    {
      "index": 1,
      "codec_name": "aac",
      "tags": {
        "language": "eng"
      }
    }
  ]
}
```

## Language codes

| Code     | Language              |
|----------|-----------------------|
| `eng`    | English               |
| `spa`    | Spanish               |
| `und`    | Undetermined (English most likely unless "Dual" in release name) |
| `jpn`    | Japanese              |
| `por`    | Portuguese            |
| `fra`    | French                |
| `deu`/`ger` | German             |

## Multiple audio tracks (Dual audio)

If the file has both English and Spanish audio, the output will show
multiple streams:

```json
{
  "streams": [
    {"index": 1, "codec_name": "aac", "tags": {"language": "eng"}},
    {"index": 2, "codec_name": "aac", "tags": {"language": "spa"}}
  ]
}
```

Multiple `language` values = Dual/Multi audio.

## What to check before assuming language

- Releases from YTS (e.g., `[YTS.MX]` or `[YTS.AM]`) are **English-only**.
- Without "Dual", "Lat", "Esp", or "Cast" in the release name, assume English.
- "720p", "1080p", "WEBRip", "BluRay", "x265", "HEVC" alone do NOT indicate language.
- "Dual" usually means English + Spanish. "Lat" or "Latino" usually means Spanish only.
- "Dual-Lat" = English + Spanish Latino (two audio tracks).

## Alternative: check with mediainfo

If ffprobe is not installed:

```bash
# Install
sudo apt-get install -y mediainfo

# Check audio
mediainfo --Inform="Audio;%Language(String)%" /path/to/video.mkv
```
