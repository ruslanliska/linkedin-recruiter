# Requires PowerShell 5.0 or later
# Save this script as setup_project.ps1

# Enable script execution if not already enabled
# You might need to run PowerShell as Administrator and execute:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Write-Host "Starting project setup..."

# Define Python version, virtual environment name, and Chrome setup script
$PYTHON_VERSION = "python"
$VENV_NAME = "venv"
$CHROME_SETUP_SCRIPT = "src/setup_chrome.py"

# Function to check the last command's success
function Check-LastCommand {
    if (!$?) {
        Write-Error $args[0]
        exit 1
    }
}

# Check if Python is installed
Write-Host "Checking Python installation..."
$pythonPath = Get-Command $PYTHON_VERSION -ErrorAction SilentlyContinue

if (!$pythonPath) {
    Write-Error "Python is not installed or not in PATH."
    Write-Error "Please install Python and ensure it is added to PATH."
    exit 1
} else {
    Write-Host "Python is installed at $($pythonPath.Path)."
}

# Create virtual environment if it doesn't exist
Write-Host "Before virtual environment creation..."
if (!(Test-Path $VENV_NAME)) {
    Write-Host "Creating virtual environment ($VENV_NAME)..."
    python -m venv $VENV_NAME
    Check-LastCommand "Failed to create virtual environment."
    Write-Host "Finished creating virtual environment..."
} else {
    Write-Host "Virtual environment already exists."
}

# Activate the virtual environment
Write-Host "Before activating the virtual environment..."
$activateScript = Join-Path $VENV_NAME "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..."
    & $activateScript
    Check-LastCommand "Failed to activate virtual environment."
} else {
    Write-Error "Activation script not found at $activateScript."
    exit 1
}

# Upgrade pip
Write-Host "Before upgrading pip..."
python -m pip install --upgrade pip
Check-LastCommand "Failed to upgrade pip."

# Install dependencies
Write-Host "Before installing dependencies..."
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..."
    python -m pip install -r requirements.txt
    Check-LastCommand "Failed to install dependencies."
} else {
    Write-Host "requirements.txt not found. Skipping dependency installation."
}

# Run Chrome setup script
Write-Host "Before running Chrome setup script..."
if (Test-Path $CHROME_SETUP_SCRIPT) {
    Write-Host "Running Chrome setup script ($CHROME_SETUP_SCRIPT)..."
    python $CHROME_SETUP_SCRIPT
    Check-LastCommand "Failed to execute Chrome setup script."
} else {
    Write-Host "Chrome setup script ($CHROME_SETUP_SCRIPT) not found. Skipping Chrome setup."
}

Write-Host "Project setup complete."
exit 0
