@echo off
setlocal

REM Define virtual environment name and main script
set "VENV_NAME=venv"
set "MAIN_SCRIPT=main.py"

echo Starting the application...

REM Check if the virtual environment exists
if not exist "%VENV_NAME%" (
    echo Virtual environment not found. Please run setup_project.bat first.
    exit /b 1
)

REM Activate the virtual environment
call "%VENV_NAME%\Scripts\activate"
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    exit /b 1
)

REM Run the main Python script
if exist "%MAIN_SCRIPT%" (
    python %MAIN_SCRIPT%
    if %errorlevel% neq 0 (
        echo Failed to execute %MAIN_SCRIPT%.
        exit /b 1
    )
) else (
    echo %MAIN_SCRIPT% not found. Please ensure the file exists in the project directory.
    exit /b 1
)

echo Application finished.
exit /b 0
