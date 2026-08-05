#!/usr/bin/env bash
# VoiceOfOpenDoor - Audio Processing Pipeline setup (Linux, secondary/optional path)
#
# Windows 11 is the reference platform for this repository - use setup.ps1
# as the primary path. This script is kept as an alternate for Linux use.
#
# STATUS: Draft. Not yet run or verified in any environment that counts
# toward the project (see Documentation/Development Environment.md for
# the verification policy). Requires network access. Run once, then
# update the Verification Status table in README.md in this folder.
set -e

echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y ffmpeg

echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing Python packages..."
pip install --upgrade pip
pip install faster-whisper
pip install silero-vad
pip install pyannote.audio
pip install soundfile numpy

echo "Setup complete. Verify each tool manually before relying on it:"
echo "  python3 -c 'from faster_whisper import WhisperModel'"
echo "  ffmpeg -version"
