import logging
import os
import sys
from pathlib import Path


def setup_logging():
    """
    Configures logging for the application.
    Logs are written to both the console and a file named 'application.log'.
    """
    # Define log file path
    log_dir = Path(__file__).resolve().parent.parent / 'logs'
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


if __name__ == '__main__':
    main()
