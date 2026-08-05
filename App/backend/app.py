"""
VoiceOfOpenDoor - App backend.

Local, Windows-first web application, following the same pattern as
Open Door Design's other apps (vanilla HTML/CSS/JS, served locally,
tested directly against JAWS/NVDA). This is the "Voice Engineering
Workbench" - not a set of CLI phases, but tools a person actually uses.

Launch model (Option C, per Dean/Chap's discussion): a desktop-style
launcher (launch.py, or a .bat shortcut calling it) starts this local
server and opens the default browser automatically - no terminal
command required to use the app day to day. Running `python app.py`
directly (as below) is still supported for development, with the
Flask debug reloader on.

STATUS: Working. Home (/) and Recordings (/recordings, /recording/<file>)
are real and tested against the actual manifest and corpus - including
Add Recordings, which changes the count as files are imported. Every
other item in the Workbench nav (Analyze, Transcripts,
Segments, Train, Generate Speech, Settings) is a real route that
renders a real page, but each currently states plainly that it is not
yet built rather than faking functionality - see TOOLS below.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # VoiceOfOpenDoor/
MANIFEST_PATH = BASE_DIR / "Dataset" / "Metadata" / "recordings.json"
AUDIO_DIR = BASE_DIR / "Dataset" / "Raw Audio"

sys.path.insert(0, str(BASE_DIR / "Tools" / "Audio Processing"))
sys.path.insert(0, str(BASE_DIR / "Tools" / "Dataset Utilities"))
from analyze import analyze_file  # noqa: E402
from build_manifest import natural_duration  # noqa: E402
from analysis_service import run_analysis, analysis_is_stale, summarize_for_display, natural_datetime  # noqa: E402

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

CLASSIFICATION_OPTIONS = [
    "Candidate",
    "Conditional Candidate",
    "Evaluation Only",
    "Rejected",
    "Not Yet Classified",
]

GROUP_ORDER = ["Candidate", "Conditional Candidate", "Evaluation Only", "Rejected", "Not Yet Classified"]
GROUP_LABELS = {
    "Candidate": "Candidates",
    "Conditional Candidate": "Conditional Candidates",
    "Evaluation Only": "Evaluation Only - Needs Review",
    "Rejected": "Rejected",
    "Not Yet Classified": "Not Yet Classified",
}
# Labels for the summary count sentence, e.g. "5 marked Evaluation Only"
COUNT_LABELS = {
    "Candidate": "Candidate",
    "Conditional Candidate": "Conditional Candidate",
    "Evaluation Only": "marked Evaluation Only",
    "Rejected": "Rejected",
    "Not Yet Classified": "not yet classified",
}

# The Workbench nav - the minimum lovable product skeleton. Every entry
# is a real route; entries not yet in BUILT_TOOLS render an honest
# "not yet built" page instead of faking functionality.
TOOLS = [
    ("home", "Home", "/"),
    ("recordings", "Recordings", "/recordings"),
    ("analyze", "Analyze", "/analyze"),
    ("transcripts", "Transcripts", "/transcripts"),
    ("segments", "Segments", "/segments"),
    ("train", "Train", "/train"),
    ("generate-speech", "Generate Speech", "/generate-speech"),
    ("settings", "Settings", "/settings"),
]
BUILT_TOOLS = {"home", "recordings", "analyze"}
STUB_DESCRIPTIONS = {
    "transcripts": "Will list accepted recordings, generate a draft transcript for each, and let you review it sentence by sentence: play, edit, approve. This is Phase 5, planned next.",
    "segments": "Will let you cut accepted, transcribed recordings into corpus-ready clips.",
    "train": "Will walk through selecting and integrating a voice engine (XTTS v2 is the current candidate - see Documentation/Voice Pipeline Roadmap.md for an unresolved licensing question) and producing a trained voice.",
    "generate-speech": "Will wrap Tools/Synthesis/synthesize.py: type text, generate speech, play it, save the WAV file.",
    "settings": "Will show the reference development environment and let you confirm which pipeline tools are verified on this machine.",
}


def load_manifest():
    if not MANIFEST_PATH.exists():
        return []
    return json.loads(MANIFEST_PATH.read_text())


def save_manifest(manifest):
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def build_status_summary(manifest):
    counts = {}
    for r in manifest:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1

    next_action = None
    for r in manifest:
        if r["classification"] == "Evaluation Only":
            next_action = r
            break

    return {
        "total": len(manifest),
        "counts": counts,
        "next_action": next_action,
    }


@app.context_processor
def inject_nav():
    return {"tools": TOOLS}


@app.route("/")
def home():
    manifest = load_manifest()
    summary = build_status_summary(manifest)
    return render_template("home.html", summary=summary, count_labels=COUNT_LABELS, active="home")


@app.route("/recordings")
def recordings_screen():
    manifest = load_manifest()

    grouped = {key: [] for key in GROUP_ORDER}
    for r in manifest:
        grouped.setdefault(r["classification"], []).append(r)

    # Always render every group, even empty ones, so headings don't
    # appear/disappear as recordings are deleted - keeps navigation
    # predictable and gives the focus-after-delete fix below a stable
    # heading to land on even if a group is emptied out.
    groups = [
        {"key": key, "label": GROUP_LABELS.get(key, key), "recordings": grouped[key]}
        for key in GROUP_ORDER
    ]

    status_message = request.args.get("status_message")
    focus_group = request.args.get("focus_group")
    return render_template(
        "recordings.html",
        groups=groups,
        active="recordings",
        status_message=status_message,
        focus_group=focus_group,
    )


def _find_recording(manifest, filename):
    return next((r for r in manifest if r["file"] == filename), None)


@app.route("/recording/<path:filename>")
def recording_detail(filename):
    manifest = load_manifest()
    record = _find_recording(manifest, filename)
    if record is None:
        abort(404)
    status_message = request.args.get("status_message")
    stale = bool(record.get("analysis")) and analysis_is_stale(record["analysis"], AUDIO_DIR / filename)
    analyzed_at_natural = None
    if record.get("analysis") and record["analysis"].get("analyzed_at"):
        analyzed_at_natural = natural_datetime(record["analysis"]["analyzed_at"])
    return render_template(
        "recording_detail.html",
        r=record,
        active="recordings",
        classification_options=CLASSIFICATION_OPTIONS,
        status_message=status_message,
        analysis_stale=stale,
        analyzed_at_natural=analyzed_at_natural,
    )


@app.route("/audio/<path:filename>")
def audio_file(filename):
    return send_from_directory(AUDIO_DIR, filename)


@app.route("/recording/<path:filename>/classification", methods=["POST"])
def update_classification(filename):
    manifest = load_manifest()
    record = _find_recording(manifest, filename)
    if record is None:
        abort(404)

    new_classification = request.form.get("classification")
    if new_classification not in CLASSIFICATION_OPTIONS:
        abort(400)

    record["classification"] = new_classification
    save_manifest(manifest)
    return redirect(url_for("recording_detail", filename=filename, status_message=f"Classification updated to {new_classification}."))


@app.route("/recording/<path:filename>/notes", methods=["POST"])
def update_notes(filename):
    manifest = load_manifest()
    record = _find_recording(manifest, filename)
    if record is None:
        abort(404)

    record["user_notes"] = request.form.get("user_notes", "")
    save_manifest(manifest)
    return redirect(url_for("recording_detail", filename=filename, status_message="Notes saved."))


@app.route("/recording/<path:filename>/delete/confirm")
def delete_confirm(filename):
    manifest = load_manifest()
    record = _find_recording(manifest, filename)
    if record is None:
        abort(404)
    return render_template("delete_confirm.html", filename=filename, classification=record["classification"], active="recordings")


@app.route("/recording/<path:filename>/delete", methods=["POST"])
def delete_recording(filename):
    manifest = load_manifest()
    record = _find_recording(manifest, filename)
    if record is None:
        abort(404)

    classification = record["classification"]

    audio_path = AUDIO_DIR / filename
    if audio_path.exists():
        audio_path.unlink()

    manifest = [r for r in manifest if r["file"] != filename]
    save_manifest(manifest)

    return redirect(url_for(
        "recordings_screen",
        status_message=f"{filename} was permanently deleted.",
        focus_group=classification,
    ))


SUPPORTED_IMPORT_EXTENSIONS = {".wav", ".mp3", ".m4a"}
# .mov and other video containers are not supported yet - would need
# audio-track extraction, which isn't built. Rejected with a specific
# reason below rather than silently accepted or vaguely refused.


def _file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@app.route("/recordings/import")
def import_recordings_form():
    return render_template("import.html", active="recordings")


@app.route("/recordings/import", methods=["POST"])
def import_recordings():
    uploaded_files = request.files.getlist("audio_files")
    manifest = load_manifest()
    existing_filenames = {r["file"] for r in manifest}

    results = {"imported": [], "skipped": [], "failed": []}

    # Existing-file checksums are only computed if we actually need to
    # compare against them (i.e. once a file has passed the cheaper
    # filename/extension checks), to avoid hashing the whole corpus on
    # every import when nothing was actually uploaded.
    existing_checksums = None

    for upload in uploaded_files:
        if not upload or not upload.filename:
            continue

        # Folder selection (webkitdirectory) reports each file's name as
        # a relative path like "FolderName/file.mp3" - the corpus is a
        # flat structure, so only the base filename is used, both for
        # storage and for duplicate detection.
        original_name = Path(upload.filename).name
        suffix = Path(original_name).suffix.lower()

        if suffix not in SUPPORTED_IMPORT_EXTENSIONS:
            reason = f"Unsupported file type ({suffix or 'no extension'}). Supported: {', '.join(sorted(SUPPORTED_IMPORT_EXTENSIONS))}."
            if suffix == ".mov":
                reason = "Video files (.mov) are not supported yet - audio-track extraction hasn't been built."
            results["skipped"].append({"file": original_name, "reason": reason})
            continue

        if original_name in existing_filenames:
            results["skipped"].append({"file": original_name, "reason": "Duplicate filename - a recording with this exact name is already in the corpus."})
            continue

        dest_path = AUDIO_DIR / original_name
        if dest_path.exists():
            # Shouldn't happen if the manifest and disk agree, but don't
            # silently overwrite either way.
            results["skipped"].append({"file": original_name, "reason": "A file with this name already exists on disk, even though it wasn't in the manifest. Not overwritten."})
            continue

        # Save to a temp name first so a failed/damaged file never lands
        # in the real corpus folder under its final name.
        temp_path = AUDIO_DIR / f".importing-{original_name}"
        try:
            upload.save(temp_path)
        except Exception as exc:  # noqa: BLE001
            results["failed"].append({"file": original_name, "reason": f"Could not save the uploaded file: {exc}"})
            continue

        if existing_checksums is None:
            existing_checksums = {_file_sha256(AUDIO_DIR / r["file"]): r["file"] for r in manifest if (AUDIO_DIR / r["file"]).exists()}

        new_checksum = _file_sha256(temp_path)
        if new_checksum in existing_checksums:
            temp_path.unlink()
            results["skipped"].append({"file": original_name, "reason": f"Duplicate content - matches the audio already in the corpus as {existing_checksums[new_checksum]}."})
            continue

        analysis = analyze_file(temp_path)
        # ffprobe doesn't always raise/error on a non-audio or corrupt
        # file - it can return valid JSON with no audio stream found at
        # all (codec/duration missing or zero). Both cases mean the
        # file isn't usable, not just an explicit "error" key.
        if "error" in analysis or not analysis.get("codec") or not analysis.get("duration_seconds"):
            temp_path.unlink()
            reason = analysis.get("error") or "No readable audio stream was found - the file may be damaged, empty, or not actually an audio file despite its extension."
            results["failed"].append({"file": original_name, "reason": reason})
            continue

        temp_path.rename(dest_path)
        existing_checksums[new_checksum] = original_name
        existing_filenames.add(original_name)

        entry = {
            "file": original_name,
            "duration_natural": natural_duration(analysis.get("duration_seconds", 0)),
            "duration_seconds": analysis.get("duration_seconds"),
            "classification": "Evaluation Only",
            "note": f"Imported via Add Recordings on {datetime.now().strftime('%Y-%m-%d')}. Not yet reviewed.",
            "user_notes": "",
            "objective_flags": analysis.get("flags", []),
        }
        manifest.append(entry)
        results["imported"].append(original_name)

    if results["imported"]:
        save_manifest(manifest)

    return render_template("import_results.html", results=results, active="recordings")


def _needs_analysis(record):
    analysis = record.get("analysis")
    if analysis is None:
        return True
    if analysis.get("status") == "failed":
        return True
    audio_path = AUDIO_DIR / record["file"]
    return analysis_is_stale(analysis, audio_path)


@app.route("/analyze")
def analyze_page():
    manifest = load_manifest()

    needing = [r for r in manifest if _needs_analysis(r)]
    analyzed = [r for r in manifest if not _needs_analysis(r) and r.get("analysis")]
    stale = [r for r in needing if r.get("analysis") and analysis_is_stale(r["analysis"], AUDIO_DIR / r["file"])]

    needing_groups = {key: [] for key in GROUP_ORDER}
    for r in needing:
        needing_groups.setdefault(r["classification"], []).append(r)
    needing_groups_list = [
        {"key": key, "label": GROUP_LABELS.get(key, key), "recordings": needing_groups[key]}
        for key in GROUP_ORDER
        if needing_groups.get(key)
    ]

    for r in manifest:
        r["_summary"] = summarize_for_display(r.get("analysis"))

    status_message = request.args.get("status_message")
    return render_template(
        "analyze.html",
        active="analyze",
        total=len(manifest),
        needing_count=len(needing),
        analyzed_count=len(analyzed),
        stale_count=len(stale),
        needing_groups=needing_groups_list,
        analyzed=analyzed,
        status_message=status_message,
    )


@app.route("/analyze/run", methods=["POST"])
def analyze_run():
    manifest = load_manifest()
    by_file = {r["file"]: r for r in manifest}

    action = request.form.get("action", "")

    if action == "all_needing":
        targets = [f for f, r in by_file.items() if _needs_analysis(r)]
    elif action.startswith("group:"):
        group = action.split(":", 1)[1]
        targets = [f for f, r in by_file.items() if r["classification"] == group and _needs_analysis(r)]
    elif action == "stale":
        targets = [f for f, r in by_file.items() if r.get("analysis") and analysis_is_stale(r["analysis"], AUDIO_DIR / f)]
    elif action == "selected":
        targets = [f for f in request.form.getlist("selected_files") if f in by_file]
    elif action == "reanalyze_selected":
        targets = [f for f in request.form.getlist("reanalyze_files") if f in by_file]
    else:
        abort(400)

    results = {"analyzed": [], "failed": []}
    for filename in targets:
        record = by_file[filename]
        analysis = run_analysis(AUDIO_DIR / filename)
        record["analysis"] = analysis
        if analysis["status"] == "analyzed":
            results["analyzed"].append(filename)
        else:
            results["failed"].append({"file": filename, "reason": analysis.get("error", "Unknown error")})

    save_manifest(manifest)

    if request.form.get("return_to") == "detail" and len(targets) == 1:
        filename = targets[0]
        if results["analyzed"]:
            msg = f"Analysis complete for {filename}."
        else:
            msg = f"Analysis failed for {filename}: {results['failed'][0]['reason']}"
        return redirect(url_for("recording_detail", filename=filename, status_message=msg))

    return render_template("analyze_results.html", active="analyze", results=results, target_count=len(targets))


def _register_stub(slug, label):
    def view():
        return render_template(
            "stub.html",
            tool_label=label,
            description=STUB_DESCRIPTIONS.get(slug, "Not yet built."),
            active=slug,
        )
    view.__name__ = f"stub_{slug}"
    return view


for slug, label, path in TOOLS:
    if slug not in BUILT_TOOLS:
        app.add_url_rule(path, endpoint=slug, view_func=_register_stub(slug, label))


if __name__ == "__main__":
    app.run(debug=True)

