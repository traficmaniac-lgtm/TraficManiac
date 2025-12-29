@echo off
setlocal

REM Install dependencies if they are not already present
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Failed to install dependencies. Please ensure Python and pip are available.
    pause
    exit /b %ERRORLEVEL%
)

REM Launch the CPA Grip AI Suite GUI
python -m cpagrip_ai_suite

endlocal
pause
