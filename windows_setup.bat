@echo off
setlocal enabledelayedexpansion

REM Define Python version, virtual environment name, and Chrome setup script
set "PYTHON_VERSION=python"
set "VENV_NAME=venv"
set "CHROME_SETUP_SCRIPT=src/setup_chrome.py"

echo Starting project setup...

REM Check if Python is installed
echo Checking Python installation...
where %PYTHON_VERSION% >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python and ensure it is added to PATH.
    exit /b 1
)
echo Python is installed.

echo Before virtual environment creation...

REM Create virtual environment
if not exist "!VENV_NAME!" (
    echo Creating virtual environment (!VENV_NAME!)...
    !PYTHON_VERSION! -m venv !VENV_NAME!
    if !errorlevel! neq 0 (
        echo Failed to create virtual environment.
        exit /b 1
    )
    echo Finished creating virtual environment...
) else (
    echo Virtual environment already exists.
)

echo Before activating the virtual environment...

REM Activate the virtual environment
call "!VENV_NAME!\Scripts\activate.bat"
if !errorlevel! neq 0 (
    echo Failed to activate virtual environment.
    exit /b 1
)

echo Before upgrading pip...

REM Upgrade pip
python -m pip install --upgrade pip
if !errorlevel! neq 0 (
    echo Failed to upgrade pip.
    exit /b 1
)

echo Before installing dependencies...

REM Install dependencies
if exist "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    python -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo Failed to install dependencies.
        exit /b 1
    )
) else (
    echo requirements.txt not found. Skipping dependency installation.
)

echo Before running Chrome setup script...

REM Run Chrome setup script
if exist "!CHROME_SETUP_SCRIPT!" (
    echo Running Chrome setup script (!CHROME_SETUP_SCRIPT!)...
    python "!CHROME_SETUP_SCRIPT!"
    if !errorlevel! neq 0 (
        echo Failed to execute Chrome setup script.
        exit /b 1
    )
) else (
    echo Chrome setup script (!CHROME_SETUP_SCRIPT!) not found. Skipping Chrome setup.
)

echo Project setup complete.
exit /b 0
