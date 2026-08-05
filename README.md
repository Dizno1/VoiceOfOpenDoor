# VoiceOfOpenDoor

VoiceOfOpenDoor is an engineering project dedicated to creating a high-quality, locally hosted synthetic voice for Open Door Design. Built from a carefully curated speech dataset, pronunciation standards, and a reproducible training process, it provides a consistent narration voice for accessible applications, educational content, audio description, and future Open Door Design projects.

---

## Current Status

- **Current phase:** Phase 3/4 continue in the background; primary focus has shifted to Phase 10 (Accessible Windows Application) per Dean's direction — the repository is becoming a Voice Engineering Workbench (a set of tools, not a set of CLI phases), not a TTS trainer.
- **Current corpus:** the recordings in `Dataset/Raw Audio/`, tracked as structured data in `Dataset/Metadata/recordings.json` - the exact count changes as recordings are imported, reviewed, and deleted, so see the App's Home page for the current total rather than a number here that will go stale
- **What's built:** `Tools/Audio Processing/analyze.py` (objective audio report); `Tools/Dataset Utilities/build_manifest.py` (structured manifest); `App/` — a full 8-tool nav skeleton (Home, Recordings, Analyze, Transcripts, Segments, Train, Generate Speech, Settings), with Home, Recordings, and Analyze fully working (including Add Recordings, play/classify/notes/delete, group- and individual-recording analysis with persisted results, and JAWS-confirmed accessibility fixes) and the rest honest stubs. Uses Open Door Design's shared design system (`DesignPhilosophyAndStandards`). Launch model: double-click launcher opens a local server + browser automatically (Option C), not a bare terminal command. See `App/README.md`.
- **What's still a draft, not working:** `Tools/Synthesis/` (XTTS v2 adapter — correct interface, never executed; unresolved CPML licensing question); transcription, VAD, diarization (none built yet).
- **End-to-end target:** A local Windows command that accepts text and generates a WAV file using the trained VoiceOfOpenDoor voice (Phase 9), an accessible Windows application (Phase 10, now started), and a local API for other Open Door Design apps (Phase 11). Full path in `Documentation/Voice Pipeline Roadmap.md`.
- **Next task:** Analyze is built and tested but not yet JAWS-confirmed on Dean's machine - that's the immediate next step, not new development. After that's confirmed, the next build is the transcript data model and engine preparation (Phase 3), then transcript review (Phase 4) - not the Transcripts screen directly, per the corrected sequencing in `Documentation/Development and Testing Roadmap.md`.
- **Reference platform:** Windows 11 (see `Documentation/Development Environment.md`)

---

## Project Philosophy

VoiceOfOpenDoor exists to create and preserve the authoritative digital voice of Open Door Design.

The recordings are the project's primary asset. Speech synthesis models, training techniques, and AI technologies will continue to evolve, but a carefully designed and documented speech corpus will remain valuable regardless of which engine is ultimately used.

Every engineering decision should improve the long-term quality, portability, and maintainability of the voice corpus rather than optimize for a single model or vendor.

The goal is not simply to train a voice model. The goal is to build a professional digital voice that can represent Open Door Design for many years.

---

## Development Philosophy

Development follows an analysis-first workflow.

Every significant phase begins with analysis, continues with implementation, and concludes with updated documentation.

Repository documentation is considered the authoritative source of project status.

Conversation history should never be required to understand the current state of the project.

---

## Engineering Principles

- Preserve all original recordings.
- Never modify archival source recordings.
- Maintain versioned project documentation.
- Verify transcripts before training.
- Build datasets that remain independent of any specific TTS engine.
- Add new recordings only to address documented gaps.
- Base engineering decisions on analysis rather than assumptions.
- Documentation is part of every completed phase.
- Speech-processing capability (transcription, VAD, diarization) is repository infrastructure, not a dependency on any single AI assistant's runtime. It must run locally and must not be hardwired to one engine.

---

## Repository Continuity

This repository is designed so development can continue regardless of which engineer or AI assistant is performing the work.

Before beginning any new phase:

1. Read the README completely.
2. Read every document in the Documentation folder.
3. Determine the current completed phase.
4. Continue the documented roadmap.
5. Update the documentation before considering the phase complete.

Every completed phase should leave the repository in a state where another contributor can continue development without requiring prior conversation history.

---

## Speech Processing Pipeline

Transcription, voice activity detection, diarization, and noise analysis are provided by local tooling under `Tools/Audio Processing/`, not by whichever AI assistant happens to be operating the repository in a given session. This keeps the corpus workflow reproducible and independent of any one assistant's runtime environment or network access.

`Tools/Audio Processing/analyze.py` (objective level/clipping/silence report) works and has been tested against the full corpus. Transcription, VAD-based segmentation, and diarization are still planned, not built.

Speech synthesis (text to WAV, using the trained voice) is the separate `Tools/Synthesis/` component — see `Documentation/Voice Pipeline Roadmap.md` for the full path from corpus to a usable local application and API, and the engine decision behind it.

Both are designed to be engine-agnostic at their interfaces, even though a specific engine is integrated internally to make each one actually work rather than only supporting every engine in theory.

---

## Capabilities

Engineering-level phase tracking lives in `Documentation/Development and Testing Roadmap.md` (the authoritative near-term plan) and `Documentation/Voice Pipeline Roadmap.md` (the longer corpus-to-application arc, engine selection, and reusability design). This section describes the repository by what it can actually do, not by phase number.

**Recording Management** - working. Import recordings (individual files or a whole folder), play, classify, add notes, and permanently delete, all through the App. Includes duplicate detection by filename and by content, and objective audio analysis (level, clipping risk, silence) backing every recording's assessment.

**Audio Analysis** - working in the App (`/analyze`), not yet JAWS-confirmed on Dean's machine. Runs the same `Tools/Audio Processing/analyze.py` used from the command line, integrated through `App/backend/analysis_service.py` rather than reimplemented - individually, by classification group, or all-at-once, with persisted results shown on each recording's detail page. Objective only: duration, format, codec, sample rate, channels, level, clipping risk, silence. Does not detect speech presence, speaker count, or music - that's a real design direction for a future pass (see the Development and Testing Roadmap's Phase 2), not something implemented yet, and this app does not claim otherwise.

**Transcript Workflow** - not yet built. Design principles are established (`Documentation/Transcript Editing Design Principles.md`) ahead of any editor code, per the project's analysis-first standard.

**Corpus Preparation** - not yet built (segmentation and validation/export).

**Training** - not yet built. Engine decision made (Coqui XTTS v2, pending an unresolved commercial-licensing question - see `Documentation/Voice Pipeline Roadmap.md`), engine-agnostic adapter interface built (`Tools/Synthesis/engines/`), no trained model produced yet.

**Speech Generation** - not yet built as a working command; a draft CLI exists (`Tools/Synthesis/synthesize.py`) but has never been executed anywhere, since it depends on a trained model that doesn't exist yet.
