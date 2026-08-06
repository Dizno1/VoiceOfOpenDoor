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

EXTERNAL DATA ARCHITECTURE (Aug 5, 2026): VoiceOfOpenDoor is now
published to GitHub. The repository holds application code only.
All recordings, the manifest, transcripts, segments, and models live
in a user-configured folder outside the repository - see
App/backend/local_data.py and App/local-settings.json (gitignored).
Every route except the setup flow requires a valid, configured data
root; a before_request hook redirects to /setup otherwise. There is
no silent fallback to storing private data inside the repository.

STATUS: Working. Home, Recordings, Analyze, Add Recordings, and the
first-run/change-data-folder/migration flow are real and tested. Every
other item in the Workbench nav (Transcripts, Segments, Train,
Generate Speech) is a real route that renders a real page, but each
currently states plainly that it is not yet built. Settings is now
real too - see below.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # VoiceOfOpenDoor/ (the repository root)
REPO_LEGACY_AUDIO_DIR = BASE_DIR / "Dataset" / "Raw Audio"  # old in-repo location, migration source only

sys.path.insert(0, str(BASE_DIR / "Tools" / "Audio Processing"))
sys.path.insert(0, str(BASE_DIR / "Tools" / "Dataset Utilities"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import analyze_file  # noqa: E402
from build_manifest import natural_duration  # noqa: E402
from analysis_service import run_analysis, analysis_is_stale, summarize_for_display, natural_datetime  # noqa: E402
import local_data  # noqa: E402

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

LOCAL_SETTINGS_PATH = BASE_DIR / "App" / "local-settings.json"
LOCAL_SETTINGS_EXAMPLE_PATH = BASE_DIR / "App" / "local-settings.example.json"
config = local_data.LocalDataConfig(LOCAL_SETTINGS_PATH, LOCAL_SETTINGS_EXAMPLE_PATH)


def get_data_root():
    return config.get_data_root()


def get_audio_dir():
    root = get_data_root()
    return root / "Original Recordings" if root else None


def get_manifest_path():
    root = get_data_root()
    return root / "Metadata" / "recordings.json" if root else None


SETUP_EXEMPT_ENDPOINTS = {
    "setup_page", "setup_confirm", "setup_migrate_page", "setup_migrate_run", "static",
}


@app.before_request
def require_data_root():
    if request.endpoint in SETUP_EXEMPT_ENDPOINTS or request.endpoint is None:
        return
    root = get_data_root()
    status = local_data.validate_data_root(root)
    if not (status["exists"] and status["writable"]):
        return redirect(url_for("setup_page"))


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
BUILT_TOOLS = {"home", "recordings", "analyze", "settings"}
STUB_DESCRIPTIONS = {
    "transcripts": "Will list accepted recordings, generate a draft transcript for each, and let you review it sentence by sentence: play, edit, approve. This is Phase 5, planned next.",
    "segments": "Will let you cut accepted, transcribed recordings into corpus-ready clips.",
    "train": "Will walk through selecting and integrating a voice engine (XTTS v2 is the current candidate - see Documentation/Voice Pipeline Roadmap.md for an unresolved licensing question) and producing a trained voice.",
    "generate-speech": "Will wrap Tools/Synthesis/synthesize.py: type text, generate speech, play it, save the WAV file.",
}


def load_manifest():
    manifest_path = get_manifest_path()
    if manifest_path is None or not manifest_path.exists():
        return []
    try:
        return json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        # Damaged manifest - rebuild from scratch via discovery rather
        # than crash. The source audio files are never touched by this;
        # only the manifest itself is being treated as empty so
        # discovery can repopulate it from what's actually on disk.
        backup_path = manifest_path.with_suffix(".json.damaged")
        try:
            manifest_path.replace(backup_path)
        except OSError:
            pass
        return []


def save_manifest(manifest):
    manifest_path = get_manifest_path()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))


def build_status_summary(manifest):
    active = [r for r in manifest if r.get("status", "Active") != "Archived"]

    workflow_counts = {"Analysis Clear": 0, "Needs Review": 0, "Analysis Failed": 0, "Not Analyzed": 0}
    for r in active:
        workflow_counts[compute_workflow_status(r)] += 1

    return {
        "total": len(active),
        "clear_count": workflow_counts["Analysis Clear"],
        "needs_review_count": workflow_counts["Needs Review"],
        "failed_count": workflow_counts["Analysis Failed"],
        "not_analyzed_count": workflow_counts["Not Analyzed"],
        "needs_attention": workflow_counts["Needs Review"] + workflow_counts["Analysis Failed"],
    }


@app.context_processor
def inject_nav():
    return {"tools": TOOLS}


# ---------------------------------------------------------------------------
# Setup / first-run / change-data-folder / migration
# ---------------------------------------------------------------------------

@app.route("/setup")
def setup_page():
    root = get_data_root()
    status = local_data.validate_data_root(root)
    return render_template(
        "setup.html",
        active="settings",
        current_path=str(root) if root else "",
        status=status,
        is_reconfigure=status["exists"] and status["writable"],
        error_message=request.args.get("error_message"),
    )


@app.route("/setup", methods=["POST"])
def setup_confirm():
    submitted_path = request.form.get("data_root", "").strip()
    if not submitted_path:
        return redirect(url_for("setup_page", error_message="Enter a folder path."))

    create_result = local_data.create_data_root_if_needed(submitted_path)
    if not create_result["created"]:
        return redirect(url_for("setup_page", error_message=create_result["error"]))

    root = create_result["root"]
    status = local_data.validate_data_root(root)
    if not status["writable"]:
        return redirect(url_for("setup_page", error_message=status["error"]))

    local_data.ensure_subfolders(root)
    config.save(str(root))

    # Original Recordings may already have files (a prior session, or
    # manually copied in) - register them now rather than waiting for
    # the next restart to pick them up.
    manifest = load_manifest()
    manifest, scan_results = scan_and_register(get_audio_dir(), manifest)
    if scan_results["added"] or scan_results["damaged"]:
        save_manifest(manifest)

    legacy_files = local_data.find_repo_corpus(REPO_LEGACY_AUDIO_DIR)
    if legacy_files:
        return redirect(url_for("setup_migrate_page"))

    return redirect(url_for("home", status_message="Data folder confirmed."))


@app.route("/setup/migrate")
def setup_migrate_page():
    legacy_files = local_data.find_repo_corpus(REPO_LEGACY_AUDIO_DIR)
    return render_template("setup_migrate.html", active="settings", legacy_files=legacy_files, count=len(legacy_files))


@app.route("/setup/migrate", methods=["POST"])
def setup_migrate_run():
    mode = request.form.get("mode", "skip")
    root = get_data_root()

    if mode == "skip" or root is None:
        return redirect(url_for("home", status_message="Migration skipped."))

    dest_dir = root / "Original Recordings"
    legacy_files = local_data.find_repo_corpus(REPO_LEGACY_AUDIO_DIR)

    results = []
    for f in legacy_files:
        results.append(local_data.migrate_file(f, dest_dir, mode))

    # Migrate the manifest itself (classifications, notes, analysis) -
    # merge into the new location's manifest rather than overwrite it,
    # in case some entries are already there.
    legacy_manifest_path = BASE_DIR / "Dataset" / "Metadata" / "recordings.json"
    if legacy_manifest_path.exists():
        legacy_manifest = json.loads(legacy_manifest_path.read_text())
        new_manifest = load_manifest()
        existing_files = {r["file"] for r in new_manifest}
        for entry in legacy_manifest:
            if entry["file"] not in existing_files:
                new_manifest.append(entry)
        save_manifest(new_manifest)

    return render_template("setup_migrate_results.html", active="settings", results=results, mode=mode)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.route("/settings")
def settings_page():
    root = get_data_root()
    status = local_data.validate_data_root(root)
    counts = local_data.count_data(root) if root else {}
    return render_template(
        "settings.html",
        active="settings",
        data_root=str(root) if root else "Not configured",
        status=status,
        counts=counts,
        status_message=request.args.get("status_message"),
    )


@app.route("/settings/open-folder", methods=["POST"])
def settings_open_folder():
    root = get_data_root()
    if root is None:
        return redirect(url_for("settings_page", status_message="No data folder configured."))
    try:
        if platform.system() == "Windows":
            os.startfile(root)  # noqa: S606 - local desktop app, opening the user's own configured folder
            msg = "Opened the data folder in File Explorer."
        else:
            msg = f"Cannot open a folder window automatically on this platform. The path is: {root}"
    except OSError as exc:
        msg = f"Could not open the folder: {exc}"
    return redirect(url_for("settings_page", status_message=msg))


@app.route("/settings/validate", methods=["POST"])
def settings_validate():
    root = get_data_root()
    status = local_data.validate_data_root(root)
    if status["exists"] and status["writable"]:
        msg = "Data folder is available and writable."
    else:
        msg = f"Problem found: {status['error']}"
    return redirect(url_for("settings_page", status_message=msg))


# ---------------------------------------------------------------------------
# Home / Recordings / Recording detail
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    manifest = load_manifest()
    summary = build_status_summary(manifest)
    return render_template("home.html", summary=summary, active="home",
                            status_message=request.args.get("status_message"))


FILTER_LABELS = {
    "attention": "Recordings With Possible Issues",
    "needs_review": "Needs Review",
    "failed": "Analysis Failed",
    "clear": "No Objective Issues",
}


def _matches_filter(record, filter_name):
    status = compute_workflow_status(record)
    if filter_name == "attention":
        return status in ("Needs Review", "Analysis Failed")
    if filter_name == "needs_review":
        return status == "Needs Review"
    if filter_name == "failed":
        return status == "Analysis Failed"
    if filter_name == "clear":
        return status == "Analysis Clear"
    return True


@app.route("/recordings")
def recordings_screen():
    manifest = load_manifest()
    active_manifest = [r for r in manifest if r.get("status", "Active") != "Archived"]
    archived = [r for r in manifest if r.get("status", "Active") == "Archived"]

    for r in active_manifest:
        r["_workflow_status"] = compute_workflow_status(r)

    filter_name = request.args.get("filter")
    status_message = request.args.get("status_message")
    focus_group = request.args.get("focus_group")

    if filter_name:
        filtered = [r for r in active_manifest if _matches_filter(r, filter_name)]
        return render_template(
            "recordings.html",
            filtered_view=True,
            filter_name=filter_name,
            filter_label=FILTER_LABELS.get(filter_name, "Filtered Recordings"),
            filtered_recordings=filtered,
            archived=archived,
            active="recordings",
            status_message=status_message,
        )

    grouped = {key: [] for key in GROUP_ORDER}
    for r in active_manifest:
        grouped.setdefault(r["classification"], []).append(r)

    # Always render every group, even empty ones, so headings don't
    # appear/disappear as recordings are deleted - keeps navigation
    # predictable and gives the focus-after-delete fix below a stable
    # heading to land on even if a group is emptied out.
    groups = [
        {"key": key, "label": GROUP_LABELS.get(key, key), "recordings": grouped[key]}
        for key in GROUP_ORDER
    ]

    return render_template(
        "recordings.html",
        filtered_view=False,
        groups=groups,
        archived=archived,
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
    audio_dir = get_audio_dir()
    stale = bool(record.get("analysis")) and analysis_is_stale(record["analysis"], audio_dir / filename)
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
        workflow_status=compute_workflow_status(record),
    )


@app.route("/audio/<path:filename>")
def audio_file(filename):
    return send_from_directory(get_audio_dir(), filename)


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


@app.route("/recording/<path:filename>/archive", methods=["POST"])
def toggle_archive(filename):
    manifest = load_manifest()
    record = _find_recording(manifest, filename)
    if record is None:
        abort(404)

    current = record.get("status", "Active")
    record["status"] = "Active" if current == "Archived" else "Archived"
    save_manifest(manifest)
    verb = "restored from archive" if record["status"] == "Active" else "archived"
    return redirect(url_for("recording_detail", filename=filename, status_message=f"Recording {verb}."))


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

    audio_path = get_audio_dir() / filename
    if audio_path.exists():
        audio_path.unlink()

    manifest = [r for r in manifest if r["file"] != filename]
    save_manifest(manifest)

    return redirect(url_for(
        "recordings_screen",
        status_message=f"{filename} was permanently deleted.",
        focus_group=classification,
    ))


# ---------------------------------------------------------------------------
# Add Recordings
# ---------------------------------------------------------------------------

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
    audio_dir = get_audio_dir()
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

        dest_path = audio_dir / original_name
        if dest_path.exists():
            # This is the "selected files from inside Original Recordings
            # itself" case - the file is already exactly where it needs
            # to be. Don't attempt to copy it onto itself; point at the
            # feature built for exactly this.
            results["skipped"].append({"file": original_name, "reason": "This file is already in Original Recordings. Use Scan Existing Recordings (on the Recordings page or Settings) to register it instead of Add Recordings."})
            continue

        # Save to a temp name first so a failed/damaged file never lands
        # in the real corpus folder under its final name.
        temp_path = audio_dir / f".importing-{original_name}"
        try:
            upload.save(temp_path)
        except Exception as exc:  # noqa: BLE001
            results["failed"].append({"file": original_name, "reason": f"Could not save the uploaded file: {exc}"})
            continue

        if existing_checksums is None:
            existing_checksums = {_file_sha256(audio_dir / r["file"]): r["file"] for r in manifest if (audio_dir / r["file"]).exists()}

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

        # Analyze again at the final path (not temp_path) so the stored
        # source_mtime used for staleness detection refers to where the
        # file actually lives, not a path that no longer exists.
        analysis_record = run_analysis(dest_path)

        entry = {
            "file": original_name,
            "duration_natural": analysis_record.get("duration_natural") or natural_duration(analysis.get("duration_seconds", 0)),
            "duration_seconds": analysis.get("duration_seconds"),
            "classification": "Evaluation Only",
            "status": "Active",
            "note": f"Imported via Add Recordings on {datetime.now().strftime('%Y-%m-%d')}. Not yet reviewed.",
            "user_notes": "",
            "objective_flags": analysis.get("flags", []),
            "analysis": analysis_record,
        }
        manifest.append(entry)
        results["imported"].append(original_name)

    if results["imported"]:
        save_manifest(manifest)

    return render_template("import_results.html", results=results, active="recordings")


# ---------------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------------

def _needs_analysis(record):
    analysis = record.get("analysis")
    if analysis is None:
        return True
    if analysis.get("status") == "failed":
        return True
    audio_path = get_audio_dir() / record["file"]
    return analysis_is_stale(analysis, audio_path)


@app.route("/analyze")
def analyze_page():
    manifest = load_manifest()
    audio_dir = get_audio_dir()

    needing = [r for r in manifest if _needs_analysis(r)]
    analyzed = [r for r in manifest if not _needs_analysis(r) and r.get("analysis")]
    stale = [r for r in needing if r.get("analysis") and analysis_is_stale(r["analysis"], audio_dir / r["file"])]

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
    audio_dir = get_audio_dir()

    action = request.form.get("action", "")

    if action == "all_needing":
        targets = [f for f, r in by_file.items() if _needs_analysis(r)]
    elif action.startswith("group:"):
        group = action.split(":", 1)[1]
        targets = [f for f, r in by_file.items() if r["classification"] == group and _needs_analysis(r)]
    elif action == "stale":
        targets = [f for f, r in by_file.items() if r.get("analysis") and analysis_is_stale(r["analysis"], audio_dir / f)]
    elif action == "selected":
        targets = [f for f in request.form.getlist("selected_files") if f in by_file]
    elif action == "reanalyze_selected":
        targets = [f for f in request.form.getlist("reanalyze_files") if f in by_file]
    else:
        abort(400)

    results = {"analyzed": [], "failed": []}
    for filename in targets:
        record = by_file[filename]
        analysis = run_analysis(audio_dir / filename)
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


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".aac"}

# Workflow status is a separate axis from the human `classification`
# field - it never gets set to "Candidate" or similar just because
# analysis found nothing wrong (that's a human judgment, not an
# automatic one). Only these specific, analyzer-supported findings
# put a recording in the Needs Review queue - not just any flag text
# (e.g. the low-bitrate flag is real and useful, but isn't one of the
# categories Dean specified, so it doesn't by itself trigger Needs
# Review).
NEEDS_REVIEW_FLAG_MARKERS = [
    "ceiling",  # clipping / near-clipping
    "Low mean volume",  # unusually low level
    "Excessive silence",
    "Unusual channel configuration",
]


def compute_workflow_status(record):
    """
    Analysis Clear / Needs Review / Analysis Failed / Not Analyzed -
    computed fresh from the stored analysis every time, not cached on
    the record, so it can never drift out of sync with the analysis
    it's supposed to describe.
    """
    analysis = record.get("analysis")
    if analysis is None:
        return "Not Analyzed"
    if analysis.get("status") == "failed":
        return "Analysis Failed"
    flags = analysis.get("objective_flags") or []
    for flag in flags:
        if any(marker in flag for marker in NEEDS_REVIEW_FLAG_MARKERS):
            return "Needs Review"
    return "Analysis Clear"


def scan_and_register(audio_dir, manifest):
    """
    Scan audio_dir for audio files not represented in manifest, analyze
    and register the valid ones. Original Recordings is treated as the
    authoritative source - files found there always win over an empty
    or out-of-date manifest. Never raises; every file either succeeds
    or is reported with a specific reason, and one bad file never stops
    the rest from being processed. Files are never copied, moved,
    renamed, or altered by this function - only read and recorded.

    Returns (updated_manifest, results). Caller is responsible for
    saving the manifest if results["added"] is non-empty.
    """
    results = {"found": 0, "added": [], "already_registered": 0, "unsupported": [], "damaged": [], "failed": [],
               "added_clear": 0, "added_needs_review": 0}

    if audio_dir is None or not audio_dir.exists():
        return manifest, results

    registered_names = {r["file"] for r in manifest}
    # Content hashes of already-registered files still present on disk,
    # so a file that's actually a duplicate under a different name is
    # recognized as already registered rather than added a second time.
    registered_checksums = {}
    for r in manifest:
        p = audio_dir / r["file"]
        if p.exists():
            try:
                registered_checksums[_file_sha256(p)] = r["file"]
            except OSError:
                pass

    try:
        candidate_files = sorted(f for f in audio_dir.iterdir() if f.is_file() and not f.name.startswith("."))
    except OSError as exc:
        results["failed"].append({"file": "(folder)", "reason": f"Could not list Original Recordings: {exc}"})
        return manifest, results

    for f in candidate_files:
        results["found"] += 1
        suffix = f.suffix.lower()

        if f.name in registered_names:
            results["already_registered"] += 1
            continue

        if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
            results["unsupported"].append({"file": f.name, "reason": f"Unsupported file type ({suffix or 'no extension'})."})
            continue

        try:
            checksum = _file_sha256(f)
        except OSError as exc:
            results["failed"].append({"file": f.name, "reason": f"Could not read file: {exc}"})
            continue

        if checksum in registered_checksums:
            results["already_registered"] += 1
            continue

        try:
            analysis = run_analysis(f)
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the scan
            results["failed"].append({"file": f.name, "reason": f"Analysis failed unexpectedly: {exc}"})
            continue

        if analysis["status"] != "analyzed":
            # Register it anyway, with the failed analysis attached - a
            # damaged file physically present in Original Recordings
            # must be discoverable (Home's tally, the Recordings
            # "failed" filter) or the user has no way to learn about it
            # again except by re-reading a startup console line or
            # re-running a manual scan. Still reported in the scan
            # results as "damaged" too, so that report stays accurate.
            entry = {
                "file": f.name,
                "duration_natural": "unknown duration",
                "duration_seconds": None,
                "classification": "Evaluation Only",
                "status": "Active",
                "note": f"Discovered already present in Original Recordings (registered {datetime.now().strftime('%Y-%m-%d')}). Analysis failed - see Analysis section for details.",
                "user_notes": "",
                "objective_flags": [],
                "analysis": analysis,
            }
            manifest.append(entry)
            registered_names.add(f.name)
            results["damaged"].append({"file": f.name, "reason": analysis.get("error", "Unknown error")})
            continue

        entry = {
            "file": f.name,
            "duration_natural": analysis.get("duration_natural") or natural_duration(analysis.get("duration_seconds", 0)),
            "duration_seconds": analysis.get("duration_seconds"),
            "classification": "Evaluation Only",
            "status": "Active",
            "note": f"Discovered already present in Original Recordings (registered {datetime.now().strftime('%Y-%m-%d')}). Not yet reviewed.",
            "user_notes": "",
            "objective_flags": analysis.get("objective_flags", []),
            # Analyzed immediately as part of registration, per the
            # analysis-first workflow - reuses this same run_analysis()
            # call rather than analyzing the file twice.
            "analysis": analysis,
        }
        manifest.append(entry)
        registered_names.add(f.name)
        registered_checksums[checksum] = f.name
        results["added"].append(f.name)
        if compute_workflow_status(entry) == "Needs Review":
            results["added_needs_review"] += 1
        else:
            results["added_clear"] += 1

    return manifest, results


@app.route("/recordings/scan", methods=["POST"])
def scan_recordings():
    manifest = load_manifest()
    manifest, results = scan_and_register(get_audio_dir(), manifest)
    if results["added"] or results["damaged"]:
        save_manifest(manifest)
    results["failed_analysis_count"] = len(results["damaged"])
    return render_template("scan_results.html", active="recordings", results=results)


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


def _run_startup_discovery():
    """
    Runs once when this module is imported - by `python app.py`
    directly, or by launch.py's `from app import app`. Not inside
    `if __name__ == "__main__"`, since that block never runs on the
    launch.py path. Original Recordings is authoritative: if a valid
    data root is already configured (the normal restart case), any
    audio files sitting there with no manifest entry are registered
    AND analyzed before the server starts accepting requests, so the
    first page Dean sees already reflects the analysis-first workflow -
    no in-page "scanning" progress UI needed, since nothing has been
    served yet to move focus on. Console output is a short fixed
    sequence, not one line per file.
    """
    root = get_data_root()
    status = local_data.validate_data_root(root)
    if not (status["exists"] and status["writable"]):
        return

    print("Scanning local recordings...")

    audio_dir = get_audio_dir()
    manifest = load_manifest()
    registered = {r["file"] for r in manifest}
    try:
        candidate_count = sum(
            1 for f in audio_dir.iterdir()
            if f.is_file() and not f.name.startswith(".") and f.name not in registered
        ) if audio_dir and audio_dir.exists() else 0
    except OSError:
        candidate_count = 0

    if candidate_count:
        print(f"Analyzing {candidate_count} new recording{'s' if candidate_count != 1 else ''}...")

    manifest, results = scan_and_register(audio_dir, manifest)
    if results["added"] or results["damaged"]:
        save_manifest(manifest)

    if results["added"] or results["damaged"] or results["unsupported"]:
        failed_count = len(results["damaged"])
        unsupported_count = len(results["unsupported"])
        unsupported_note = f" ({unsupported_count} unsupported file(s) skipped)" if unsupported_count else ""
        print(f"Analysis complete: {results['added_clear']} clear, {results['added_needs_review']} need review, {failed_count} failed{unsupported_note}.")
    else:
        print(f"Scan complete: {results['already_registered']} recording(s) already registered, nothing new found.")


_run_startup_discovery()


if __name__ == "__main__":
    app.run(debug=True)
