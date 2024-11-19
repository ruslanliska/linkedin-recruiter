import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def setup_logging():
    """
    Configures logging to output messages to both console and a log file.
    """
    log_dir = Path(__file__).resolve().parent / 'logs'
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
    Defines the path to the Google Chrome executable based on the operating system.
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


def get_profile_path(os_type):
    """
    Defines the Chrome user data directory based on the operating system.
    Args:
        os_type (str): 'Windows' or 'Darwin' for macOS
    Returns:
        Path: Path object to the automation profile directory
    """
    home_dir = Path.home()
    if os_type == 'Windows':
        profile_dir = home_dir / 'automation_profile'
    elif os_type == 'Darwin':
        profile_dir = home_dir / 'automation_profile'
    else:
        logging.error(f"Unsupported Operating System: {os_type}")
        sys.exit(1)
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


def launch_chrome(chrome_path, profile_path, os_type):
    """
    Launches Google Chrome with the specified user data directory to initialize the profile.
    Args:
        chrome_path (Path): Path to the Chrome executable
        profile_path (Path): Path to the automation profile directory
        os_type (str): 'Windows' or 'Darwin' for macOS
    Returns:
        subprocess.Popen: The subprocess running Chrome
    """
    chrome_commands = {
        'Windows': [
            str(chrome_path),
            f'--user-data-dir={str(profile_path)}',
            '--no-first-run',
            '--no-default-browser-check',
        ],
        'Darwin': [
            str(chrome_path),
            f'--user-data-dir={str(profile_path)}',
            '--no-first-run',
            '--no-default-browser-check',
        ],
    }

    try:
        cmd = chrome_commands[os_type]
        logging.info(f"Launching Chrome with command: {' '.join(cmd)}")
        # Start Chrome
        chrome_process = subprocess.Popen(cmd)
        return chrome_process
    except FileNotFoundError:
        logging.error('Google Chrome executable not found.')
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to launch Chrome: {e}")
        sys.exit(1)


def terminate_process(process):
    """
    Terminates the given subprocess.
    Args:
        process (subprocess.Popen): The subprocess to terminate
    """
    try:
        if process.poll() is None:
            logging.info('Terminating Chrome process...')
            process.terminate()
            process.wait(timeout=5)
            logging.info('Chrome process terminated gracefully.')
    except subprocess.TimeoutExpired:
        logging.warning(
            'Chrome process did not terminate in time. Killing process.',
        )
        process.kill()
    except Exception as e:
        logging.error(f"Error terminating Chrome process: {e}")


def main():
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info('=== Starting Chrome Automation Profile Setup ===')

    os_type = get_os_type()
    logger.info(f"Detected Operating System: {os_type}")

    chrome_path = get_chrome_path(os_type)
    logger.info(f"Google Chrome executable found at: {chrome_path}")

    profile_path = get_profile_path(os_type)
    create_profile_directory(profile_path)

    # If the profile directory already has data, prompt the user to clear it
    if any(profile_path.iterdir()):
        logger.warning(f"The profile directory {profile_path} is not empty.")
        response = input(f"Do you want to clear the existing profile data in {
                         profile_path
                         }? (y/n): ").lower()
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
            logger.info(
                'Keeping existing profile data. Proceeding with setup.',
            )
    else:
        logger.info(f"No existing data in profile directory: {profile_path}")

    # Launch Chrome with the custom profile
    chrome_process = launch_chrome(chrome_path, profile_path, os_type)

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
            # Check if Chrome process has terminated
            if chrome_process.poll() is not None:
                logger.info('Chrome process has been closed.')
                break
            time.sleep(1)
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
