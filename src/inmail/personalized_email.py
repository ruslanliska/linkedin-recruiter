# src/inmail/personalized_email.py
import json
import logging
import random
import time
import traceback

import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from src.agents.main import generate_personal_email
from src.database.handlers import log_email
from src.database.handlers import log_run_end
from src.inmail.utils import get_user_data_dir
from src.inmail.utils import inject_key_listeners
from src.inmail.utils import wait_for_key_signal
# Configure logging
logging.basicConfig(level=logging.INFO)


def run_selenium_automation(
    data,
    visible_mode,
    control_email_sending,
    prompt: str = None,
    reference_email: str = None,
    run_id: int = None,
    callback=None,
):
    """
    Runs the Selenium automation process.

    Parameters:
    - data: pandas DataFrame containing the data to process.
    - visible_mode: bool indicating whether to run in visible mode.
    - control_email_sending: bool indicating whether to control email sending.
    - prompt: str containing the user prompt.
    - reference_email: str containing the email instructions.
    - run_id: int containing the unique run identifier.
    - callback: function to call upon completion or error (optional).
    """
    logging.info(f"Run ID: {run_id} - Automation started.")
    driver = None
    run_status = 'Running'
    error_message = None

    try:
        # Set up Selenium WebDriver options
        options = uc.ChromeOptions()

        if not visible_mode:
            options.add_argument('--headless')
        print('USERDATADIR', get_user_data_dir())
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument(f'--user-data-dir={get_user_data_dir()}')
        # options.add_argument(
        #     '--user-data-dir=/Users/ruslanliska/automation_profile',
        # )
        # On Windows: C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data
        # options.add_argument("--user-data-dir=/Users/ruslanliska/Library/Application Support/Google/Chrome")  # Main User Data folder

        # Initialize the WebDriver
        try:
            driver = uc.Chrome(options=options)

            from selenium_stealth import stealth
            stealth(
                driver,
                languages=['en-US', 'en'],
                vendor='Google Inc.',
                platform='Win32',
                webgl_vendor='Intel Inc.',
                renderer='Intel Iris OpenGL Engine',
                fix_hairline=True,
            )
            time.sleep(random.uniform(2, 10))

            logging.info('ChromeDriver initialized successfully.')
        except Exception as e:
            logging.error(
                f"Failed to initialize ChromeDriver automatically: {e}",
            )
            run_status = 'Failed'
            error_message = f"ChromeDriver Initialization Error: {e}"
            log_run_end(
                run_id=run_id, status=run_status,
                error_message=error_message,
            )
            if callback:
                callback(success=False, message=error_message)
            return  # Exit the function as WebDriver is essential

        # Process each item in the data
        for index, row in data.iterrows():
            try:
                email = None
                email_status = None
                error_message = None
                linkedin_profile = row['Person Linkedin Url']

                driver.get(linkedin_profile)

                from bs4 import BeautifulSoup

                full_html = driver.page_source
                soup = BeautifulSoup(full_html, 'html.parser')

                desired_tags = ['main']
                text_from_desired_tags = []
                for tag in soup.find_all(desired_tags):
                    tag_text = tag.get_text(separator=' ', strip=True)
                    if tag_text:
                        text_from_desired_tags.append(tag_text)

                cleaned_text = '\n'.join(text_from_desired_tags)
                # Log a snippet
                logging.debug(f"Cleaned Text: {cleaned_text[:100]}...")

                # Generate the personal email
                email = generate_personal_email(
                    page_summary=cleaned_text,
                    user_prompt=prompt,
                    email_instructions=reference_email,
                )

                # Extract profile ID from <code> elements
                code_elements = driver.find_elements(By.TAG_NAME, 'code')
                profile_id = None
                for code_element in code_elements:
                    code_content = code_element.get_attribute('innerHTML')
                    if 'identityDashProfilesByMemberIdentity' in code_content:
                        try:
                            data_json = json.loads(code_content)
                            profile_urn = data_json['data']['data']['identityDashProfilesByMemberIdentity']['*elements'][0]
                            profile_id = profile_urn.split(':')[-1]
                            break
                        except (json.JSONDecodeError, KeyError) as e:
                            logging.warning(f"JSON parsing error: {e}")
                            continue

                if profile_id:
                    logging.info(f"Extracted Profile ID: {profile_id}")
                else:
                    logging.warning('Profile ID not found.')
                    raise ValueError('Profile ID extraction failed.')

                # Navigate to the messaging composer
                driver.get(
                    f'https://www.linkedin.com/talent/profile/{
                        profile_id
                    }?rightRail=composer',
                )

                time.sleep(random.uniform(10, 20))
                # Locate and interact with the subject input field
                subject_input = driver.find_element(
                    By.CSS_SELECTOR, "input[aria-label='Message subject'][placeholder='Add a subject']",
                )
                subject_input.click()
                subject_input.send_keys('Staffing Partner')

                # Locate and interact with the email editor
                editor = driver.find_element(
                    By.CSS_SELECTOR, ".ql-editor[contenteditable='true']",
                )
                editor.click()

                # Type the email in chunks to mimic human typing
                chunk_size = 20
                for i in range(0, len(email), chunk_size):
                    editor.send_keys(email[i:i + chunk_size])

                # Control email sending if required
                if control_email_sending:
                    inject_key_listeners(driver)

                    try:
                        pressed_key = wait_for_key_signal(
                            driver, timeout=300,
                        )  # 5 minutes
                        logging.info(f"Key pressed: {pressed_key}")

                        if pressed_key == 'Enter':
                            logging.info(
                                'Enter key was pressed. Proceeding with email sending.',
                            )
                        elif pressed_key == 'Backspace':
                            logging.info(
                                'Backspace key was pressed. Skipping email sending.',
                            )
                            email_status = 'Skipped'
                            log_email(
                                run_id=run_id,
                                linkedin_profile_url=linkedin_profile,
                                email_text=email,
                                email_status=email_status,
                                error_message='User skipped sending.',
                            )
                            continue
                        else:
                            logging.warning('Unrecognized key press detected.')
                            email_status = 'Failed'
                            error_message = 'Unrecognized key press.'
                            log_email(
                                run_id=run_id,
                                linkedin_profile_url=linkedin_profile,
                                email_text=email,
                                email_status=email_status,
                                error_message=error_message,
                            )
                            continue
                    except TimeoutException:
                        logging.error(
                            'Timeout: No key press detected within the timeout period.',
                        )
                        email_status = 'Failed'
                        error_message = 'Timeout waiting for user input.'
                        log_email(
                            run_id=run_id,
                            linkedin_profile_url=linkedin_profile,
                            email_text=email,
                            email_status=email_status,
                            error_message=error_message,
                        )
                        continue

                # Locate and interact with the send button
                send_button = driver.find_element(
                    By.CSS_SELECTOR, 'button[data-live-test-messaging-submit-btn]',
                )

                if send_button.get_attribute('disabled'):
                    email_status = 'Failed'
                    error_message = 'Send button disabled.'
                    logging.warning('Send button is disabled.')
                else:
                    send_button.click()
                    email_status = 'Sent'
                    logging.info('Message sent successfully.')

                # Log the email sending result
                log_email(
                    run_id=run_id,
                    linkedin_profile_url=linkedin_profile,
                    email_text=email,
                    email_status=email_status,
                    error_message=error_message,
                )

            except Exception as e:
                email_status = 'Failed'
                error_message = str(e)
                logging.error(f"Error processing profile {
                              linkedin_profile}: {e}")
                logging.debug(traceback.format_exc())
                # Log the error for this email
                log_email(
                    run_id=run_id,
                    linkedin_profile_url=linkedin_profile,
                    email_text=email if email else '',
                    email_status=email_status,
                    error_message=error_message,
                )
                continue

        # Update run status to Completed
        run_status = 'Completed'
        log_run_end(
            run_id=run_id, status=run_status,
            error_message='Run completed successfully.',
        )
        logging.info(f"Run ID: {run_id} - Automation completed successfully.")

        # Invoke the callback to indicate success
        if callback:
            callback(
                success=True,
                message='Automation completed successfully.',
            )

    except KeyboardInterrupt:
        run_status = 'Interrupted'
        error_message = 'Run was interrupted by the user (KeyboardInterrupt).'
        logging.warning(error_message)
        log_run_end(
            run_id=run_id, status=run_status,
            error_message=error_message,
        )

        if callback:
            callback(
                success=False,
                message=error_message,
            )

    except Exception as e:
        run_status = 'Failed'
        error_message = f"An unexpected error occurred: {e}"
        logging.error(error_message)
        logging.debug(traceback.format_exc())
        log_run_end(
            run_id=run_id, status=run_status,
            error_message=error_message,
        )

        if callback:
            callback(
                success=False,
                message=error_message,
            )

    finally:
        # Ensure the WebDriver is properly closed
        if driver:
            driver.quit()
            logging.info('WebDriver has been closed.')

        # If the run was interrupted or failed, ensure the run end is logged
        if run_id and run_status not in ['Completed', 'Failed', 'Interrupted']:
            run_status = 'Failed'
            error_message = 'Run ended unexpectedly.'
            log_run_end(
                run_id=run_id, status=run_status,
                error_message=error_message,
            )
            if callback:
                callback(
                    success=False,
                    message=error_message,
                )
