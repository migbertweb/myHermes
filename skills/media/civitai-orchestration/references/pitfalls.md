# Civitai Orchestration MCP Pitfalls

## 1. InsufficientBuzz Error
This error means the **user's Civitai account** has run out of Buzz credits.
- **Do not** attempt to fix this by changing the `engine` argument (e.g., from `sdcpp` to `google` or `gemini`). ALL generation engines in the Civitai MCP consume the account's pooled Buzz balance.
- **Mitigation:** Stop using the MCP for this turn. Fall back to Hermes' native `image_generate` (which uses FAL/OpenAI, separate billing) or a free HTTP API like Pollinations.ai. Avoid infinite loops of identical retries.

## 2. Aspect Ratio Ignored (`sdcpp` + `flux2klein`)
When invoking image generation with `engine: "sdcpp"` and `model: "flux2klein"`, the API notoriously ignores the `aspectRatio` property (such as `"9:16"`) and returns a **1024x1024 square** image.
- **Mitigation:** Anticipate square output. In video orchestration workflows like Remotion, handle this downstream using `objectFit: "cover"` combined with background overlays/dimming instead of assuming a native vertical image.