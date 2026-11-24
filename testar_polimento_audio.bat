@echo off
setlocal
pushd "%~dp0"
set "PILOT_PYTHON=.venv\Scripts\python.exe"
"%PILOT_PYTHON%" -V >nul 2>nul
if errorlevel 1 (
    set "PILOT_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    set "PYTHONPATH=%CD%\.venv\Lib\site-packages"
)
"%PILOT_PYTHON%" -B devtools\preview_audio_polish.py %*
set "PILOT_EXIT=%ERRORLEVEL%"
popd
exit /b %PILOT_EXIT%
