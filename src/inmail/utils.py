import logging

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
                if (!isShiftPressed) { // Prevent multiple signals if Shift is held down
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
                isShiftPressed = false; // Reset the flag when Shift is released
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

        # Define the condition to wait until window.keyPressed is 'Enter' or 'Shift'
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
            f'{pressed_key} key signal detected. Continuing the script...',
        )
        return pressed_key

    except Exception as e:
        logging.error(f"Timeout waiting for key signal: {e}")
        raise e


def get_captured_keys(driver):
    """
    Retrieves and returns the value of the hidden textarea that logs Enter and Shift key presses.
    """
    try:
        key_log = driver.find_element(
            By.ID, 'key-log-area',
        ).get_attribute('value')
        return key_log
    except Exception as e:
        logging.error(f"Failed to retrieve key logs: {e}")
        return ''


def inject_key_logging(driver):
    """
    Injects JavaScript into the browser to log all Enter key presses with timestamps.
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
                const timestamp = new Date().toISOString(); // Timestamp for each key press
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
