# Voice Pipeline Roadmap

## Purpose

This document defines the concrete path from raw recordings to a usable, local, Windows-first speech synthesis application, and how the reusable framework stays separate from Dean's personal voice identity. It supersedes the informal "10 planned phases" framing in earlier README versions — the roadmap below is the authoritative phase list going forward.

## The Layers

Six distinct things exist in this project. They are easy to blur together; keep them separate.

1. **Recording corpus** — the raw, unmodified original recordings. `Dataset/Raw Audio/`. Never edited in place.
2. **Training/cloning dataset** — cleaned, segmented, transcribed clips derived from the corpus, in the format a specific engine needs. `Dataset/Clean Audio/`, `Dataset/Metadata/`. Derived, regenerable, not archival.
3. **Voice model** — the trained/cloned voice identity artifact produced by the chosen engine from the dataset (e.g. speaker embedding or fine-tuned weights). `Training/Models/`.
4. **Inference engine** — the software that turns text + a voice model into audio. This is the swappable component — see "Engine Decision" below.
5. **Accessible application** — the local Windows program a person actually uses: enter text, generate speech, play it, save it.
6. **Local API** — a local service other Open Door Design applications call to get speech from the VoiceOfOpenDoor voice, without each one re-implementing synthesis.

Optional, later: **Windows system voice integration** (registering the voice as a SAPI5 voice so any Windows application can select it directly).

## Roadmap

**Superseded, July 29, 2026.** The phase-by-phase plan below is kept for history, but `Documentation/Development and Testing Roadmap.md` is now the authoritative near-term development plan - it replaces this phase list with a more detailed, test-gated version. The "Layers," "Engine Decision," and "Reusability" sections later in this document are still valid and are not superseded.

### Phase 1 — Repository Foundation
Status: Completed

### Phase 2 — Initial Corpus Assessment
Status: Completed

### Phase 3 — Subjective Listening Assessment
Status: In Progress
Engineering/listening review of each recording. Does not require a transcript.

### Phase 4 — Local Audio Processing Tooling
Status: In Progress
`analyze.py` (objective report: level, clipping risk, silence count) exists and has been tested against the full corpus. Transcription, VAD-based segmentation, and diarization are not yet built.

### Phase 5 — Transcript Generation & Verification
Status: Planned
Draft transcripts generated locally, then verified by Dean against the audio. The interaction design for verification/editing is governed by `Documentation/Transcript Editing Design Principles.md` - written before any editor code, per the project's own analysis-first standard.

### Phase 6 — Pronunciation Dictionary
Status: Planned

### Phase 7 — Dataset Preparation
Status: Planned
Segment recordings into corpus-ready clips; assemble the training/cloning dataset (layer 2 above) from verified transcripts and accepted recordings.

### Phase 8 — Voice Engine Selection & Integration
Status: Planned — decision made, integration not yet built
See "Engine Decision" below. Produces the first trained/cloned voice model (layer 3).

### Phase 9 — Local Synthesis Command
Status: Planned — first practical target
A Windows command-line tool: text in, WAV file out, using the Phase 8 voice model. This is the first point at which the project can actually produce speech, and the milestone everything before it exists to reach.

### Phase 10 — Accessible Windows Application
Status: In Progress
A screen-reader-first Windows interface. Framed as a **Voice Engineering Workbench** — a full nav skeleton of tools (Home, Recordings, Analyze, Transcripts, Segments, Train, Generate Speech, Settings), not a sequence of CLI phases. Launch model: a double-click launcher starts a local server and opens the default browser automatically (Option C - not a bare Flask dev command, not a separate native GUI framework), so no terminal command is needed day to day. Home and Recordings are built; the rest are real routes with honest "not yet built" stub pages, not missing links. See `App/README.md`.

### Phase 11 — Local API
Status: Planned
A local service other Open Door Design applications can call to get VoiceOfOpenDoor speech, without embedding synthesis logic themselves.

### Phase 12 — Framework Generalization
Status: Planned
Separate the reusable framework from Dean's personal assets (see "Reusability" below) so another person can clone the project and build their own voice with it.

### Phase 13 — Optional System Voice Integration
Status: Planned
Register the trained voice as a Windows SAPI5 voice so other Windows applications can select it directly, outside the local API.

## Engine Decision

**First integrated engine: Coqui XTTS v2** (community-maintained fork, package name `coqui-tts` — confirmed against current PyPI/Hugging Face docs July 28, 2026; the original `pip install TTS` package is unmaintained and should not be used).

**Unresolved licensing concern — resolve before Phase 8:** XTTS v2's model weights are under the Coqui Public Model License (CPML), which restricts commercial use. Open Door Design is a business. Before integrating this engine for real, confirm CPML's terms are acceptable for how the resulting voice will actually be used (internal tooling and non-commercial narration are more likely fine than a paid product). If not acceptable, switch to **Chatterbox** (MIT-licensed, no commercial restriction) instead — it was flagged in the same research pass as comparable-or-better quality.

Rationale, checked against the current (2026) open-source landscape rather than assumed from memory:

- Mature and widely documented; installs with a single `pip install` on Windows, no exotic build steps.
- Designed for voice cloning from a short reference sample (as little as ~6 seconds), with quality improving further when given a few minutes of reference audio — which matches this project's ~18-25 minutes of existing recordings well. This project does not need to train a voice model from scratch; it needs a cloning/fine-tuning workflow, which is what XTTS v2 is built for.
- Runs on CPU (slower) or GPU (faster); does not strictly require a GPU to produce a first result.

This is a fast-moving space. Other 2026 options worth tracking behind the same interface if XTTS v2's quality or Windows behavior disappoints in practice: **Chatterbox** (MIT-licensed, reported to outperform XTTS v2 in some blind quality comparisons) and **Kokoro-82M** (extremely lightweight, but does not support voice cloning, so not usable for this project's specific goal). Do not adopt a newer engine without documenting the switch here and confirming it still fits the engine-agnostic interface below.

**The engine-agnostic principle still applies, now formalized.** `Tools/Synthesis/engines/base.py` defines a `SpeechEngine` interface (`generate_speech(text, voice_reference, output_path)`). `engines/xtts_v2.py` implements it. `synthesize.py` and, later, the App and local API should only ever call that interface — never import an engine-specific package directly. Swapping engines means adding a new file under `engines/` and changing the one line in `synthesize.py` that selects the active engine; nothing else should need to change.

A design that supports every possible engine but cannot synthesize speech is not the goal. Integrate XTTS v2 first, get Phase 9 working, and keep the interface clean enough to swap later if needed — in that order of priority.

## Reusability: Framework vs. Personal Assets

For another person to clone this project and build their own voice, the framework and Dean's personal identity must be cleanly separable. They are not the same repository content:

**Personal to Dean — never part of the reusable framework:**
- Everything in `Dataset/Raw Audio/`, `Dataset/Clean Audio/` (his recordings)
- Transcripts of his recordings
- The trained/cloned voice model built from his voice (`Training/Models/`)
- Any of his personal pronunciation entries that are specific to how he speaks rather than general English pronunciation rules

**Reusable framework — the same for anyone:**
- The repository structure and documentation standards
- `Tools/Audio Processing/` (analysis, VAD, diarization, segmentation)
- `Tools/Synthesis/` (the engine-agnostic inference interface)
- The accessible Windows application and local API code
- The setup/verification workflow

A cloned copy of this project is not "done" just because someone swaps in different audio files. The reusable framework must actively walk a new user through: recording guidance, consent/authorization confirmation for using their own voice, transcript verification, segmentation, dataset assembly, engine setup, training/cloning, testing the result, and deployment — the same sequence Dean is going through now, not a shortcut around it. That guided path is itself part of what Phase 12 needs to build, not an afterthought.
