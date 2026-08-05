# Transcript Editing Design Principles

Written before any transcript editor code, deliberately. These are principles, not implementation details — the contract every feature gets checked against, not a spec to build from directly.

## Origin

Developed across a conversation between Dean, Chap (ChatGPT), and Claude on July 28-29, 2026. Not a Claude-only or Chap-only design — credited jointly because it was reasoned out jointly, and because the repository's own standard is to record decisions, not which assistant said them.

## The Core Reframe

Most transcript editors start from the data structure — a table of Start / Transcript / End rows — because that's what a caption file looks like. That produces an editing experience built around rows, which is exactly why so many transcript editors feel awkward with a screen reader: the unit on screen is a row, but the unit in a person's head is a sentence they're currently listening to.

This project starts from the task instead: *how does someone efficiently correct a transcript by ear and keyboard, from focus to approval, without losing their place?* The visual/table view is a legitimate and useful interface for the same underlying data — but it's a second interface built on the same model, not the model itself.

## Principles

1. **The transcript is the workspace.** The unit of work is a segment - a sentence someone is currently listening to and correcting - not a row in a table.

2. **One data model, multiple purpose-built interfaces.** The screen-reader-first editor and a future visual/table view both read and write the same underlying segment data. Neither is the "real" one; they're adapted to different ways of working with the same material. (Precedent already exists in this repository: `Dataset/Metadata/recordings.json` is read by three different screens today.)

3. **Focus remains where the user is working.** The application never steals focus. Playback never moves keyboard focus away from the control the user is using.

4. **Commands act on the object with current focus.** A timing adjustment on the start boundary adjusts the start; the same key on the end boundary adjusts the end; the same category of command inside the transcript text edits the text. This minimizes how much a user has to memorize, because behavior follows a single rule instead of a list of arbitrary bindings.

5. **Context-sensitive shortcuts must be discoverable.** One key (not a global cheat sheet) announces only the shortcuts valid for whatever currently has focus.

6. **The interface minimizes unnecessary speech.** Results are announced only after a deliberate action - never continuous status chatter during playback or idle time.

7. **Reversible actions are silent and instant; irreversible actions always confirm.** Nudging a boundary or correcting a word needs no confirmation - it's cheap to undo. Deleting a recording or discarding a segment always requires an explicit confirmation step. (Precedent: this is exactly how recording classification vs. recording deletion already behave in the App today - this principle names that distinction so future features don't have to guess which category they're in.)

8. **Approve-and-advance is a single action.** Once a reviewer is in a rhythm across a run of clean segments, moving to the next one after approving should be one keystroke, not a full tab through play/approve/next each time.

9. **Progress is always answerable in one sentence.** "Segment 4 of 12" as part of the existing heading, not a separate status field someone has to seek out.

10. **Browse mode and focus mode are both supported; production work is optimized for focus/direct interaction.** A screen reader user isn't forced through a purely visual workflow to get real editing work done.

11. **Keyboard-first does not mean screen-reader-only.** The same fast, predictable interaction model should be equally strong for a sighted keyboard user, someone with an RSI, or anyone who prefers not to use a mouse. The design is defined by what it does, not who it's "for."

12. **The application adapts to the editing task, not the other way around.** Build the screen-reader-first interaction model first. Do not build a conventional spreadsheet/timeline editor and attempt to retrofit accessibility onto it afterward.

## Build-Order Note

This document governs the eventual Transcripts screen in the VoiceOfOpenDoor App (Phase 5/App nav). It should be built as a real, working editor for VoiceOfOpenDoor's own segments first - a single real consumer - with clean module boundaries as ordinary engineering hygiene, not as a generalized public framework from day one. Whether to extract it into its own repository (an "Accessible Transcript Editor" or similar) is a separate, later decision, made once these principles have been proven against real editing work rather than designed in the abstract.

Per Dean's standing instruction (July 28, 2026): this document does not itself authorize starting the Transcripts screen. That remains on hold until the Recordings/detail page fixes are confirmed via a fresh JAWS test.
