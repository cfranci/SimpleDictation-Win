@echo off
REM SimpleDictation for Windows -- build script
REM Installs dependencies and packages as a standalone .exe

echo === SimpleDictation Build ===
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate and install deps
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

REM Build .exe using the spec file (includes all local modules)
echo.
echo Building SimpleDictation.exe...
pyinstaller SimpleDictation.spec --noconfirm

echo.
if exist "dist\SimpleDictation.exe" (
    echo SUCCESS: dist\SimpleDictation.exe
    echo.
    echo Run it with: dist\SimpleDictation.exe
) else (
    echo Build failed. Check the output above for errors.
)

pause
