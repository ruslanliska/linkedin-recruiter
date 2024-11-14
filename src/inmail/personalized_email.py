import logging
import random
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from src.inmail.utils import *
# Configure logging
logging.basicConfig(level=logging.INFO)


def run_selenium_automation(
    data,
    visible_mode,
    control_email_sending,
    prompt: str = None,
    reference_email: str = None,
    callback=None,
):
    """
    Runs the Selenium automation process.

    Parameters:
    - linkedin_email: str containing the user's LinkedIn email.
    - linkedin_password: str containing the user's LinkedIn password.
    - data: pandas DataFrame containing the data to process.
    - visible_mode: bool indicating whether to run in visible mode.
    - email_template: str containing the email template.
    - callback: function to call upon completion or error (optional).
    """
    print(f'{prompt=}')
    print(f'{reference_email=}')
    driver = None
    try:
        # Set up Selenium WebDriver options
        options = uc.ChromeOptions()

        if not visible_mode:
            options.add_argument('--headless')

        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument(
            '--user-data-dir=/Users/ruslanliska/automation_profile',
        )

        # On Windows: C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data
        # options.add_argument("--user-data-dir=/Users/ruslanliska/Library/Application Support/Google/Chrome")  # Main User Data folder

        # Specify the exact profile you want to use
        # options.add_argument("--profile-directory=Profile 11")
        # Initialize the WebDriver
        try:
            # driver = uc.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver = uc.Chrome(options=options)

            from selenium_stealth import stealth
            stealth(
                driver, languages=['en-US', 'en'],
                vendor='Google Inc.',
                platform='Win32',
                webgl_vendor='Intel Inc.',
                renderer='Intel Iris OpenGL Engine',
                fix_hairline=True,
            )
            time.sleep(random.uniform(2, 5))

            logging.info('ChromeDriver initialized successfully.')
        except Exception as e:
            logging.error(
                f"Failed to initialize ChromeDriver automatically: {e}",
            )

        # Process each item in the data
        # for index, row in data.iterrows():
        #     linkedin_url = row['Person Linkedin Url']
        #     email = row['Email']
        #     # Perform automation steps
        #     driver.get(linkedin_url)
        #     time.sleep(2)  # Wait for the page to load

        # Clear the flag in case this part of the script runs again
        driver.get('https://www.linkedin.com')
        time.sleep(2)
        if control_email_sending:
            # Inject JavaScript listeners for Enter and Backspace keys
            inject_key_listeners(driver)

            # Provide instructions to the user
            print('Please perform the necessary actions in the browser.')
            print(
                'Once done, press the **Enter** or **Backspace** key within the browser to continue...',
            )

            # Wait for the user to press Enter or Backspace
            pressed_key = wait_for_key_signal(
                driver, timeout=300,
            )  # Timeout after 5 minutes

            # After key press, retrieve the captured keys
            captured_keys = get_captured_keys(driver)
            print('Captured Key Presses:')
            print(captured_keys)

            # Execute different logic based on the key pressed
            if pressed_key == 'Enter':
                print('Enter key was pressed. Executing Enter-specific logic...')
                # Add your Enter key specific logic here
                # Example: Proceed to the next step
            elif pressed_key == 'Shift':
                print('X key was pressed. Executing Backspace-specific logic...')
                # Add your Backspace key specific logic here
                # Example: Perform a different action or exit
            else:
                print('Unrecognized key press detected.')

        linkedin_profile = 'https://www.linkedin.com/in/ruslan-liska/'
        driver.get(linkedin_profile)
        time.sleep(12)
        # Get the full page HTML
        from bs4 import BeautifulSoup

        full_html = driver.page_source
        print('Full HTML Content:')
        print('FINISH PERSONALISED')
        # print(full_html)  # This prints the full HTML of the page

        # Optional: Parse the HTML with BeautifulSoup to extract only the visible text
        soup = BeautifulSoup(full_html, 'html.parser')

        desired_tags = ['main']
        text_from_desired_tags = []
        for tag in soup.find_all(desired_tags):
            tag_text = tag.get_text(separator=' ', strip=True)
            if tag_text:  # Only add non-empty text
                text_from_desired_tags.append(tag_text)

        # Join the text from desired tags, with each entry on a new line
        cleaned_text = '\n'.join(text_from_desired_tags)

        print('\nCleaned Visible Page Text:')
        # print(cleaned_text)
        # create_email(cleaned_text)
        print('FINISH PERONAKL')
        filename = 'page_text_output.txt'

        # Write the cleaned text to a text file
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(cleaned_text)

        print(f"Text content successfully written to {filename}")

        # Implement your automation logic here
        # Example placeholder:
        # personalized_message = email_template.format(name=row['Name'])
        # Code to send the message

        # Close the WebDriver
        driver.quit()

        # If a callback is provided, call it to indicate success
        if callback:
            callback(
                success=True,
                message='Automation completed successfully.',
            )

    except Exception as e:
        # If a callback is provided, call it to indicate an error
        if callback:
            callback(
                success=False,
                message=f'An error occurred during automation:\n{e}',
            )
        logging.error(f"Error during Selenium automation: {e}")
    finally:
        # Ensure the driver is quit in case of exceptions
        if driver:
            driver.quit()
            logging.info('Automation complete. Browser closed.')
