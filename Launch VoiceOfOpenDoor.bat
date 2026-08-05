@echo off
setlocal
cd /d "%~dp0"

set PYCMD=

where py >nul 2>&1
if %errorlevel%==0 (
    set PYCMD=py
) else (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set PYCMD=python
    )
)

if "%PYCMD%"=="" (
    echo VoiceOfOpenDoor could not start.
    echo Python was not found on this computer.
    echo To fix this: install Python from https://www.python.org/downloads/windows/
    echo then run "Launch VoiceOfOpenDoor.bat" again.
    echo.
    pause
    exit /b 1
)

echo Starting VoiceOfOpenDoor using: %PYCMD%
echo.
%PYCMD% "App\launch.py"
set LAUNCH_RESULT=%errorlevel%

if not %LAUNCH_RESULT%==0 (
    echo.
    echo VoiceOfOpenDoor did not start successfully.
    echo See the messages above for what to fix, then try again.
    echo.
    pause
)

exit /b %LAUNCH_RESULT%
