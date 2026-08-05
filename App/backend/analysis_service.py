"""
VoiceOfOpenDoor - Analysis service.

The application service/adapter the production directive asked for:
the single place the App calls into Tools/Audio Processing/analyze.py,
so the command-line tool and the App workflow share one analysis
implementation rather than becoming two unrelated ones.

STATUS: Working. Wraps the real analyze_file() function - does not
reimplement any analysis logic. Every result stored in the manifest
comes from this module calling that function.
"""

import time
from datetime import datetime, timezone
from pathlib import Path

from analyze import analyze_file, ANALYZER_VERSION  # noqa: E402 - Tools/Audio Processing on sys.path
from build_manifest import natural_duration  # noqa: E402 - Tools/Dataset Utilities on sys.path


def natural_datetime(iso_string: str) -> str:
    """Format an ISO timestamp as natural language, e.g. 'August 5, 2026 at 6:04 PM'.
    Never expose a raw ISO/digit timestamp in the UI - screen readers
    read those as an unbroken string of digits, not a date.
    Built without %-I / %#I strftime flags - those are platform-specific
    (Linux vs Windows) and this must run correctly on Windows."""
    if not iso_string:
        return "unknown time"
    try:
        dt = datetime.fromisoformat(iso_string)
    except ValueError:
        return iso_string
    local = dt.astimezone()
    hour_24 = local.hour
    period = "AM" if hour_24 < 12 else "PM"
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
    month_name = local.strftime("%B")
    return f"{month_name} {local.day}, {local.year} at {hour_12}:{local.minute:02d} {period}"


def run_analysis(audio_path: Path) -> dict:
    """
    Run the real analyzer on one file and return a normalized analysis
    record ready to store on a manifest entry under "analysis".

    Never raises for an analysis failure (missing file, damaged file,
    ffprobe failure) - returns a record with status "failed" and an
    error message instead, so a batch can continue past one bad file.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if not audio_path.exists():
        return {
            "status": "failed",
            "analyzed_at": now,
            "analyzer_version": ANALYZER_VERSION,
            "error": "Audio file was not found on disk.",
        }

    try:
        source_mtime = audio_path.stat().st_mtime
    except OSError as exc:
        return {
            "status": "failed",
            "analyzed_at": now,
            "analyzer_version": ANALYZER_VERSION,
            "error": f"Could not read file information: {exc}",
        }

    try:
        result = analyze_file(audio_path)
    except FileNotFoundError as exc:
        return {
            "status": "failed",
            "analyzed_at": now,
            "analyzer_version": ANALYZER_VERSION,
            "source_mtime": source_mtime,
            "error": f"FFmpeg or FFprobe was not found ({exc.filename or 'required tool'} not on PATH). Run Setup or configure the tool path, then try again.",
        }
    except PermissionError as exc:
        return {
            "status": "failed",
            "analyzed_at": now,
            "analyzer_version": ANALYZER_VERSION,
            "source_mtime": source_mtime,
            "error": f"Permission denied while reading this file: {exc}",
        }
    except Exception as exc:  # noqa: BLE001 - any other analyzer failure must not stop the batch
        return {
            "status": "failed",
            "analyzed_at": now,
            "analyzer_version": ANALYZER_VERSION,
            "source_mtime": source_mtime,
            "error": f"Analysis failed unexpectedly: {exc}",
        }

    if "error" in result:
        return {
            "status": "failed",
            "analyzed_at": now,
            "analyzer_version": ANALYZER_VERSION,
            "source_mtime": source_mtime,
            "error": result["error"],
        }

    # A file with no readable audio stream at all (see the same check
    # used in Add Recordings) is also a failure, not a valid analysis.
    if not result.get("codec") or not result.get("duration_seconds"):
        return {
            "status": "failed",
            "analyzed_at": now,
            "analyzer_version": ANALYZER_VERSION,
            "source_mtime": source_mtime,
            "error": "No readable audio stream was found - the file may be damaged or empty.",
        }

    return {
        "status": "analyzed",
        "analyzed_at": now,
        "analyzer_version": ANALYZER_VERSION,
        "source_mtime": source_mtime,
        "error": None,
        "duration_seconds": result.get("duration_seconds"),
        "duration_natural": natural_duration(result.get("duration_seconds", 0)),
        "file_size_bytes": result.get("size_bytes"),
        "bit_rate": result.get("bit_rate"),
        "codec": result.get("codec"),
        "sample_rate": result.get("sample_rate"),
        "channels": result.get("channels"),
        "mean_volume_db": result.get("mean_volume_db"),
        "max_volume_db": result.get("max_volume_db"),
        "silence_segment_count": result.get("silence_segment_count"),
        "objective_flags": result.get("flags", []),
    }


def analysis_is_stale(analysis: dict, audio_path: Path) -> bool:
    """True if the source file has changed since this analysis ran."""
    if not analysis or analysis.get("status") != "analyzed":
        return False
    stored_mtime = analysis.get("source_mtime")
    if stored_mtime is None:
        return False
    if not audio_path.exists():
        return False
    try:
        current_mtime = audio_path.stat().st_mtime
    except OSError:
        return False
    # Small tolerance - filesystems don't always preserve mtime to the
    # exact float, and a file re-saved with identical content sometimes
    # gets a mtime that differs in the last few microseconds.
    return abs(current_mtime - stored_mtime) > 1.0


def summarize_for_display(analysis: dict) -> str:
    """One-line human summary of an analysis result, for list views."""
    if analysis is None:
        return "Not yet analyzed."
    if analysis.get("status") == "failed":
        return f"Analysis failed: {analysis.get('error', 'unknown error')}"
    flags = analysis.get("objective_flags") or []
    if flags and flags[0].startswith("No objective flags"):
        return "No objective flags raised."
    if flags:
        return flags[0]
    return "Analyzed."
