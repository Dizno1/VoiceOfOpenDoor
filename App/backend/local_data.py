"""
VoiceOfOpenDoor - Local data root configuration and migration.

VoiceOfOpenDoor is now published to GitHub. This module implements the
external-data architecture required for that: the repository holds
only application code. All recordings, transcripts, segments, models,
and the manifest itself live in a user-configured folder outside the
repository, recorded in App/local-settings.json (gitignored - never
committed).

STATUS: Working. Config load/save, validation, subfolder creation, and
a verify-before-delete migration path (copy or move) from the old
in-repo Dataset/Raw Audio location are all implemented and tested.
"""

import hashlib
import json
import os
import shutil
from pathlib import Path

REQUIRED_SUBFOLDERS = [
    "Incoming Recordings",
    "Original Recordings",
    "Processed Recordings",
    "Rejected Recordings",
    "Transcripts",
    "Segments",
    "Models",
    "Exports",
    "Backups",
    # Not one of the nine folders named in the directive, but the
    # manifest itself contains Dean's private classifications and notes
    # about his own recordings - it cannot stay in the public repository
    # either. Kept alongside the required nine rather than silently
    # placed loose at the data root.
    "Metadata",
]


def _file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class LocalDataConfig:
    def __init__(self, settings_path: Path, example_path: Path):
        self.settings_path = settings_path
        self.example_path = example_path

    def load(self) -> dict:
        if not self.settings_path.exists():
            return {}
        try:
            return json.loads(self.settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self, data_root: str) -> None:
        self.settings_path.write_text(json.dumps({"data_root": data_root}, indent=2))

    def get_data_root(self) -> "Path | None":
        raw = self.load().get("data_root")
        return Path(raw) if raw else None


def validate_data_root(root: "Path | None") -> dict:
    """
    Check whether a data root path is usable. Never raises - always
    returns a status dict so the caller can show a clear message
    instead of a crash.
    """
    if root is None:
        return {"configured": False, "exists": False, "writable": False, "error": "No data folder has been configured yet."}

    if not root.exists():
        return {"configured": True, "exists": False, "writable": False, "error": f"The folder {root} does not exist."}

    if not root.is_dir():
        return {"configured": True, "exists": False, "writable": False, "error": f"{root} exists but is not a folder."}

    writable = os.access(root, os.W_OK)
    if not writable:
        return {"configured": True, "exists": True, "writable": False, "error": f"{root} exists but is not writable. Check folder permissions."}

    return {"configured": True, "exists": True, "writable": True, "error": None}


def create_data_root_if_needed(path_str: str) -> dict:
    """
    Create the data root folder itself (not subfolders) if it doesn't
    exist yet, supporting "create a new folder" from the setup page.
    Never raises - returns a status dict.
    """
    root = Path(path_str)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return {"created": False, "error": f"Could not create {root}: {exc}"}
    return {"created": True, "error": None, "root": root}


def ensure_subfolders(root: Path) -> list:
    """Create every required subfolder if missing. Returns the list created (for reporting)."""
    created = []
    for name in REQUIRED_SUBFOLDERS:
        folder = root / name
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            created.append(name)
    return created


def count_data(root: Path) -> dict:
    """Recording/transcript/segment/model counts for the Settings page."""
    def count_files(subfolder, extensions=None):
        folder = root / subfolder
        if not folder.exists():
            return 0
        files = [f for f in folder.iterdir() if f.is_file() and f.name != ".gitkeep"]
        if extensions:
            files = [f for f in files if f.suffix.lower() in extensions]
        return len(files)

    audio_ext = {".wav", ".mp3", ".m4a", ".flac", ".aac"}
    return {
        "recordings": count_files("Original Recordings", audio_ext),
        "transcripts": count_files("Transcripts"),
        "segments": count_files("Segments"),
        "models": count_files("Models"),
    }


def find_repo_corpus(repo_dataset_raw_audio: Path) -> list:
    """Audio files still sitting in the old in-repo location, needing migration."""
    if not repo_dataset_raw_audio.exists():
        return []
    audio_ext = {".wav", ".mp3", ".m4a", ".flac", ".aac"}
    return [f for f in repo_dataset_raw_audio.iterdir() if f.is_file() and f.suffix.lower() in audio_ext]


def migrate_file(source: Path, dest_dir: Path, mode: str) -> dict:
    """
    Copy or move one file from the repo's old location to the new data
    root's Original Recordings folder. For "move", the source is only
    deleted after the destination copy is verified byte-for-byte via
    checksum - never before.
    """
    dest = dest_dir / source.name
    if dest.exists():
        return {"file": source.name, "status": "skipped", "reason": "A file with this name already exists at the destination - not overwritten."}

    try:
        shutil.copy2(source, dest)
    except OSError as exc:
        return {"file": source.name, "status": "failed", "reason": f"Copy failed: {exc}"}

    source_checksum = _file_checksum(source)
    dest_checksum = _file_checksum(dest)
    if source_checksum != dest_checksum:
        # Verification failed - remove the bad partial copy, leave the
        # original completely untouched, never delete on a failed verify.
        try:
            dest.unlink()
        except OSError:
            pass
        return {"file": source.name, "status": "failed", "reason": "Copy did not verify (checksum mismatch) - original left in place."}

    if mode == "move":
        try:
            source.unlink()
        except OSError as exc:
            return {"file": source.name, "status": "copied_not_removed", "reason": f"Copied and verified, but the original could not be removed: {exc}"}
        return {"file": source.name, "status": "moved", "reason": None}

    return {"file": source.name, "status": "copied", "reason": None}
