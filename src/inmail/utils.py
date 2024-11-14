import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def inject_enter_key_listener(driver):
    """
    Injects JavaScript into the browser to listen for the Enter key.
    When Enter is pressed, a hidden DOM element is added as a signal.
    """
    js_code = """
    (function() {
        // Avoid injecting multiple listeners
        if (window.enterKeyListenerInjected) return;
        window.enterKeyListenerInjected = true;

        document.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                // Check if the signal element already exists
                let signalElement = document.getElementById('enter-key-signal');
                if (!signalElement) {
                    signalElement = document.createElement('div');
                    signalElement.id = 'enter-key-signal';
                    signalElement.style.display = 'none';
                    document.body.appendChild(signalElement);
                }
                console.log('Enter key pressed. Signal sent to Selenium.');
            }
        });
    })();
    """
    driver.execute_script(js_code)
    logging.info('Injected Enter key listener into the browser.')


def wait_for_enter_key_signal(driver, timeout=300):
    """
    Waits until the hidden signal element is present in the DOM,
    indicating that the Enter key has been pressed.
    """
    try:
        logging.info('Waiting for Enter key signal from the user...')
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, 'enter-key-signal')),
        )
        logging.info('Enter key signal detected. Continuing the script...')
    except Exception as e:
        logging.error(f"Timeout waiting for Enter key signal: {e}")
        raise e


def get_captured_keys(driver):
    """
    Retrieves and returns the value of the hidden textarea that logs Enter key presses.
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
