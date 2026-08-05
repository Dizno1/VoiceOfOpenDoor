"""
VoiceOfOpenDoor - Synthesis engine interface.

Every synthesis engine (XTTS v2 today, Chatterbox or anything else
later) implements this same interface. The application, CLI, and
local API should only ever call generate_speech() - never import an
engine-specific package directly. Swapping engines means adding a new
file in this folder and changing one line where the active engine is
selected (see synthesize.py); nothing else in the project should need
to change.

STATUS: Interface defined and used by the XTTS v2 adapter. Not yet
exercised end to end anywhere - see Tools/Synthesis/README.md.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class SpeechEngine(ABC):
    """Common interface for all VoiceOfOpenDoor synthesis engines."""

    @abstractmethod
    def generate_speech(self, text: str, voice_reference: Path, output_path: Path) -> None:
        """
        Generate speech and write it to output_path as a WAV file.

        text: the text to speak.
        voice_reference: path to a voice reference (a folder of clips
            for a cloning-style engine today; may become a path to a
            trained model artifact once Phase 8 produces one).
        output_path: where to write the resulting WAV file.

        Raises on failure rather than returning a status code, so
        callers can rely on a normal try/except.
        """
        raise NotImplementedError
