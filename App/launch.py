#!/usr/bin/env python3
"""
VoiceOfOpenDoor - Launcher.

Runs after the batch file has already confirmed a Python interpreter
exists (see "Launch VoiceOfOpenDoor.bat" - it checks that itself,
since if Python is missing this script can't run at all to check it).

This script:
  1. Checks Flask is installed before doing anything else.
  2. Checks whether the app is already running (avoids starting a
     duplicate server or opening a second browser tab).
  3. Starts the server in the background.
  4. Waits until the server actually responds before opening a browser -
     never opens the browser blind on a fixed delay.
  5. Prints one clear plain-text line per step, and on any failure,
     prints exactly what to run to fix it, then exits with a non-zero
     code so the batch file knows to keep the window open.

STATUS: The requirement-checking, duplicate-detection, and
wait-for-ready logic below have been run and verified in a Linux
sandbox (see CHANGELOG.md for what was tested and how). The Windows
double-click experience itself - especially whether Chrome actually
opens - has NOT been verified yet. This is a second attempt after the
first one failed silently on Dean's machine; test it and report back
exactly what you see, including any printed error text.
"""

import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/"


def log(message: str) -> None:
    # One clear plain-text statement per line - no special characters
    # that might read oddly with a screen reader, no progress bars.
    print(message)


def port_is_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_flask_available() -> bool:
    try:
        import flask  # noqa: F401
        return True
    except ImportError:
        return False


def wait_for_server(host: str, port: int, timeout_seconds: float = 15.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if port_is_open(host, port):
            return True
        time.sleep(0.25)
    return False


def open_browser_safely(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception as exc:  # noqa: BLE001 - report, don't crash the app over this
        log(f"The server is running, but the browser could not be opened automatically: {exc}")
        log(f"Open your browser and go to: {url}")


def main() -> int:
    log("Checking VoiceOfOpenDoor requirements...")

    if not check_flask_available():
        log("")
        log("VoiceOfOpenDoor could not start: Flask is not installed.")
        log("To fix this, open Command Prompt in this folder and run:")
        log("    py -m pip install -r requirements.txt")
        log("If that command is not recognized, try:")
        log("    python -m pip install -r requirements.txt")
        log("Then run Launch VoiceOfOpenDoor.bat again.")
        return 1

    log("Flask found.")

    if port_is_open(HOST, PORT):
        log(f"VoiceOfOpenDoor already appears to be running at {URL}")
        log("Opening your browser to the existing session instead of starting a new one.")
        open_browser_safely(URL)
        return 0

    log("Starting the VoiceOfOpenDoor server...")

    try:
        from app import app
    except Exception as exc:  # noqa: BLE001 - surface the real import error
        log("")
        log("VoiceOfOpenDoor could not start: the application failed to load.")
        log(f"The error was: {exc}")
        log("This is likely a bug in the application itself, not a missing package.")
        return 1

    server_error = {}

    def run_server():
        try:
            app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
        except Exception as exc:  # noqa: BLE001
            server_error["exception"] = exc

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    if not wait_for_server(HOST, PORT, timeout_seconds=15.0):
        log("")
        log("VoiceOfOpenDoor did not start within 15 seconds.")
        if "exception" in server_error:
            log(f"The server reported this error: {server_error['exception']}")
        else:
            log("This usually means something else is already using port 5000.")
        return 1

    log("Server ready. Opening your browser...")
    open_browser_safely(URL)

    log("VoiceOfOpenDoor is running. Close this window to stop it.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Stopping VoiceOfOpenDoor.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
