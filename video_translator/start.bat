@echo off
title Video Dialogue Translator
cd /d "%~dp0"

rem Already running? Just open the browser.
netstat -ano | findstr /r /c:":8000 .*LISTENING" >nul
if not errorlevel 1 (
  start "" http://localhost:8000
  exit /b
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo [!] ffmpeg not found. Install it with:  winget install Gyan.FFmpeg
  echo     then open this shortcut again.
  pause
  exit /b 1
)

if not "%ANTHROPIC_API_KEY%"=="" goto deps
echo ANTHROPIC_API_KEY is not set.
set /p ANTHROPIC_API_KEY=Paste your Anthropic API key and press Enter: 
setx ANTHROPIC_API_KEY "%ANTHROPIC_API_KEY%" >nul

:deps
python -c "import fastapi, multipart, faster_whisper, anthropic, uvicorn" >nul 2>nul
if errorlevel 1 (
  echo Installing Python packages...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [!] Package install failed. Is Python installed and on PATH?
    pause
    exit /b 1
  )
)

rem Open the browser once the server has had a moment to start.
start "" /min cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:8000"
echo Server running at http://localhost:8000  (close this window to stop)
python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
