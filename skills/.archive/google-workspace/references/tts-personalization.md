# Google Workspace TTS Voice Personalization

Combined reference for how text-to-speech voice settings interact with the user's Google Workspace data reporting and general agent TTS delivery.

This reference consolidates three skills that covered the same edge-tts voice configuration:
- `google-tts-personalization` (general Edge TTS personalization)
- `google-workspace-personalization` (TTS for Workspace data specifically)
- `google-workspace-tts-customization` (TTS persona recipes)

## Edge TTS CLI Parameters

The `edge-tts` CLI supports fine-grained control via command-line flags (NOT SSML tags inside the text string):

| Parameter | Format | Example | Effect |
|-----------|--------|---------|--------|
| Rate | `--rate=+/-X%` | `--rate=-10%` | Speech speed (-15% = slow, +15% = fast) |
| Pitch | `--pitch=+/-XHz` | `--pitch=-15Hz` | Voice pitch (-40Hz = very deep, +20Hz = high) |

**Important:** SSML `<prosody>` tags within the text are NOT supported by the edge-tts CLI and will be read literally.

## User Voice Preferences

The user prefers a balanced, professional but deep tone — neither too grave nor too cartoonishly high.

- Voice: `es-MX-JorgeNeural`
- Rate: approximately `-10%` to `-5%`
- Pitch: approximately `-15Hz`
- Goal: A deep, balanced, authoritative tone avoiding extreme "Darth Vader" darkness or "Jar Jar" high-pitch.

Delivery preference: Workspace data reports should be delivered as voice notes (`.ogg`) unless explicitly requested in text. Summaries should be concise and focused on action items.

## Persona Recipes

### The "Vader/Deep" Persona
- **Rate:** `-10%` to `-20%` (Slow, authoritative)
- **Pitch:** `-15Hz` to `-40Hz` (Deep, resonant)
- **Pitfall:** Avoid below -50Hz — the voice becomes unintelligible or overly "dark"

### The "Acute/High" Persona
- **Rate:** `+10%` to `+20%` (Energetic)
- **Pitch:** `+20Hz` to `+50Hz` (High frequency)
- **Pitfall:** High pitch values can sound "cartoonish" if not balanced with rate

### The "Viernes" Configuration (Separate from Default)
The skills documented a `+15%` rate / `+20Hz` pitch configuration for a distinct personality named "Viernes" — this is NOT the user's default voice preference (which is slower/deeper). Keep separate if the user ever asks for this specific persona.

## Implementation Strategy

Since the standard `text_to_speech` tool may not expose rate/pitch parameters directly, use direct CLI invocation:

```bash
edge-tts --voice es-MX-JorgeNeural --rate=-5% --pitch=-15Hz -t "Text to speak" --write-media output.ogg
```

Then deliver with `MEDIA:output.ogg`.

## Verification

Generate a test sample:
```bash
edge-tts --voice es-MX-JorgeNeural --rate=-5% --pitch=-15Hz -t "Prueba de voz personalizada" --write-media test.ogg
```

Iterate based on user feedback by adjusting Hz or % in increments of 5-10.
