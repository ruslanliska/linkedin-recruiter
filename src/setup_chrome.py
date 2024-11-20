import logging
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil


def get_application_path():
    """
    Determines the path to the application directory, whether
    running as a script or as a bundled executable.
    Returns:
        Path: Path object to the application directory.
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundled executable
        exe_path = Path(sys.executable).parent
        # Assuming the project structure:
        # project_root/
        # ├── src/
        # │   └── setup_chrome.py
        # ├── dist/
        # │   └── setup_chrome (executable)
        # To reach src/, go one level up from dist/
        project_root = exe_path.parent
        return project_root
    else:
        # If run as a normal script
        return Path(__file__).parent


def setup_logging():
    """
    Configures logging to output messages to both console and a log file.
    """
    app_path = get_application_path()
    log_dir = app_path / 'logs'
    # Ensure the logs directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'setup_chrome_profile.log'

    logging.basicConfig(
        level=logging.INFO,  # Set the minimum logging level
        format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
        handlers=[
            logging.StreamHandler(sys.stdout),  # Log to console
            logging.FileHandler(log_file, encoding='utf-8'),  # Log to file
        ],
    )


def get_os_type():
    """
    Detects the operating system.
    Returns:
        str: 'Windows' or 'Darwin' for macOS
    """
    return platform.system()


def get_chrome_path(os_type):
    """
    Defines the path to the Google Chrome
    executable based on the operating system.
    Args:
        os_type (str): 'Windows' or 'Darwin' for macOS
    Returns:
        Path: Path object to the Chrome executable
    """
    if os_type == 'Windows':
        # Common installation paths for Windows
        possible_paths = [
            Path('C:/Program Files/Google/Chrome/Application/chrome.exe'),
            Path('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'),
        ]
        for path in possible_paths:
            if path.exists():
                return path
        logging.error('Google Chrome executable not found on Windows.')
        sys.exit(1)
    elif os_type == 'Darwin':
        # Default installation path for macOS
        chrome_path = Path(
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        )
        if chrome_path.exists():
            return chrome_path
        logging.error('Google Chrome executable not found on macOS.')
        sys.exit(1)
    else:
        logging.error(f"Unsupported Operating System: {os_type}")
        sys.exit(1)


def get_profile_path():
    """
    Defines the Chrome user data directory based on the operating system.
    Returns:
        Path: Path object to the automation
        profile directory within project root
    """
    app_path = get_application_path()
    profile_dir = app_path / 'src' / 'automation_profile'
    return profile_dir


def create_profile_directory(profile_path):
    """
    Creates the automation profile directory if it doesn't exist.
    Args:
        profile_path (Path): Path to the automation profile directory
    """
    try:
        if profile_path.exists():
            logging.info(f"Profile directory already exists: {profile_path}")
        else:
            profile_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created profile directory: {profile_path}")
    except Exception as e:
        logging.error(f"Failed to create profile directory: {e}")
        sys.exit(1)


def launch_chrome(chrome_path, profile_path, os_type, log_file):
    """
    Launches Google Chrome with the specified user
    data directory to initialize the profile.
    Args:
        chrome_path (Path): Path to the Chrome executable
        profile_path (Path): Path to the automation profile directory
        os_type (str): 'Windows' or 'Darwin' for macOS
        log_file (Path): Path to the log file for Chrome's output
    Returns:
        subprocess.Popen: The subprocess running Chrome
    """
    chrome_commands = {
        'Windows': [
            str(chrome_path),
            f'--user-data-dir={str(profile_path)}',
            '--no-first-run',
            '--no-default-browser-check',
            '--new-instance',  # Force a new instance on Windows
        ],
        'Darwin': [
            str(chrome_path),
            f'--user-data-dir={str(profile_path)}',
            '--no-first-run',
            '--no-default-browser-check',
            # '--new-instance' not needed on macOS
        ],
    }

    try:
        cmd = chrome_commands[os_type]
        logging.info(f"Launching Chrome with command: {' '.join(cmd)}")

        # Open the log file in append mode for Chrome's stdout and stderr
        chrome_log_path = log_file.parent / 'chrome_output.log'
        chrome_log = chrome_log_path.open('a', encoding='utf-8')

        # Start Chrome, redirecting stdout and
        # stderr to the chrome_output.log file
        chrome_process = subprocess.Popen(
            cmd,
            stdout=chrome_log,
            stderr=chrome_log,
            shell=False,  # Avoid using shell for security reasons
        )
        logging.info(f"Chrome launched successfully with PID: {
                     chrome_process.pid
                     }")
        return chrome_process
    except FileNotFoundError:
        logging.error('Google Chrome executable not found.')
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to launch Chrome: {e}")
        sys.exit(1)


def terminate_process_and_children(process):
    """
    Terminates the given subprocess and all its child processes.
    Args:
        process (subprocess.Popen): The subprocess to terminate
    """
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        gone, still_alive = psutil.wait_procs(children, timeout=5)
        for p in still_alive:
            p.kill()
        parent.terminate()
        parent.wait(timeout=5)
        logging.info('Chrome process and all child processes terminated.')
    except Exception as e:
        logging.error(f"Error terminating Chrome and its child processes: {e}")


def terminate_process(process):
    """
    Terminates the given subprocess and its child processes.
    Args:
        process (subprocess.Popen): The subprocess to terminate
    """
    try:
        if process.poll() is None:
            logging.info(
                'Terminating Chrome process and its child processes...',
            )
            terminate_process_and_children(process)
    except Exception as e:
        logging.error(f"Error terminating Chrome process: {e}")


def is_chrome_running_with_profile(profile_path):
    """
    Checks if any Chrome process is running
      with the specified user data directory.
    Args:
        profile_path (Path): Path to the automation profile directory
    Returns:
        bool: True if a matching Chrome process is found, False otherwise
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'chrome' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if any(f"--user-data-dir={str(profile_path)}" in arg for arg in cmdline):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def main():
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info('=== Starting Chrome Automation Profile Setup ===')

    os_type = get_os_type()
    logger.info(f"Detected Operating System: {os_type}")

    chrome_path = get_chrome_path(os_type)
    logger.info(f"Google Chrome executable found at: {chrome_path}")

    profile_path = get_profile_path()
    create_profile_directory(profile_path)

    # Define the main log file
    app_path = get_application_path()
    main_log_file = app_path / 'logs' / 'setup_chrome_profile.log'

    # If the profile directory already has data, prompt the user to clear it
    if any(profile_path.iterdir()):
        logger.warning(f"The profile directory {profile_path} is not empty.")
        # response = input(f"Do you want to clear the existing profile data in {profile_path}? (y/n): ").lower()
        response = 'n'
        if response == 'y':
            try:
                shutil.rmtree(profile_path)
                profile_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cleared and recreated profile directory: {
                            profile_path
                            }")
            except Exception as e:
                logger.error(f"Failed to clear profile directory: {e}")
                sys.exit(1)
        else:
            logger.info('Keeping existing profile data.')
            sys.exit(0)
    else:
        logger.info(f"No existing data in profile directory: {profile_path}")

    # Ensure no other Chrome instances are running with the same profile
    if is_chrome_running_with_profile(profile_path):
        logger.error(
            'Another Chrome instance is already running with the automation profile.',
        )
        logger.error(
            'Please close all Chrome windows using the automation profile and try again.',
        )
        sys.exit(1)

    # Launch Chrome with the custom profile, redirecting its output to chrome_output.log
    chrome_process = launch_chrome(
        chrome_path, profile_path, os_type, main_log_file,
    )

    logger.info('Chrome has been launched with the custom automation profile.')
    logger.info(
        'Please configure Chrome as needed (e.g., log in, install extensions).',
    )
    logger.info(
        'Once you have completed the setup, close the Chrome window to proceed.',
    )

    # Wait for the user to close Chrome
    try:
        while True:
            if not is_chrome_running_with_profile(profile_path):
                logger.info(
                    'Chrome process associated with the automation profile has been closed.',
                )
                break
            else:
                # Optional: Uncomment the following lines to log
                # every minute that Chrome is still running
                # current_time = time.strftime("%H:%M:%S")
                # logger.debug(f"Chrome is still running at {current_time}...")
                pass
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received. Terminating Chrome process.')
        terminate_process(chrome_process)
        sys.exit(0)
    except Exception as e:
        logger.error(
            f"An error occurred while waiting for Chrome to close: {e}",
        )
        terminate_process(chrome_process)
        sys.exit(1)

    logger.info('Chrome automation profile setup is complete.')
    logger.info('You can now proceed to run the main automation application.')


if __name__ == '__main__':
    main()
