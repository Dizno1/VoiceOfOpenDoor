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
    echo VoiceOfOpenDoor setup could not run.
    echo Python was not found on this computer.
    echo To fix this: install Python from https://www.python.org/downloads/windows/
    echo then run "Setup.bat" again.
    echo.
    pause
    exit /b 1
)

echo Installing VoiceOfOpenDoor App requirements using: %PYCMD%
echo.
%PYCMD% -m pip install -r "App\requirements.txt"
set SETUP_RESULT=%errorlevel%

echo.
if %SETUP_RESULT%==0 (
    echo Setup complete. You can now run "Launch VoiceOfOpenDoor.bat".
) else (
    echo Setup did not complete successfully. See the messages above for details.
)

echo.
pause
exit /b %SETUP_RESULT%
