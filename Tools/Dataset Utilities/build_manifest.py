#!/usr/bin/env python3
"""
VoiceOfOpenDoor - Build the recordings manifest.

Combines the objective per-file report from Tools/Audio Processing/analyze.py
with the classification each recording was given in Recording Assessment
v1/v2, into one structured file: Dataset/Metadata/recordings.json.

This manifest is the single source of truth the application reads from.
It exists because right now the classifications only live as prose in
the Documentation/ assessment files, which a program can't reliably
parse. Going forward, new assessments should update this manifest
directly (and the prose documents should summarize it), not the other
way around - see the note in README.md "Next Steps" for this file.

STATUS: Working. Run and verified against the real 20-file corpus,
July 28, 2026 (Linux sandbox; requires only Python + the analyze.py
report, no ML/network dependency, so it should run unmodified on
Windows).

Usage:
    python build_manifest.py --analyze-report <path to analyze.py JSON output> --out <path>
"""

import argparse
import json
from pathlib import Path

# Classification data transcribed from Documentation/Recording Assessment
# v1.md and v2.md. This is the one place it's manually maintained until
# the assessment documents are generated from this manifest instead.
CLASSIFICATIONS = {
    # v1 - Strong Technical Candidates
    "Editedaudio1303953228.m4a": ("Candidate", "Strong technical candidate (Assessment v1)."),
    "Editedaudio1655457179.m4a": ("Candidate", "Strong technical candidate (Assessment v1)."),
    "Editedaudio2013336627.m4a": ("Candidate", "Strong technical candidate (Assessment v1)."),
    "Editedaudio2303953228.m4a": ("Candidate", "Strong technical candidate (Assessment v1)."),
    # v1 - Usable After Cleanup
    "EditedSection 508-Submit An Issue August 26 2024-audio.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    "Editedaudio1105962106.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    "Editedaudio1286992121.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    "Editedaudio1377890889.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    "Editedaudio1467666570.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    "Editedaudio1521603543.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    "Editedaudio1559462767.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    "Editedaudio1961666103.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    "UnscriptedRecordingsForTTS.m4a": ("Conditional Candidate", "Usable after cleanup (Assessment v1)."),
    # v1 - Requires Listening Review (still pending as of this writing)
    "Editedaudio1407063783.m4a": ("Evaluation Only", "Peak level near maximum - audible distortion not yet confirmed by ear."),
    "Editedaudio1948085081.m4a": ("Evaluation Only", "Comparatively weaker estimated SNR - not yet listened for room noise."),
    "Editedaudio2655457179.m4a": ("Evaluation Only", "Comparatively lower estimated SNR - not yet listened for background/room tone."),
    # v2 - new recordings
    "RecUpVoiceOfOpenDoorTest.mp3": ("Candidate", "Natural conversational speech, consistent level, no disqualifying noise. Longest recording in the corpus - requires segmentation before training (Assessment v2)."),
    "RecUpAppTest Recording.mp3": ("Rejected", "Audible radio in background (Assessment v2)."),
    "VictorStreamTestNoHeadPhones.mp3": ("Evaluation Only", "Purpose not yet confirmed - suspected Victor Reader Stream recording-method comparison (Assessment v2)."),
    "VRStreamHeadphone.mp3": ("Evaluation Only", "Purpose not yet confirmed - suspected Victor Reader Stream recording-method comparison (Assessment v2)."),
}


def natural_duration(seconds: float) -> str:
    """Convert seconds to natural language, e.g. '6 minutes 31 seconds'."""
    total = round(seconds)
    minutes, secs = divmod(total, 60)
    parts = []
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs or not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    return " ".join(parts)


def build_manifest(analyze_report_path: Path, existing_manifest_path: Path = None) -> list:
    report = json.loads(analyze_report_path.read_text())

    existing_by_file = {}
    if existing_manifest_path and existing_manifest_path.exists():
        for entry in json.loads(existing_manifest_path.read_text()):
            existing_by_file[entry["file"]] = entry

    manifest = []
    for entry in report:
        filename = entry["file"]
        existing = existing_by_file.get(filename)

        if existing:
            # The manifest is the source of truth once a recording has
            # been touched through the app - don't clobber a
            # classification change or notes someone made there.
            classification = existing.get("classification")
            note = existing.get("note")
            user_notes = existing.get("user_notes", "")
            analysis = existing.get("analysis")
            status = existing.get("status", "Active")
        else:
            classification, note = CLASSIFICATIONS.get(
                filename, ("Not Yet Classified", "No assessment entry found for this file.")
            )
            user_notes = ""
            analysis = None
            status = "Active"

        manifest.append({
            "file": filename,
            "duration_natural": natural_duration(entry.get("duration_seconds", 0)),
            "duration_seconds": entry.get("duration_seconds"),
            "classification": classification,
            "status": status,
            "note": note,
            "user_notes": user_notes,
            "objective_flags": entry.get("flags", []),
            "analysis": analysis,
        })
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Build the VoiceOfOpenDoor recordings manifest")
    parser.add_argument("--analyze-report", required=True, help="Path to analyze.py's JSON output")
    parser.add_argument("--out", required=True, help="Where to write the manifest JSON")
    args = parser.parse_args()

    out_path = Path(args.out)
    manifest = build_manifest(Path(args.analyze_report), existing_manifest_path=out_path)
    out_path.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote manifest for {len(manifest)} recording(s) to {args.out}")


if __name__ == "__main__":
    main()
