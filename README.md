# LinkedIn Recruiter Automation

Automate your LinkedIn recruitment process seamlessly with our Python-based tool. This application leverages a custom Chrome profile to interact with LinkedIn, enabling tasks such as sending connection requests, messaging candidates, and more.

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
    - [1. Clone the Repository](#1-clone-the-repository)
    - [2. Set Up a Virtual Environment](#2-set-up-a-virtual-environment)
    - [3. Install Dependencies](#3-install-dependencies)
    - [4. Build Executables (Optional)](#4-build-executables-optional)
4. [Usage](#usage)
    - [1. Running the Setup Script](#1-running-the-setup-script)
    - [2. Configuring Chrome](#2-configuring-chrome)
    - [3. Running the Main Automation Script](#3-running-the-main-automation-script)
5. [Project Structure](#project-structure)
6. [Troubleshooting](#troubleshooting)
7. [Contributing](#contributing)
8. [License](#license)

---

## Features

- **Automated LinkedIn Tasks:** Streamline connection requests, messaging, and profile visits.
- **Custom Chrome Profile:** Maintain separate browsing sessions to avoid interference with personal accounts.
- **Cross-Platform Support:** Currently optimized for macOS, with plans for Windows support.
- **Detailed Logging:** Monitor activities and troubleshoot issues with comprehensive logs.

---

## Prerequisites

Before installing the LinkedIn Recruiter Automation tool, ensure your system meets the following requirements:

- **Operating System:** macOS (tested on macOS Catalina and later)
- **Python Version:** Python 3.6 or higher
- **Google Chrome:** Installed on your system
- **Apple Developer Account (Optional):** For code signing and notarization (recommended for distribution)

---

## Installation

Follow these steps to set up the LinkedIn Recruiter Automation tool on your macOS system.

### 1. Clone the Repository

Begin by cloning the repository to your local machine.

```bash
git clone https://github.com/ruslanliska/linkedin-recruiter.git
cd linkedin-recruiter
```

*Replace `yourusername` with your actual GitHub username.*

### 2. Set Up a Virtual Environment

It's recommended to use a virtual environment to manage dependencies without affecting your global Python installation.

```bash
python3 -m venv venv
source venv/bin/activate
```

*To deactivate the virtual environment later, simply run `deactivate`.*

### 3. Install Dependencies

Install the required Python packages using `pip`.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*Ensure that the `requirements.txt` file includes all necessary packages, such as `undetected-chromedriver`, `selenium`, and `psutil`.*

### 4. Build Executables (Optional)

If you prefer running standalone executables without managing a Python environment, you can build them using **PyInstaller**.

#### A. Install PyInstaller

With your virtual environment activated, install PyInstaller:

```bash
pip install pyinstaller
```

#### B. Build Executables

Run PyInstaller to create executables for both `setup_chrome.py` and `main.py`.

```bash
pyinstaller --onefile --console src/setup_chrome/setup_chrome.py
pyinstaller --onefile --console src/main/main.py
```

- `--onefile`: Packages the script and all dependencies into a single executable.
- `--console`: Keeps the console window open for user interaction. Use `--windowed` if you prefer to hide the console (suitable for GUI applications).

The executables will be located in the `dist/` directory.

---

## Usage

### 1. Running the Setup Script

The `setup_chrome` script initializes a custom Chrome profile for automation.

#### A. Navigate to the Executable

```bash
cd dist
```

#### B. Run the Setup Executable

```bash
./setup_chrome
```

**Output Example:**

```
2024-11-20 08:25:27,668 - INFO - Application Path: /Users/ruslanliska/PycharmProjects/linkedin-recruiter
2024-11-20 08:25:27,668 - INFO - Profile Path: /Users/ruslanliska/PycharmProjects/linkedin-recruiter/src/automation_profile
2024-11-20 08:25:27,668 - INFO - === Starting Chrome Automation Profile Setup ===
2024-11-20 08:25:27,668 - INFO - Detected Operating System: Darwin
2024-11-20 08:25:27,668 - INFO - Google Chrome executable found at: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
2024-11-20 08:25:27,668 - INFO - Profile directory already exists: /Users/ruslanliska/PycharmProjects/linkedin-recruiter/src/automation_profile
2024-11-20 08:25:27,668 - INFO - Chrome launched successfully with PID: 5938
2024-11-20 08:25:27,668 - INFO - Chrome has been launched with the custom automation profile.
2024-11-20 08:25:27,668 - INFO - Please configure Chrome as needed (e.g., log in, install extensions).
2024-11-20 08:25:27,668 - INFO - Once you have completed the setup, close the Chrome window to proceed.
```

### 2. Configuring Chrome

After launching Chrome with the custom profile:

1. **Log In:** Sign in with your LinkedIn account to synchronize your session.
2. **Install Extensions:** Add any necessary Chrome extensions that facilitate automation tasks.
3. **Adjust Settings:** Modify Chrome settings as required (e.g., disable notifications, set default search engine).

**Important:** Ensure you **close Chrome** after completing the setup to allow the script to finalize the profile.

### 3. Running the Main Automation Script

Once the setup is complete, run the main automation script to start automating LinkedIn tasks.

#### A. Navigate to the Executable

If not already in the `dist/` directory:

```bash
cd dist
```

#### B. Run the Main Executable

```bash
./main
```

**Output Example:**

```
2024-11-20 09:00:00,123 - INFO - Run ID: 28 - Automation Task Started.
2024-11-20 09:00:05,456 - INFO - ChromeDriver initialized successfully.
2024-11-20 09:00:10,789 - INFO - Navigated to https://www.example.com
2024-11-20 09:00:15,012 - INFO - Page Title: Example Domain
2024-11-20 09:00:20,345 - INFO - ChromeDriver has been closed.
```

---

## Project Structure

Understanding the project's directory structure helps in navigating and managing the project effectively.

```
linkedin-recruiter/
├── src/
│   ├── setup_chrome/
│   │   └── setup_chrome.py
│   ├── main/
│   │   └── main.py
│   ├── logs/                     # Log files (auto-created by scripts)
│   └── automation_profile/      # Chrome profile (auto-created by setup script)
├── dist/                        # PyInstaller output (executables)
│   ├── setup_chrome              # Executable for setup
│   └── main                      # Executable for main automation
├── build/                       # PyInstaller build files (auto-created)
├── requirements.txt             # Python dependencies
├── setup_chrome.spec            # PyInstaller spec file for setup_chrome.py
├── main.spec                    # PyInstaller spec file for main.py
└── README.md                    # Project documentation
```

---

## Troubleshooting

Encountering issues during installation or usage? Here are some common problems and their solutions.

### 1. `automation_profile` Created in `dist/` Instead of `src/`

**Cause:** Path resolution issues in the `setup_chrome.py` script.

**Solution:**

- Ensure that the `get_application_path()` function correctly determines the project root.
- Verify that the project structure aligns with the path calculations in the script.
- Check the `setup_chrome_profile.log` located in `src/logs/` for detailed path information.

**Example Log Entries:**

```
2024-11-20 08:25:27,668 - INFO - Application Path: /Users/ruslanliska/PycharmProjects/linkedin-recruiter
2024-11-20 08:25:27,668 - INFO - Profile Path: /Users/ruslanliska/PycharmProjects/linkedin-recruiter/src/automation_profile
```

### 2. Executable Fails to Launch Chrome

**Cause:** Incorrect path to the Chrome executable or Chrome not installed.

**Solution:**

- Verify that Google Chrome is installed at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
- Update the `get_chrome_path()` function if Chrome is installed in a different location.

### 3. Permission Denied Errors

**Cause:** Lack of necessary permissions to create directories or execute files.

**Solution:**

- Ensure you have read/write permissions in the project directory.
- Run the executable with elevated permissions if necessary:

  ```bash
  sudo ./setup_chrome
  ```

### 4. Missing Dependencies

**Cause:** Required Python packages are not installed.

**Solution:**

- Activate your virtual environment:

  ```bash
  source venv/bin/activate
  ```

- Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

### 5. Executable Not Found After Building

**Cause:** PyInstaller build failed or output path issues.

**Solution:**

- Ensure PyInstaller ran without errors during the build process.
- Check the `dist/` directory for the executables.
- Review the `setup_chrome.spec` and `main.spec` files for correct configurations.

---

## Contributing

Contributions are welcome! To contribute to the LinkedIn Recruiter Automation tool, follow these steps:

1. **Fork the Repository:** Click the "Fork" button on the repository page.

2. **Clone Your Fork:**

   ```bash
   git clone https://github.com/yourusername/linkedin-recruiter.git
   cd linkedin-recruiter
   ```

3. **Create a New Branch:**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

4. **Make Changes:** Implement your feature or fix.

5. **Commit Changes:**

   ```bash
   git commit -m "Add feature: YourFeatureName"
   ```

6. **Push to Your Fork:**

   ```bash
   git push origin feature/YourFeatureName
   ```

7. **Create a Pull Request:** Navigate to the original repository and create a pull request.

**Please ensure that your contributions adhere to the project's coding standards and include appropriate documentation and tests.**

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements

- **PyInstaller:** For enabling the creation of standalone executables.
- **Undetected-Chromedriver:** For facilitating Selenium interactions with Chrome.
- **Selenium:** For web browser automation.
- **psutil:** For process management.
