# Synthesis

## Purpose

This is the engine-agnostic inference layer: text in, WAV out, using the VoiceOfOpenDoor voice model. Phase 9 (Local Synthesis Command), Phase 10 (Accessible Windows Application), and Phase 11 (Local API) all build on this layer rather than calling a specific TTS engine's API directly.

See `Documentation/Voice Pipeline Roadmap.md` for the full engine decision and rationale.

## Status: Draft, Not Yet Runnable

`synthesize.py` in this folder is a first draft of the Phase 9 command. It has **not** been run or verified anywhere — not in a temporary sandbox, not on Dean's Windows system. It requires:

- Network access (to `pip install` the TTS package and download the XTTS v2 model weights on first run)
- A trained/cloned voice model, which does not exist yet — Phase 7 (dataset) and Phase 8 (engine integration, producing the actual voice clone) come before this can produce Dean's voice specifically

Until those exist, this script cannot be tested end-to-end. It's included now so the interface shape and the Phase 9 target are concrete, not just described in prose — but treat every line of it as unverified until it has actually been run.

## Interface

```
python synthesize.py "Text to speak" --voice path/to/voice_reference_clips --out output.wav
```

`--voice` points at reference audio (for XTTS v2's voice-cloning mode) or, once Phase 8 produces a dedicated model artifact, a path to that model instead. The interface is intentionally engine-agnostic at the command-line level even though the current implementation is XTTS-v2-specific internally — swapping engines should mean editing inside `synthesize.py`, not changing how it's called.

## Next Steps Before This Is Real

1. Install and verify XTTS v2 on Dean's Windows 11 system (`pip install coqui-tts` or `pip install TTS`; confirm which package name is current before installing).
2. Confirm GPU availability on the Windows machine — affects synthesis speed, not whether it works at all.
3. Produce a first voice reference set from Phase 3/7 accepted recordings.
4. Run `synthesize.py` for the first time and record the result — success or failure — in the Verification Status table below.

## Verification Status

| Item | Windows 11 (Dean's system) | Temporary AI-assistant sandbox |
|---|---|---|
| Package name / API confirmed against current docs | Confirmed July 28, 2026 (`coqui-tts`, `TTS.api.TTS`, `tts_to_file`) — documentation check only, not an install or run | Same check, same result |
| `synthesize.py` actually runs | Not yet verified | Not attempted (no network/GPU in sandbox; XTTS v2 cannot be installed here) |
| Produces recognizable Dean-voice output | Not yet verified | N/A |

**CPML licensing — unresolved.** See Engine Decision in Voice Pipeline Roadmap. Do not proceed to Phase 8 integration until this is either confirmed acceptable or the engine is switched to Chatterbox.
