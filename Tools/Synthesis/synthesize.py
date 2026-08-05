#!/usr/bin/env python3
"""
VoiceOfOpenDoor - Synthesis command (Phase 9 draft)

STATUS: DRAFT. NOT YET RUN OR VERIFIED ANYWHERE.
See Tools/Synthesis/README.md before trusting anything below.

This CLI is engine-agnostic: it only calls the SpeechEngine interface
(engines/base.py). The active engine is selected in exactly one place
below. Swapping engines - XTTS v2 today, Chatterbox or anything else
later - means changing that one line, not this file's logic or the
command-line interface.

Usage:
    python synthesize.py "Text to speak" --voice ./voice_reference --out output.wav
"""

import argparse
import sys
from pathlib import Path

from engines.xtts_v2 import XTTSv2Engine

# The one place the active engine is chosen. See Documentation/Voice
# Pipeline Roadmap.md "Engine Decision" for rationale and the
# unresolved CPML licensing question that may change this.
ACTIVE_ENGINE = XTTSv2Engine()


def main():
    parser = argparse.ArgumentParser(description="VoiceOfOpenDoor synthesis command (draft)")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("--voice", required=True, help="Folder of voice reference clips")
    parser.add_argument("--out", required=True, help="Output WAV file path")
    args = parser.parse_args()

    voice_ref_dir = Path(args.voice)
    if not voice_ref_dir.is_dir():
        print(f"Voice reference folder not found: {voice_ref_dir}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out)
    ACTIVE_ENGINE.generate_speech(args.text, voice_ref_dir, out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
