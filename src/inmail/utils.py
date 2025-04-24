import logging
import platform
import re
import sys
import time
from datetime import datetime
from datetime import time as dt_time  # Alias time to avoid conflict
from datetime import timedelta
from pathlib import Path

import pytz
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def inject_key_listeners(driver):
    """
    Injects JavaScript into the browser to listen for Enter and Shift keys.
    When Enter is pressed, sets window.keyPressed = 'Enter'.
    When Shift is pressed, sets window.keyPressed = 'Shift'.
    Additionally, logs the key presses in a hidden textarea.
    """
    js_code = """
    (function() {
        // Avoid injecting multiple listeners
        if (window.keyListenersInjected) return;
        window.keyListenersInjected = true;

        // Initialize the keyPressed variable
        window.keyPressed = null;

        // Create a hidden textarea to store key logs
        let keyLogArea = document.getElementById('key-log-area');
        if (!keyLogArea) {
            keyLogArea = document.createElement('textarea');
            keyLogArea.id = 'key-log-area';
            keyLogArea.style.display = 'none'; // Hidden from view
            document.body.appendChild(keyLogArea);
        }

        // Variable to track if Shift is currently pressed
        let isShiftPressed = false;

        document.addEventListener('keydown', function(event) {
            const key = event.key;
            const timestamp = new Date().toISOString();
            let logEntry = `${timestamp}: ${key}\\n`;

            if (key === 'Enter') {
                // Set the window.keyPressed variable
                window.keyPressed = 'Enter';
                console.log('Enter key pressed. Signal sent to Selenium.');
            }

            if (key === 'Shift') {
                if (!isShiftPressed) { // Prevent multiple signals if Shift
                    isShiftPressed = true;
                    // Set the window.keyPressed variable
                    window.keyPressed = 'Shift';
                    console.log('Shift key pressed. Signal sent to Selenium.');
                }
            }

            // Append the log entry
            keyLogArea.value += logEntry;
        });

        document.addEventListener('keyup', function(event) {
            const key = event.key;
            if (key === 'Shift') {
                isShiftPressed = false; // Reset the flag when Shift
            }
        });
    })();
    """
    driver.execute_script(js_code)
    logging.info('Injected Enter and Shift key listeners into the browser.')


def wait_for_key_signal(driver, timeout=300):
    """
    Waits until the window.keyPressed variable is set to 'Enter' or 'Shift'.
    Returns the key that was pressed ('Enter' or 'Shift').
    """
    try:
        logging.info('Waiting for Enter or Shift key signal from the user...')

        # Define the condition to wait
        # until window.keyPressed is 'Enter' or 'Shift'
        def key_pressed(driver):
            try:
                key = driver.execute_script('return window.keyPressed;')
                if key in ['Enter', 'Shift']:
                    return key
                return False
            except Exception:
                return False

        pressed_key = WebDriverWait(driver, timeout).until(key_pressed)

        logging.info(
            f"{pressed_key} key signal detected. Continuing the script...",
        )
        return pressed_key

    except Exception as e:
        logging.error(f"Timeout waiting for key signal: {e}")
        raise e


def get_captured_keys(driver):
    """
    Retrieves and returns the value of the hidden textarea that
      logs Enter and Shift key presses.
    """
    try:
        key_log = driver.find_element(
            By.ID,
            'key-log-area',
        ).get_attribute('value')
        return key_log
    except Exception as e:
        logging.error(f"Failed to retrieve key logs: {e}")
        return ''


def inject_key_logging(driver):
    """
    Injects JavaScript into the browser to log all
    Enter key presses with timestamps.
    The logs are stored in a hidden textarea element.
    """
    js_code = """
    (function() {
        // Avoid injecting multiple listeners
        if (window.keyLoggingInjected) return;
        window.keyLoggingInjected = true;

        // Create a hidden textarea to store key logs
        let keyLogArea = document.getElementById('key-log-area');
        if (!keyLogArea) {
            keyLogArea = document.createElement('textarea');
            keyLogArea.id = 'key-log-area';
            keyLogArea.style.display = 'none'; // Hidden from view
            document.body.appendChild(keyLogArea);
        }

        // Listen for Enter keydown events
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                const timestamp = new Date().toISOString(); // Timestamp
                const logEntry = `${timestamp}: Enter\n`;
                keyLogArea.value += logEntry; // Append to the textarea

                // Optional: Log to the console for debugging
                console.log(`Enter Key Pressed - ${logEntry}`);
            }
        });
    })();
    """
    driver.execute_script(js_code)
    logging.info('Injected Enter key logging into the browser.')


def get_user_data_dir():
    """
    Determines the user data directory for Chrome
      based on the operating system.
    Returns:
        Path: The path to the Chrome user data directory.
    """
    os_type = platform.system()
    home_dir = Path.home()

    if os_type == 'Windows':
        # Path for Windows
        profile_dir = Path(__file__).resolve(
        ).parent.parent / 'automation_profile'
    elif os_type == 'Darwin':
        # Path for macOS
        profile_dir = Path(__file__).resolve(
        ).parent.parent / 'automation_profile'
    else:
        logging.error(f"Unsupported Operating System: {os_type}")
        sys.exit(1)

    return profile_dir


def slugify_company(company_name):
    # Lowercase and replace spaces and special characters with a dash
    slug = re.sub(r'[^\w\s-]', '', company_name).lower().replace(' ', '-')
    return slug


def parse_results_count(results_text):
    # Remove the extra text and whitespace
    cleaned = results_text.upper().replace('RESULTS', '').strip()
    # Remove any plus sign
    cleaned = cleaned.replace('+', '')

    multiplier = 1
    # Check for thousands and millions suffixes
    if 'K' in cleaned:
        multiplier = 1000
        cleaned = cleaned.replace('K', '')
    elif 'M' in cleaned:
        multiplier = 1000000
        cleaned = cleaned.replace('M', '')

    try:
        value = float(cleaned) * multiplier
    except ValueError:
        value = 0
    return int(value)


def wait_until_next_day():
    """
    Sleep (block) until 9 AM CET.
    This stops processing in this thread until the specified time.
    """
    # Get current time in UTC
    now_utc = datetime.now(pytz.utc)

    # Convert to CET
    cet_timezone = pytz.timezone('CET')
    now_cet = now_utc.astimezone(cet_timezone)

    # Calculate next 5 AM CET
    if now_cet.hour >= 5:
        # If it's past 6 AM today, set to 5 AM next day
        next_cet = (now_cet + timedelta(days=1)).replace(
            hour=5,
            minute=0,
            second=0,
            microsecond=0,
        )
    else:
        # If it's before 5 AM today, set to 5 AM today
        next_cet = now_cet.replace(
            hour=5,
            minute=0,
            second=0,
            microsecond=0,
        )

    # Convert the target time back to UTC
    next_utc = next_cet.astimezone(pytz.utc)

    # Calculate the time to wait in seconds
    seconds_to_wait = (next_utc - now_utc).total_seconds()
    print(f"{next_cet=}")
    print(f"{seconds_to_wait=}")
    time.sleep(seconds_to_wait)


def is_within_trading_hours_or_wait(
    start_hour=7, end_hour=21, timezone_str='CET',  # 5 PM is 17:00
):
    """
    Checks if the current time is within the specified trading hours
    [start_hour, end_hour) in the given timezone (e.g., 9:00 AM to 4:59:59 PM).

    If the current time is within the trading hours, returns True immediately.
    If the current time is outside trading hours, it waits (sleeps) until
    the next start_hour (e.g., 9 AM today or 9 AM next day) and then returns True.

    Args:
        start_hour (int): The hour the trading window starts (e.g., 9 for 9 AM). Inclusive.
        end_hour (int): The hour the trading window ends (e.g., 17 for 5 PM). Exclusive.
        timezone_str (str): The timezone string recognized by pytz (e.g., 'CET', 'Europe/Berlin', 'America/New_York').

    Returns:
        True: Always returns True, but might block/wait before doing so if outside trading hours.
    """
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        print(f"Error: Unknown timezone '{timezone_str}'. Using UTC as fallback.")  # noqa: E501
        tz = pytz.utc
        # Adjust hours if timezone was specific, e.g. CET=UTC+1/2 depending on DST
        # This fallback might not be ideal, better to ensure correct timezone_str
        # For simplicity here, we'll just use UTC hours if timezone fails.

    # --- Get Current Time ---
    now_utc = datetime.now(pytz.utc)
    now_local = now_utc.astimezone(tz)
    current_local_time = now_local.time()

    # --- Define Trading Window Times ---
    # Use datetime.time for easy comparison
    trading_start_time = dt_time(start_hour, 0, 0)
    trading_end_time = dt_time(end_hour, 0, 0)

    # --- Check if Within Trading Hours ---
    # The condition is: start_time <= current_time < end_time
    if trading_start_time <= current_local_time < trading_end_time:
        print(f"Current time {now_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')} is within trading hours")  # noqa: E501
        print(f"{start_hour}:00 - {end_hour}:00 {timezone_str}).")
        return True
    else:
        print(
            f"Current time {now_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')} is outside trading hours", # noqa: E501
        )
        print(f"{start_hour}:00 - {end_hour}:00 {timezone_str}).")

        # --- Calculate Next Trading Start Time ---
        # Replace time part of current local datetime with the start hour
        start_datetime_today = now_local.replace(
            hour=start_hour, minute=0, second=0, microsecond=0,
        )

        if now_local.time() >= trading_end_time:
            # If current time is after trading ended today, wait until start time *tomorrow*
            next_start_local = start_datetime_today + timedelta(days=1)
            print(f"Targeting start time tomorrow.")
        else:  # current_local_time < trading_start_time
            # If current time is before trading starts today, wait until start time *today*
            next_start_local = start_datetime_today
            print(f"Targeting start time later today.")

        # --- Calculate Wait Duration and Sleep ---
        # Convert the target local start time back to UTC for accurate comparison
        next_start_utc = next_start_local.astimezone(pytz.utc)

        # Calculate the difference in seconds
        # Use a fresh `now_utc` call to minimize drift during calculation
        wait_duration_seconds = (
            next_start_utc - datetime.now(pytz.utc)
        ).total_seconds()

        if wait_duration_seconds > 0:
            print(
                f"Waiting for {wait_duration_seconds:.2f} seconds until the next window starts at {next_start_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')}.",  # noqa: E501
            )
            time.sleep(wait_duration_seconds)
            print(
                f"Wait finished. Resuming at {
                    datetime.now(pytz.utc).astimezone(
                        tz
                    ).strftime('%Y-%m-%d %H:%M:%S %Z%z')
                }",
            )
            # After waiting, we have reached the start of the next trading period
            return True
        else:
            # If wait duration is zero or negative, it means the start time is now or has just passed.
            # This could happen due to calculation time or clock skew. Proceed immediately.
            print('Calculated wait time is non-positive. Proceeding immediately.')
            return True
