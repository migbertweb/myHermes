# Pollinations.ai (Free Image API)

Free, no-key, immediate generative image API using `flux`. Excellent fallback when paid providers (Civitai Buzz, FAL credits) run out.

**Endpoint Setup:**
```python
import urllib.parse
prompt = "3D tech illustration, dark navy background with cyan glow..."
url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1080&height=1920&model=flux&nologo=true"
# Fetch with curl or urllib
```
*Note:* Models like `seedream` are paid-only and will return JSON errors. Stick to `flux` or `turbo`.

## Pitfall: Resolution Clamping
The free API clamps the longest side to 1024px. If you request `width=1080&height=1920`, the API respects the aspect ratio but returns a **576x1024** image.

**Upscale Mitigation (FFMPEG):**
For 9:16 vertical video backgrounds (e.g., Remotion projects), upscale the returned 576x1024 image back to 1080x1920 using high-quality Lanczos scaling and a subtle unsharp mask to restore crispness without heavy distortion:
```bash
ffmpeg -y -loglevel error -i pollinations-output.jpg -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.4:5:5:0.0" -q:v 4 upscaled-final.jpg
```