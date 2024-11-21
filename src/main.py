import logging
import os
import subprocess
import sys
from pathlib import Path


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
        return Path(__file__).parent.parent


sys.path.append(str(get_application_path()))


def setup_logging():
    """
    Configures logging for the application.
    Logs are written to both the console and a file named 'application.log'.
    """
    # Define log file path
    app_path = get_application_path()
    log_dir = app_path / 'logs'
    # Ensure the logs directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'application.log'

    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,  # Set the minimum logging level
        # Log format
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # Log to console
            logging.FileHandler(log_file, encoding='utf-8'),  # Log to file
        ],
    )

    # Optionally, set the logger for
    # 'undetected_chromedriver' to WARNING to reduce verbosity
    logging.getLogger('undetected_chromedriver').setLevel(logging.WARNING)


def main():
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)  # Get a logger for this module

    logger.info('=== Starting LinkedIn Automation Application ===')

    try:
        # Add the parent directory to PYTHONPATH
        # **after** logging is configured
        sys.path.append(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)),
            ),
        )

        # Now import other modules
        from src.database.setup import create_database
        from src.ui.main_window import LinkedInAutomationApp

        # Initialize the database
        logger.info('Initializing the database...')
        create_database()
        logger.info('Database initialized successfully.')

        # Launch the main application window
        logger.info('Launching the main application window.')
        app = LinkedInAutomationApp()
        app.mainloop()
        logger.info('Application closed gracefully.')

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)


def run_subprocess():
    # Prevent recursion by checking an environment variable
    if os.environ.get('IS_SUBPROCESS'):
        print('This is a subprocess. Exiting to prevent recursion.')
        return

    # Set an environment variable to mark subprocesses
    env = os.environ.copy()
    env['IS_SUBPROCESS'] = '1'

    # Run the subprocess
    args = [sys.executable, __file__]  # Re-invoke the same script
    subprocess.Popen(args, env=env)
    print('Started subprocess with PID:', os.getpid())


def is_frozen():
    """Check if the application is running as a PyInstaller bundle."""
    return getattr(sys, 'frozen', False)


if __name__ == '__main__':
    setup_logging()
    if is_frozen():
        logging.info('Running as a bundled executable.')
        run_subprocess()
    else:
        logging.info('Running in development mode.')
        main()
