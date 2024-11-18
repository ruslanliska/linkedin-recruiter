import logging
import random
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from src.agents.email_writer import DEFAULT_EMAIL_INSTRUCTION
from src.agents.email_writer import DEFAULT_USER_PROMPT
from src.agents.main import generate_personal_email
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

        linkedin_profile = 'https://www.linkedin.com/in/ruslan-liska/'
        # linkedin_profile = 'https://www.linkedin.com/in/lidia-herrero-coy-64197232/'
        driver.get(linkedin_profile)
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
        # TODO uncomment line for email
        email = generate_personal_email(
            page_summary=cleaned_text,
            user_prompt=prompt,
            email_instructions=reference_email,
        )
        print(email)
        # Find all <code> elements on the page
        code_elements = driver.find_elements(By.TAG_NAME, 'code')

        # Loop through the elements to find the correct one
        profile_id = None
        for code_element in code_elements:
            # Get the inner content of the <code> element
            code_content = code_element.get_attribute('innerHTML')
            import json
            # Check if the desired JSON block exists
            if 'identityDashProfilesByMemberIdentity' in code_content:
                try:
                    # Parse the content as JSON
                    data = json.loads(code_content)

                    # Extract the profile URN
                    profile_urn = data['data']['data']['identityDashProfilesByMemberIdentity']['*elements'][0]

                    # Extract the profile ID
                    profile_id = profile_urn.split(':')[-1]
                    break  # Stop searching once we find the correct block
                except (json.JSONDecodeError, KeyError):
                    # Skip blocks that don't match the structure
                    continue

        # Output the extracted profile ID
        if profile_id:
            print(f"Profile ID: {profile_id}")
        else:
            print('Profile ID not found.')
        # driver.find_element(By.XPATH, '//*[@id="ember79-profile-overflow-action"]').click()
        # driver.find_element(By.XPATH, '//*[@id="ember85"]').click()
        # print('CLICKED')
        time.sleep(random.uniform(2, 5))

        driver.get(
            f'https://www.linkedin.com/talent/profile/{
                profile_id
            }?rightRail=composer',
        )
        time.sleep(random.uniform(5, 8))

        # Locate the subject input field using stable attributes
        subject_input = driver.find_element(
            By.CSS_SELECTOR, "input[aria-label='Message subject'][placeholder='Add a subject']",
        )

        # Click the subject input to activate it (if required)
        subject_input.click()

        # Write the subject
        subject_input.send_keys('Talent Found')
        # Locate the inner contenteditable div
        editor = driver.find_element(
            By.CSS_SELECTOR, ".ql-editor[contenteditable='true']",
        )

        # Click to activate the editor (if required)
        editor.click()

        # Write text into the editor
        # editor.send_keys(email)

        # typing
        # for char in email:
        #     editor.send_keys(char)
        #     time.sleep(0.00001)

        # chunks
        chunk_size = 20  # Number of characters to send in each chunk

        for i in range(0, len(email), chunk_size):
            editor.send_keys(email[i:i + chunk_size])
            time.sleep(0.001)

        time.sleep(random.uniform(5, 8))
        # Locate the send button using its attributes
        send_button = driver.find_element(
            By.CSS_SELECTOR, 'button[data-live-test-messaging-submit-btn]',
        )

        # Check if the button is disabled
        if send_button.get_attribute('disabled'):
            print('Button disabled')
        else:
            send_button.click()
            print('Message sent!')

        # Implement your automation logic here
        # Example placeholder:
        # personalized_message = email_template.format(name=row['Name'])
        # Code to send the message
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

        # Close the WebDriver
        driver.quit()

        # If a callback is provided, call it to indicate success
        if callback:
            callback(
                success=True,
                message='Automation completed successfully.',
            )

    except ZeroDivisionError as e:
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


run_selenium_automation(
    data='', visible_mode=True,
    control_email_sending=False,
)
