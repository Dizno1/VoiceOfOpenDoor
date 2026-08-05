# VoiceOfOpenDoor Development and Testing Roadmap

Developed jointly by Dean, Chap (ChatGPT), and Claude, July 29, 2026. This document is now the authoritative near-term development plan for the repository, superseding the phase-by-phase detail in `Voice Pipeline Roadmap.md` (that document's "Layers," "Engine Decision," and "Reusability" sections remain valid and are not superseded - only its phase list is, since two competing phase lists would be exactly the kind of duplicate structure this project avoids elsewhere).

## Purpose

VoiceOfOpenDoor is being developed as a complete voice engineering workbench for preparing recordings, creating an accessible training corpus, producing transcripts, dividing recordings into usable segments, training a voice model, and generating speech.

Development must continue in deliberate stages. Each stage must be completed and tested before the next major stage begins. The current application is the authoritative proving ground for the recording and transcript workflows.

**AccessibleTranscriptEditor should not be developed as a separate application until the transcript workflow has been implemented and tested successfully inside VoiceOfOpenDoor.**

## Current State (as of July 29, 2026)

The application currently includes:
- A root-level launcher
- A working Flask application
- A Home page with current corpus status
- A Recordings page organized by classification
- Recording detail pages
- Audio playback
- Classification changes
- Recording notes
- Permanent recording deletion with confirmation
- Counts that are correct on the next page render after any change (not live/AJAX-updating without a navigation - see the open question in this session's chat log if live updating turns out to be what's actually wanted)
- Placeholder pages for Analyze, Transcripts, Segments, Train, Generate Speech, and Settings

The current recording management workflow is usable enough for structured testing, but it should receive one focused polish phase - formally closed out against the Phase 1 Completion Gate below - before Audio Analysis (Phase 2) is built, and Audio Analysis before any transcript work (Phase 3 onward) begins. Not: recordings, then straight to transcripts. Recordings, then Analyze, then transcripts.

## Add Recordings

**Status: Implemented, July 30, 2026** (individual and multi-file selection; folder selection added the same day after Dean asked whether it existed - Chromium-based browsers only). See `App/README.md` for what was built and tested, including a real bug found and fixed during testing (a damaged/non-audio file wasn't caught by the original error check). `.mov` audio-track extraction was not implemented - flagged as not built rather than silently skipped.

The Recordings page should include an Add Recordings link or button. It should allow:
- choosing one audio file
- choosing multiple audio files
- importing a folder, if practical
- accepting supported formats such as WAV, MP3, M4A, and MOV when audio extraction is supported
- rejecting unsupported files with a clear reason
- preventing accidental duplicate imports
- preserving original filenames
- creating metadata automatically
- placing new files into Evaluation Only by default
- updating all counts immediately
- returning focus to a clear status message after import

It should also report:
- number of files selected
- number imported
- number skipped
- duplicates found
- files that failed
- exact reason for each failure

**This should be tested before deleting the last remaining recording.**

### Required Import Behavior (Phase 1 completion requirement)

1. Add an Add Recordings control to the Recordings page.
2. Allow the user to choose one or multiple audio files.
3. Support the audio formats already handled by the application.
4. Preserve original filenames.
5. Create the required metadata automatically.
6. Place newly imported recordings into Evaluation Only by default unless the repository already defines a more appropriate intake classification.
7. Detect duplicate filenames and duplicate source files where practical.
8. Do not silently overwrite an existing recording.
9. Report how many files were imported, skipped, duplicated, unsupported, or failed.
10. Provide a clear reason for every failed or skipped file.
11. Update recording counts and Home page recommendations immediately after import.
12. Keep focus predictable and announce the result once in the application status region.
13. Test importing one file, multiple files, a duplicate, an unsupported file, a damaged file, and a file with spaces in its name.
14. Confirm imported recordings persist after browser refresh and application restart.

**Phase 1 must not be considered complete until recordings can be added, managed, and deleted entirely through the application.**

## Phase 1: Recording Management Stabilization

### Build
- Confirm the root-level launcher works from any extracted repository location.
- Correct all launcher and setup path references.
- Confirm requirements installation instructions use the correct App directory.
- Remove duplicate launcher files and obsolete setup files.
- Investigate duplicate Play Recording announcements.
- Review the accessibility of the native audio controls.
- Place success and error messages in a consistent status region.
- Confirm classification changes persist after refresh and restart.
- Confirm notes persist after refresh and restart.
- Confirm deletion updates all counts and recommendations.
- Confirm deleted files and metadata are both removed.
- Confirm the Home page recommendation never points to a deleted recording.
- Confirm the application behaves correctly when a classification becomes empty.
- Confirm the application behaves correctly when all recordings in a category are deleted.
- Add clear handling for missing, damaged, or unsupported audio files.

### Test
Test with JAWS and Chrome. Also test basic keyboard operation without a screen reader.

Required scenarios:
- Launch from the repository root.
- Open each recording category.
- Play recordings.
- Change every classification type.
- Move recordings between classifications repeatedly.
- Save, replace, and clear notes.
- Refresh after every type of change.
- Close and restart the application.
- Delete recordings from the beginning, middle, and end of each category.
- Delete multiple recordings in one session.
- Confirm all totals remain accurate.
- Confirm no page contains broken links.
- Confirm focus returns to a predictable location after every action.
- Confirm success messages are announced once.
- Confirm no action unexpectedly moves focus.

### Completion Gate
Phase 1 is complete when recording management remains reliable through repeated classification changes, note changes, deletions, refreshes, and application restarts.

**Do not begin transcript implementation until this phase is stable.**

## Phase 2: Audio Analysis Workflow

### Design Direction (added July 30, 2026)

Direction from Dean, drawing an explicit parallel to the "analyze first, build workflow second" philosophy also being applied in Open Door Accessible Assistant (a separate Dean project): Analyze should not be one feature alongside Transcripts, Segments, Train, and Generate Speech. It should be the application's central intelligence - the step every recording actually passes through before anything else happens to it:

```
Recording -> Analyze -> speech/non-speech -> quality -> speakers -> recommended action
                                                              |
                                    only then branch into: transcript, segmentation, rejection, or training
```

This does not contradict the existing principle below that analysis must support human decisions rather than make final ones - a *recommended* action is exactly that, a recommendation the human confirms or overrides, the same way recording classification already works. What changes is architectural: Analyze becomes the thing every recording flows through first, not a parallel, optional tool a person might or might not run.

This is a real, adopted direction for how Phase 2 should be designed, not yet reflected in the Build/Test/Completion Gate below, which still describe Analyze as a standalone workflow. Update those before implementation begins, not after.

### The Decision Question (added July 30, 2026)

A reframing worth applying to every phase, not just this one: instead of asking "what feature should I build next," ask "what decision should the application help the user make next." Recording Management helps decide which recordings belong in the corpus. Analyze helps decide which recordings deserve transcription. Transcript Review helps decide whether a transcript is accurate. Segmentation helps decide which clips belong in training. Training helps decide which model is best. Speech Generation helps decide which voice profile produces the best output. Every phase in this document should be checked against its own decision question, not just its feature list.

### What Analyze Determines, and What It Outputs

For every recording: format, duration, sample rate, channels, loudness, silence, clipping, background noise, whether speech is present, whether multiple speakers are present, whether music is detected, estimated transcription quality, and a recommended next action.

The recommended action is the important part - not a dump of numbers. The output should read like a conclusion, not a report:

```
Recording Status
Suitable for transcription.
Background noise is acceptable.
Single speaker detected.
Recommended next step: Create draft transcript.
```

or

```
Recording Status
Poor candidate.
Excessive background radio.
Recommendation: Reject from corpus.
```

Some of this (loudness, silence, clipping, duration, format) is already produced by `Tools/Audio Processing/analyze.py`. Speech/non-speech detection, speaker counting, and music detection are not yet built by anything in this repository - that's new work, not a reframing of existing work.

### Open Question: Does Corpus Validation Still Stand Alone?

Dean's July 30 step-by-step sequencing (Analyze -> Transcript Engine -> Transcript Review -> Extract AccessibleTranscriptEditor -> Segmentation -> Training -> Speech Generation) doesn't include a standalone corpus validation/export step between Segmentation and Training the way Phase 7 below does. Not resolved here - noted so it doesn't get silently dropped or silently kept without a decision. Confirm before Phase 6 (Segmentation) is built whether Phase 7 (Corpus Validation and Export) remains a distinct phase or folds into Segmentation's own export step.

### Build
Replace the Analyze placeholder with a working analysis workflow. The page should allow the user to:
- Select an unanalyzed recording.
- Run the existing audio analyzer.
- Receive understandable progress updates.
- Review objective analysis results.
- Return directly to the recording.
- Re-run analysis when necessary.

Analysis should include available measurements such as: duration, peak level, average level, clipping risk, silence, background noise, file format, sample rate, channel configuration, and other currently supported analyzer results.

Analysis results must support human decisions rather than automatically pretending to make final quality judgments.

### Test
Test: a clean recording, a quiet recording, a loud recording, a clipped recording, a recording containing silence, an unsupported file, a missing file, analysis interruption or failure, re-analysis of an existing recording.

### Completion Gate
Phase 2 is complete when analysis can be started, completed, reviewed, repeated, and recovered from failure without using the command line.

## Phase 3: Transcript Data Model and Engine Preparation

### Build
Before building the transcript editor interface, define the transcript data model. The model should support: recording identifier, transcript identifier, full transcript text, segments, segment identifiers, start and end times, speaker information when available, confidence values when available, review status, approval status, editing history, engine and model information, transcript creation date, last modified date.

Prepare transcription engine support. The application should determine: which transcription engines are available, whether Local Whisper is already installed, whether it is installed but not configured, which model is available, whether FFmpeg is available, whether required dependencies are missing, whether transcription can run locally, whether an external paid provider is optional.

Local transcription should be the preferred path when it is available and appropriate. **The application must not incorrectly report that an installed engine is not installed merely because it has not been configured.**

### Test
Test engine discovery under these conditions: engine installed and configured, engine installed but not configured, engine missing, FFmpeg missing, model missing, invalid model path, transcription process failure, successful local transcription.

### Completion Gate
Phase 3 is complete when VoiceOfOpenDoor can correctly identify, configure, and invoke at least one transcription engine and can save a structured draft transcript.

## Phase 4: Transcript Review Prototype

### Build
Replace the Transcripts placeholder with the first working transcript review interface. **This is the phase that will prove the AccessibleTranscriptEditor concept.**

The editor must be task-first rather than row-first. The current transcript segment is the workspace. See `Documentation/Transcript Editing Design Principles.md` for the interaction design this phase is governed by.

Initial workflow: open a transcript -> enter the current segment -> play -> listen -> edit the text -> replay -> approve -> advance to the next segment.

Required principles: playback never steals focus; replay never steals focus; saving never steals focus; commands act on the object that currently has focus; the current segment is always clearly identified; progress is available in one navigable location; JAWS Virtual Cursor Off must provide an efficient editing workflow; NVDA Focus Mode must provide an equivalent editing workflow; the transcript remains usable without a screen reader; the same transcript data model must support future visual and read-only interfaces.

**Do not assign the final shortcut scheme yet. Build the interaction model first.**

### Test
Conduct repeated real transcript editing sessions. Test: opening the first segment, playing and pausing, replaying the current segment, editing transcript text, saving changes, approving a segment, moving to the next/previous segment, returning to an approved segment, editing an approved segment, recovering unsaved work, refreshing the page, restarting the application, completing an entire short transcript, completing part of a long transcript, handling empty or low-confidence segments, handling non-speech audio, handling music/silence/environmental sounds.

### Completion Gate
Phase 4 is complete only after Dean has used the editor for real transcript correction and confirms that the workflow is efficient, understandable, and predictable.

**This is the decision point for the separate AccessibleTranscriptEditor repository.**

## When to Begin AccessibleTranscriptEditor

Begin the separate repository after Phase 4 is proven. Do not wait until the entire VoiceOfOpenDoor application is finished. Do not begin it before real transcript editing has occurred.

The correct point is when: the transcript data model is stable; the segment review workflow works; focus behavior is predictable; playback does not steal focus; saving does not disturb editing; segment approval works; real transcripts have been completed; major interaction problems have been identified and corrected; the interaction model is no longer changing after every test.

At that point, extract the transcript system into a reusable framework. VoiceOfOpenDoor should then consume that framework rather than maintain a private duplicate.

## Phase 5: AccessibleTranscriptEditor Extraction

### Build
Create the separate AccessibleTranscriptEditor repository. Initial contents: README, Design Principles, Interaction Model, Screen Reader Behavior, Focus Management, Transcript Data Model, Keyboard Command Architecture, Screen Reader Editor, Read-only Viewer, Integration guidance, Test transcripts, Automated tests where practical.

The first release should preserve the proven VoiceOfOpenDoor workflow. **Do not redesign everything during extraction.** Extraction should separate and stabilize the working system.

### Test
Test the standalone editor: independently, embedded in VoiceOfOpenDoor, with JAWS and Chrome, with NVDA and Firefox, with keyboard only, with multiple transcript lengths, with saved and restored sessions.

### Completion Gate
Phase 5 is complete when VoiceOfOpenDoor successfully uses the standalone transcript editor without losing functionality or accessibility.

## Phase 6: Corpus Segmentation

### Build
Replace the Segments placeholder. Allow accepted and approved transcript content to be divided into corpus-ready audio clips. Each segment: audio clip, approved transcript, start time, end time, duration, source recording, speaker, quality status, inclusion status, exclusion reason when rejected.

The segmentation workflow should reuse the interaction principles proven in the transcript editor.

### Test
Test: creating segments, adjusting boundaries, playing boundaries, rejecting segments, restoring segments, exporting approved segments, preventing duplicate segment identifiers, preserving transcript and audio synchronization.

### Completion Gate
Phase 6 is complete when a recording can move from accepted audio to an approved set of corpus-ready clips without manual file manipulation.

## Phase 7: Corpus Validation and Export

### Build
Create a corpus validation workflow. Validation should identify: missing transcript text, missing audio files, duplicate identifiers, invalid timestamps, empty clips, excessively short clips, excessively long clips, clipped audio, unsupported formats, inconsistent sample rates, unapproved content, missing speaker information, export conflicts.

Provide an export process for the selected training format.

### Test
Test valid and intentionally damaged corpora.

### Completion Gate
Phase 7 is complete when VoiceOfOpenDoor can produce a validated, repeatable training dataset.

## Phase 8: Training Engine Selection and Integration

### Build
Replace the Train placeholder only after corpus preparation is dependable. Before selecting a training engine: resolve licensing questions, confirm Windows support, confirm local hardware requirements, confirm whether CPU training is practical, confirm GPU requirements, confirm model output ownership, confirm commercial and noncommercial restrictions, confirm maintenance status, confirm accessibility of the installation and operation process.

**Do not lock VoiceOfOpenDoor permanently to one engine.** Create a training provider interface that can support different engines - same pattern as the synthesis engine adapter (`Tools/Synthesis/engines/`).

### Test
Test: environment checks, missing dependencies, training configuration, training start, progress reporting, training interruption, training failure, training completion, model validation, model storage.

### Completion Gate
Phase 8 is complete when VoiceOfOpenDoor can produce and preserve a working voice model through a documented and repeatable process.

## Phase 9: Speech Generation

### Build
Replace the Generate Speech placeholder. Allow the user to: enter or paste text, choose an available trained voice, generate speech, hear progress, play the result, regenerate the result, save the generated file, review generation history.

### Test
Test: short text, long text, punctuation, numbers, acronyms, paragraph breaks, unsupported characters, engine failure, model failure, saving and reopening generated audio.

### Completion Gate
Phase 9 is complete when generated speech can be produced, reviewed, and saved without using command-line tools.

## Phase 10: Settings, Recovery, and Production Readiness

### Build
Replace the Settings placeholder. Settings should report: Python availability, Flask availability, FFmpeg availability, transcription engines, training engines, models, storage locations, corpus location, backup location, application version, environment verification status.

Add: backup, restore, export metadata, import metadata, recovery from interrupted work, clear error reporting, diagnostic reports.

### Final Testing
Complete full workflow testing: launch -> analyze -> classify -> create transcripts -> review transcripts -> create segments -> validate corpus -> train voice -> generate speech -> close and restart -> confirm all work persists.

## Final Principle

VoiceOfOpenDoor should be developed as a chain of complete, usable workflows. Do not build every page partially. Complete and test one workflow before moving to the next.

The immediate development order:
1. Stabilize Recordings.
2. Build Analyze.
3. Prepare the transcript data model and engine detection.
4. Build and test transcript review.
5. Extract AccessibleTranscriptEditor.
6. Build Segments.
7. Validate and export the corpus.
8. Integrate training.
9. Build speech generation.
10. Complete settings, backup, recovery, and production hardening.
