"""
VoiceOfOpenDoor - XTTS v2 adapter.

STATUS: DRAFT. NOT YET RUN OR VERIFIED ANYWHERE.
Interface/API confirmed against current (2026) documentation, but this
has never actually been executed - see Tools/Synthesis/README.md.

LICENSE WARNING: XTTS v2's weights are under the Coqui Public Model
License (CPML), which restricts commercial use. See the Engine
Decision section in Documentation/Voice Pipeline Roadmap.md - this
must be resolved before this adapter is used for real.

Install: pip install coqui-tts
(NOT `pip install TTS` - that package is unmaintained.)
"""

from pathlib import Path

from .base import SpeechEngine


class XTTSv2Engine(SpeechEngine):
    def generate_speech(self, text: str, voice_reference: Path, output_path: Path) -> None:
        try:
            from TTS.api import TTS  # type: ignore
        except ImportError as exc:
            raise SystemExit(
                "The TTS package is not installed. Run:\n"
                "  pip install coqui-tts\n"
                "Do NOT install the plain 'TTS' package from PyPI - it is "
                "unmaintained and conflicts with current dependencies."
            ) from exc

        reference_clips = sorted(
            str(p) for p in voice_reference.glob("*")
            if p.suffix.lower() in {".wav", ".m4a", ".mp3"}
        )
        if not reference_clips:
            raise SystemExit(f"No reference audio found in {voice_reference}")

        # Model name and call signature confirmed against current (2026)
        # PyPI/Hugging Face documentation for the coqui-tts fork.
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        tts.tts_to_file(
            text=text,
            speaker_wav=reference_clips,
            language="en",
            file_path=str(output_path),
        )
