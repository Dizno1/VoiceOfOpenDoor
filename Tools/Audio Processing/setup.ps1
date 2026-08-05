# VoiceOfOpenDoor - Audio Processing Pipeline setup (Windows 11, primary path)
#
# STATUS: Draft. Not yet run or verified on Dean's Windows 11 system.
# Requires network access and an existing Python 3 install.
# After running, update the status table in README.md in this folder
# to say "Verified on Dean's Windows 11 system" for each item that
# actually succeeded here - do not mark items verified elsewhere.

Write-Host "Checking for Python..."
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python was not found on PATH. Install Python 3 from https://www.python.org/downloads/windows/ and re-run this script."
    exit 1
}

Write-Host "Checking for FFmpeg..."
ffmpeg -version
if ($LASTEXITCODE -ne 0) {
    Write-Host "FFmpeg was not found on PATH."
    Write-Host "Install it with: winget install Gyan.FFmpeg"
    Write-Host "Then close and reopen this terminal so PATH updates, and re-run this script."
    exit 1
}

Write-Host "Creating Python virtual environment (.venv)..."
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

Write-Host "Installing Python packages..."
python -m pip install --upgrade pip
pip install faster-whisper
pip install silero-vad
pip install soundfile numpy

Write-Host ""
Write-Host "pyannote.audio (diarization) is NOT installed by this script."
Write-Host "It requires a Hugging Face account, model license acceptance, and an access token."
Write-Host "See the 'Diarization' section in README.md before attempting that install."
Write-Host ""

Write-Host "Base setup complete. Verify each tool before relying on it:"
Write-Host "  ffmpeg -version"
Write-Host "  python -c ""from faster_whisper import WhisperModel"""
Write-Host ""
Write-Host "Record the results in Documentation/Development Environment.md and the status table in this folder's README.md."
