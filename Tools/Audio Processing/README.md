# Audio Processing Pipeline

## Purpose

This is the repository's local speech-processing infrastructure. It exists so that transcription, voice activity detection (VAD), diarization, and noise analysis are capabilities of the VoiceOfOpenDoor repository itself, not a dependency on whichever AI assistant or runtime is being used in a given session.

Any engineer or AI assistant picking up this repository should be able to run this pipeline locally, on the reference platform (Windows 11 — see `Documentation/Development Environment.md`), without network access, once setup is complete.

## Current Status

`analyze.py` exists and is a working command — it was run against the full 20-file corpus in a temporary Linux sandbox and produced a real report (`Evaluation/Sample Outputs/analyze_report_2026-07-28.json`). It only requires Python and FFmpeg, so it should also run unmodified on Windows, but that has not yet been confirmed on Dean's system — see the Verification Status table below.

Everything else in this folder is still a plan and dependency scaffold, not working software: transcription, VAD-based segmentation, and diarization do not exist yet. `analyze.py` covers the objective/technical half of a recording assessment (level, clipping risk, silence count); it does not transcribe, diarize, or judge subjective speech quality.

## Verification Status

| Tool | Windows 11 (Dean's system) | Temporary AI-assistant sandbox |
|---|---|---|
| FFmpeg | Not yet verified | Verified present (Linux sandbox, this session) |
| Python 3 | Not yet verified | Verified present (Linux sandbox, this session) |
| `analyze.py` (objective audio report) | Not yet verified | Verified working — ran against all 20 corpus files, July 28 2026 |
| faster-whisper | Not yet verified | Not attempted |
| Silero VAD | Not yet verified | Not attempted |
| pyannote.audio (diarization) | Not yet verified | Not attempted |

A tool being present in a temporary AI-assistant sandbox does not mean it is installed or working on Dean's Windows 11 system. Only the left-hand column counts for actual project use. See `Documentation/Development Environment.md` for the verification policy this table follows.

## Design Principle: Engine-Agnostic

The pipeline is intended as a consumer/producer interface, not a dependency on one vendor:

- Input: a recording from `Dataset/Raw Audio/`
- Output (once built): a draft transcript, segment/silence boundaries, and an engineering report (levels, clipping, estimated SNR, VAD-detected speech regions)

The transcription engine underneath should be swappable. Do not hardcode downstream tooling (Phase 5 verification, Phase 6 pronunciation dictionary, Phase 7 dataset preparation) to the output format of one specific engine — normalize to a single internal transcript/metadata schema instead (to be defined in `Dataset/Metadata/`).

## Planned Components

| Component | Purpose | Notes |
|---|---|---|
| FFmpeg | Format conversion, level/clipping analysis, resampling | Windows install: `winget install Gyan.FFmpeg` |
| A local ASR engine (e.g. faster-whisper or whisper.cpp) | Draft transcript generation | Local-first; swappable — see engine-agnostic note above |
| Silero VAD | Voice activity / silence detection for segmentation | Local, lightweight |
| pyannote.audio (diarization) | Flag multi-speaker recordings (e.g. background radio, room noise from other speakers) | See "Diarization" section below — meaningfully more involved than a `pip install` |
| Noise/SNR analysis | Objective corpus-suitability metrics | Can extend the ffmpeg-based checks already used in Recording Assessment v1/v2 |

## Diarization (pyannote.audio) — Additional Requirements

Installing the `pyannote.audio` package alone does not make diarization work. Before it's usable, this project will also need:

- A Hugging Face account and acceptance of the relevant model license(s)
- A Hugging Face access token, configured locally
- Confirmation of whether, once the model is downloaded once, it can run fully offline afterward, or requires network access on every run
- CPU vs. GPU requirements for acceptable processing speed
- A fallback plan if diarization setup proves impractical (e.g. relying on the subjective listening review in Phase 3 to catch multi-speaker/background-audio issues instead, as was done manually for `RecUpAppTest Recording.mp3`)

None of this has been set up yet. Treat diarization as the highest-friction component in this pipeline.

## Usage: analyze.py

```
python analyze.py "Dataset/Raw Audio" --out report.json
python analyze.py "Dataset/Raw Audio/somefile.m4a"
```

Requires only Python 3.8+ and FFmpeg on PATH — no other packages. Produces duration, format, sample rate, channel count, mean/peak volume, and a silence-segment count per file, plus simple objective flags (clipping risk, low level, low bitrate). See `Evaluation/Sample Outputs/analyze_report_2026-07-28.json` for a real report generated from the full corpus.

## Setup

- **Windows 11 (primary):** `setup.ps1`. Not yet run or verified — treat as a draft until it has been executed successfully on Dean's system and the Verification Status table above has been updated.
- **Linux (secondary/optional):** `setup.sh`. Also not yet verified end-to-end; kept as an alternate path, not the default.

## Workflow (once the pipeline actually exists)

1. Drop new recordings into `Dataset/Raw Audio/` (archival masters — never modified in place).
2. Run the pipeline to produce: draft transcript, VAD segment boundaries, and an engineering report per recording.
3. Engineering review (Phase 3) uses the report plus a listening pass to assign a classification (Candidate / Conditional Candidate / Evaluation Only / Rejected).
4. Draft transcripts for Candidate/Conditional Candidate recordings move to human verification (Phase 5) before use.
