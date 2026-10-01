# Wake word / voice pipeline diagnostics (Hermes Desktop)

## When to use
User reports the wake word ("hey hermes") transcribes their speech but "nothing happens" — no reply, no audible action. The transcription working does NOT mean the pipeline is broken; the failure is almost always downstream of STT.

## The pipeline (who runs what)

| Stage | Where | Config |
|---|---|---|
| 1. Wake detection (openWakeWord ONNX, on-device, ~80ms frames) | Backend (Python/PortAudio) | `wake_word.enabled`, `sensitivity` (0.6), `confirmation_frames` (3), `phrase` |
| 2. On fire: detector pauses mic, emits `wake.detected` over WS | Backend → Desktop | — |
| 3. Desktop opens FRESH session (`start_new_session: true`) + records via browser mic, silence ends utterance | Desktop (Electron) | `voice.silence_duration` (3), `max_recording_seconds` (120) |
| 4. STT on backend | Backend | `stt.provider: local` (faster-whisper), `stt.local.model`, `stt.local.language` |
| 5. Transcript submitted as normal user message → creates session | Desktop → Backend | — |
| 6. Agent replies | Backend | — |
| 7. Conversation speaks reply (edge TTS) + detector resumes | Desktop | `tts.provider` |

`capture=local` = backend mic (laptop/server with mic). Remote/headless backends use `capture: client` — desktop streams PCM over the WS.

## Evidence sources (in order)

### 1. `~/.hermes/logs/gui.log` (tui_gateway server log)
Markers:
- `wake.start(gui): disabled (enabled=False, surface=auto)` — wake was OFF at that connect
- `wake.start(gui): listening for 'hey hermes' (openwakeword) capture=local frame=1280` — armed
- `wake.detected: emitting to sid=''` — FIRED. **`sid=''` is NORMAL** — the client opens the session
- `wake.pause: detector paused=True` — mic released for capture
- `wake.resume: detector resumed=True` — conversation ended; pause→resume gap = conversation duration

### 2. `~/.hermes/logs/tui_gateway_crash.log`
Thread dumps; check timestamps (a dump from days ago is not today's failure). `=== SIGTERM received · <ts> ===` = clean shutdown, not a crash.

### 3. `~/.hermes/state.db` (SQLite session store)
- `sessions` table: `started_at REAL` = **unix epoch SECONDS, not ms**. Columns: `id, source, title, started_at`.
  ```sql
  SELECT id, source, substr(title,1,40), datetime(started_at,'unixepoch','localtime')
  FROM sessions WHERE started_at > strftime('%s','YYYY-MM-DD HH:MM:00') ORDER BY started_at;
  ```
- `messages` table: `timestamp` column (epoch sec), `role` in ('user','assistant'), `content` may be NULL (tool-call assistant rows).
- `desktop_session_local_errors` — rare local errors; usually empty.
- A spoken wake command that went through = a NEW desktop-session row ~seconds after `wake.detected`, titled with the spoken text.

## Decision tree
- **No `wake.detected` line** → detector never fired: mic/`input_device`/sensitivity/engine. `/wake status` in a session; `hermes config set wake_word.input_device ...`.
- **`wake.detected` + user-message row + NO assistant rows for minutes** → submit worked, reply never completed. Check whether the user typed something right after (e.g. "en fin", the new question): that typed message interrupted the in-flight turn — Hermes records it as *"user interrupted your previous spoken reply"*. Either the first reply was too slow (fresh session + first TTS call can take 30-60s) or the model call failed silently.
- **`wake.detected` + no user-message row** → desktop-side drop: `submitVoiceTurn` has `if (busy) return` (silent no-op when the composer is busy), or the fresh-session draft wasn't ready.

## Pitfalls
- **Dictation ≠ wake flow.** The mic button in the composer input (`onDictate`) INSERTS the transcript into the input box and does NOT send — user must press Enter. The ear icon (wake) auto-submits. If the user "sees the text sitting in the input", they used dictation, not the wake conversation.
- **`voice.auto_tts: false`** ("Read Responses Aloud") gates TTS only OUTSIDE the voice conversation. The wake conversation speaks replies gated by the composer **muted** toggle (independent of auto_tts). auto_tts off + hands-free expectation = "nothing happened" even when the agent replied in text.
- **`gui.log` does NOT log session/agent runs.** Absence of session activity in gui.log proves nothing — use state.db for that.
- **Wake flow is fully hands-free** — if the user types mid-turn, the reply dies. Advise: test again and wait, don't type.
- First wake use lazily installs openWakeWord deps (`pip install -e ".[wake]"`); desktop installs with `--include-desktop` pre-install them.
