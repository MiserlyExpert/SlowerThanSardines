@echo off
rem Double-click to play Slower Than Sardines from source (Windows).
rem First run sets up a private Python environment in .venv and installs pygame.
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY goto nopython
if not exist ".venv\Scripts\python.exe" (
  echo First run: setting up the game, this takes a minute...
  %PY% -m venv .venv || goto nopython
  ".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet || goto fail
)
".venv\Scripts\python.exe" main.py %*
if errorlevel 1 (
  echo.
  echo The game closed with an error. Copy the message above and send it over.
  pause
)
exit /b
:nopython
echo Python is not installed.
echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH",
echo then double-click Play.bat again.
pause
exit /b 1
:fail
echo Could not install pygame. Check your internet connection and try again.
pause
exit /b 1
