#!/usr/bin/env python3
"""
VoiceOfOpenDoor - Recording Analyzer

Scans one recording or a folder of recordings and produces an objective
engineering report for each: duration, format, sample rate, channels,
mean/peak volume, and a silence/VAD-style speech-region estimate.

This tool wraps FFmpeg (ffprobe + the volumedetect and silencedetect
filters) - no ML model, no network access, and no GPU are required.
It runs the same way on Windows, macOS, or Linux as long as FFmpeg is
on PATH.

This does NOT transcribe, diarize, or judge subjective speech quality.
It produces the objective half of a Recording Assessment entry; the
subjective half (naturalness, background-noise character, etc.) still
requires a human listening pass, per Phase 3 of the project roadmap.

Usage:
    python analyze.py <file_or_folder> [--out report.json]

Requires: Python 3.8+, FFmpeg/ffprobe on PATH. No other dependencies.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ANALYZER_VERSION = "1.0"

AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".flac", ".ogg", ".aac"}


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr


def ffprobe_info(path):
    out, err = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,sample_rate,channels",
        "-of", "json", str(path),
    ])
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"error": f"ffprobe failed to parse output: {err.strip()}"}

    fmt = data.get("format", {})
    streams = data.get("streams", [])
    audio_stream = next((s for s in streams if "sample_rate" in s), {})

    return {
        "duration_seconds": round(float(fmt.get("duration", 0)), 2),
        "size_bytes": int(fmt.get("size", 0)) if fmt.get("size") else None,
        "bit_rate": int(fmt.get("bit_rate", 0)) if fmt.get("bit_rate") else None,
        "codec": audio_stream.get("codec_name"),
        "sample_rate": audio_stream.get("sample_rate"),
        "channels": audio_stream.get("channels"),
    }


def volume_stats(path):
    _, err = run(["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    mean_match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", err)
    max_match = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", err)
    return {
        "mean_volume_db": float(mean_match.group(1)) if mean_match else None,
        "max_volume_db": float(max_match.group(1)) if max_match else None,
    }


def silence_regions(path, noise_db="-30dB", min_silence=0.5):
    _, err = run([
        "ffmpeg", "-i", str(path),
        "-af", f"silencedetect=noise={noise_db}:d={min_silence}",
        "-f", "null", "-",
    ])
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?\d+(?:\.\d+)?)", err)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?\d+(?:\.\d+)?)", err)]
    return {
        "silence_segment_count": min(len(starts), len(ends)),
    }


def flag_recording(info, volume):
    flags = []
    if volume.get("max_volume_db") is not None and volume["max_volume_db"] >= -0.5:
        flags.append("Max volume at or near 0 dB ceiling - verify no clipping/limiting by ear.")
    if volume.get("mean_volume_db") is not None and volume["mean_volume_db"] <= -28:
        flags.append("Low mean volume - possible distant mic or quiet source; verify usable SNR by ear.")
    if info.get("bit_rate") and info["bit_rate"] < 48000:
        flags.append(f"Low bitrate ({info['bit_rate']} bps) relative to rest of corpus - check for compression artifacts.")
    if not flags:
        flags.append("No objective flags raised. Still requires subjective listening pass per Phase 3.")
    return flags


def analyze_file(path):
    info = ffprobe_info(path)
    if "error" in info:
        return {"file": path.name, "error": info["error"]}
    volume = volume_stats(path)
    silence = silence_regions(path)
    return {
        "file": path.name,
        **info,
        **volume,
        **silence,
        "flags": flag_recording(info, volume),
    }


def main():
    parser = argparse.ArgumentParser(description="VoiceOfOpenDoor recording analyzer")
    parser.add_argument("target", help="Audio file or folder of audio files")
    parser.add_argument("--out", help="Write JSON report to this path instead of stdout")
    args = parser.parse_args()

    target = Path(args.target)
    if target.is_dir():
        files = sorted(p for p in target.iterdir() if p.suffix.lower() in AUDIO_EXTENSIONS)
    elif target.is_file():
        files = [target]
    else:
        print(f"Not found: {target}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print(f"No audio files found in: {target}", file=sys.stderr)
        sys.exit(1)

    report = [analyze_file(f) for f in files]

    output = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(output)
        print(f"Wrote report for {len(files)} file(s) to {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
