# Save this script as run_application.ps1

# Define virtual environment name and main script
$VENV_NAME = "venv"
$MAIN_SCRIPT = "src/main.py"

Write-Host "Starting the application..."

# Function to check the last command's success
function Check-LastCommand {
    if (!$?) {
        Write-Error $args[0]
        exit 1
    }
}

# Check if the virtual environment exists
if (!(Test-Path $VENV_NAME)) {
    Write-Error "Virtual environment not found. Please run setup_project.ps1 first."
    exit 1
} else {
    Write-Host "Virtual environment found at $VENV_NAME."
}

# Activate the virtual environment
$activateScript = Join-Path $VENV_NAME "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..."
    & $activateScript
    if (!$?) {
        Write-Error "Failed to activate virtual environment."
        exit 1
    }
} else {
    Write-Error "Activation script not found at $activateScript."
    exit 1
}

# Run the main Python script
if (Test-Path $MAIN_SCRIPT) {
    Write-Host "Running $MAIN_SCRIPT..."
    python $MAIN_SCRIPT
    if (!$?) {
        Write-Error "Failed to execute $MAIN_SCRIPT."
        exit 1
    }
} else {
    Write-Error "$MAIN_SCRIPT not found. Please ensure the file exists in the project directory."
    exit 1
}

Write-Host "Application finished."
exit 0
