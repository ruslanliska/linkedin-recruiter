import json
import logging
import random
import time
import traceback

import pandas as pd
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.agents.main import generate_personal_email
from src.database.handlers import log_email
from src.database.handlers import log_run_end
from src.inmail.utils import get_user_data_dir
from src.inmail.utils import inject_key_listeners
from src.inmail.utils import slugify_company
from src.inmail.utils import wait_for_key_signal


# Configure logger
logger = logging.getLogger(__name__)


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
    logger.info(f"Run ID: {run_id} - Automation started.")
    driver = None
    run_status = 'Running'
    error_message = None
    iteration_count = 0

    try:
        # Set up Selenium WebDriver options
        options = uc.ChromeOptions()

        if not visible_mode:
            options.add_argument('--headless')
        logger.info(f'Chrome directory: {get_user_data_dir()}')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument(f'--user-data-dir={get_user_data_dir()}')

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

            logger.info('ChromeDriver initialized successfully.')
        except Exception as e:
            logger.error(
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
            iteration_count += 1
            if iteration_count % 2 == 0:
                logger.info(f"Restarting ChromeDriver. {iteration_count=}")
                driver.quit()
                # Set up Selenium WebDriver options
                options = uc.ChromeOptions()

                if not visible_mode:
                    options.add_argument('--headless')
                logger.info(f'Chrome directory: {get_user_data_dir()}')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--start-maximized')
                options.add_argument(f'--user-data-dir={get_user_data_dir()}')

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
            try:
                email = None
                email_status = None
                error_message = None
                linkedin_profile = row['Person Linkedin Url']
                logger.info(f"Processing row {index}: {linkedin_profile=}")
                profile_email_address = row['Email']
                if pd.isna(profile_email_address):
                    logger.warning(
                        f"Guessing email for row {
                            index
                        } due to missing email address.",
                    )
                    first_name = row['First Name'].lower()
                    last_name = row['Last Name'].lower()
                    company_slug = slugify_company(row['Company'])
                    profile_email_address = (
                        f"{first_name}.{last_name}@{company_slug}.com"
                    )
                    logger.info(f'Guessed {profile_email_address=}')

                # Force a hard reload
                driver.execute_script('location.reload(true);')
                time.sleep(random.uniform(4, 7))

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
                logger.debug(f"Cleaned Text: {cleaned_text[:100]}...")

                # Generate the personal email
                email, subject = generate_personal_email(
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
                            profile_urn = data_json['data']['data']['identityDashProfilesByMemberIdentity']['*elements'][0]  # noqa:E501
                            profile_id = profile_urn.split(':')[-1]
                            break
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"JSON parsing error: {e}")
                            continue

                if profile_id:
                    logger.info(f"Extracted Profile ID: {profile_id}")
                else:
                    logger.warning('Profile ID not found.')
                    raise ValueError('Profile ID extraction failed.')

                # Navigate to the messaging composer
                logger.debug(
                    f'Navigate to https://www.linkedin.com/talent/profile/{
                        profile_id
                    }',
                )
                driver.get(
                    f'https://www.linkedin.com/talent/profile/{profile_id}',
                )

                time.sleep(random.uniform(10, 20))

                # Wait for the contact info element to load
                contact_info = driver.find_element(
                    By.CLASS_NAME, 'contact-info',
                )

                # Check if an email already exists
                try:
                    existing_email = contact_info.find_element(
                        By.XPATH, './/span[@data-test-contact-email-address]',
                    )
                    logger.debug(f"Email found: {existing_email.text}")
                except NoSuchElementException:
                    # If no email exists, look for the "Add email" button
                    logger.debug(
                        "No email found. Looking for 'Add email' button...",
                    )
                    add_email_button = driver.find_element(
                        By.XPATH, ".//button[@class='button-small-muted-tertiary contact-info__add']",  # noqa:E501
                    )
                    logger.debug("Clicking on the 'Add email' button...")
                    add_email_button.click()
                    # Wait for the email input field to appear
                    email_input = driver.find_element(
                        By.XPATH, ".//input[@type='email']",
                    )

                    logger.debug('Email input field found. Sending keys...')
                    email_input.send_keys(profile_email_address)
                    logger.debug("Clicking on the 'Save' button...")

                    # Simulate pressing the Enter key
                    email_input.send_keys(Keys.ENTER)
                    logger.debug('Email saved')
                    # Wait for the email to be saved
                    time.sleep(random.uniform(4, 7))

                driver.refresh()
                time.sleep(random.uniform(4, 7))

                email_button = driver.find_element(
                    By.XPATH, "//button[contains(@class, 'artdeco-button') and contains(@data-live-test-component, 'message-icon-btn')]",  # noqa:E501
                )
                email_button.click()
                time.sleep(random.uniform(4, 7))

                # Locate the parent element
                send_info = driver.find_element(
                    By.XPATH, "//div[contains(@class, 'single-message-composer__trigger-message')]",  # noqa:E501
                )

                # Extract the text
                text_content = send_info.text.strip()

                # Check the content
                if 'Send immediately via InMail' in text_content:
                    logger.info(
                        'The text indicates "Send immediately via InMail".',
                    )
                    # Locate the button using find_element and click it
                    settings_button = driver.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'single-message-composer__trigger-message-gear-icon')]",  # noqa:E501
                    )
                    settings_button.click()
                    time.sleep(random.uniform(3, 6))

                    # Wait for the modal to become visible

                    modal = driver.find_element(
                        By.XPATH,
                        "//div[contains(@class, 'inline-modal__overlay')]",
                    )
                    time.sleep(random.uniform(4, 6))

                    # Locate the "Email" radio button by its value and click it
                    email_radio_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//input[@type='radio' and @value='EMAIL']",
                            ),
                        ),
                    )
                    # Scroll the element into view
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        email_radio_button,
                    )

                    time.sleep(random.uniform(4, 6))

                    # Use JavaScript to ensure the exact element is clicked
                    driver.execute_script(
                        'arguments[0].click();', email_radio_button,
                    )

                    # Optional: Click the "Save" button in the modal
                    save_button = modal.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'artdeco-button--secondary') and span[text()='Save']]",  # noqa:E501
                    )
                    save_button.click()

                    try:
                        # Locate the <h3> element
                        error_message_element = driver.find_element(
                            By.XPATH,
                            "//h3[contains(@class, 'trigger-conditions-modal__message-channel-error')]",  # noqa:E501
                        )

                        # Check if the element is visible
                        if error_message_element.is_displayed():
                            logger.warning(
                                'Error message. No recipient email found. Select InMail instead.',  # noqa:E501
                            )
                            # Force a hard reload
                            driver.execute_script('location.reload(true);')
                            continue
                        else:
                            logger.info(
                                'Error message is not visible. Continue with Email.',  # noqa:E501
                            )
                    except NoSuchElementException:
                        logger.debug('Error message element not found.')

                elif 'Send immediately via Email' in text_content:
                    logger.info(
                        "The text indicates 'Send immediately via Email'.",
                    )
                else:
                    logger.warning('The text for send is changed.')

                # Locate and interact with the subject input field
                subject_input = driver.find_element(
                    By.CSS_SELECTOR,
                    "input[aria-label='Message subject'][placeholder='Add a subject']",  # noqa:E501
                )
                subject_input.click()
                subject_input.send_keys(subject)

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
                        logger.info(f"Key pressed: {pressed_key}")

                        if pressed_key == 'Enter':
                            logger.info(
                                'Enter key was pressed. Proceeding with email sending.',  # noqa:E501
                            )
                        elif pressed_key == 'Backspace':
                            logger.info(
                                'Backspace key was pressed. Skipping email sending.',  # noqa:E501
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
                            logger.warning('Unrecognized key press detected.')
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
                        logger.error(
                            'Timeout: No key press detected within the timeout period.',  # noqa:E501
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
                    By.CSS_SELECTOR,
                    'button[data-live-test-messaging-submit-btn]',
                )

                if send_button.get_attribute('disabled'):
                    email_status = 'Failed'
                    error_message = 'Send button disabled.'
                    logger.warning('Send button is disabled.')
                else:
                    send_button.click()
                    email_status = 'Sent'
                    logger.info('Message sent successfully.')
                    time.sleep(random.uniform(4, 7))

                # Log the email sending result
                log_email(
                    run_id=run_id,
                    linkedin_profile_url=linkedin_profile,
                    email_text=email,
                    email_status=email_status,
                    error_message=error_message,
                )
                time.sleep(random.uniform(61, 82))
                # Force a hard reload
                driver.execute_script('location.reload(true);')
                logger.info('Page refreshed.')

            except Exception as e:
                email_status = 'Failed'
                error_message = str(e)
                logger.error(f"Error processing profile {linkedin_profile}: {e}")  # noqa:E501
                logger.debug(traceback.format_exc())
                # Log the error for this email
                log_email(
                    run_id=run_id,
                    linkedin_profile_url=linkedin_profile,
                    email_text=email if email else '',
                    email_status=email_status,
                    error_message=error_message,
                )
                # Force a hard reload
                driver.execute_script('location.reload(true);')
                logger.info('Page refreshed.')
                continue

        # Update run status to Completed
        run_status = 'Completed'
        log_run_end(
            run_id=run_id, status=run_status,
            error_message='Run completed successfully.',
        )
        logger.info(f"Run ID: {run_id} - Automation completed successfully.")

        # Invoke the callback to indicate success
        if callback:
            callback(
                success=True,
                message='Automation completed successfully.',
            )

    except KeyboardInterrupt:
        run_status = 'Interrupted'
        error_message = 'Run was interrupted by the user (KeyboardInterrupt).'
        logger.warning(error_message)
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
        logger.error(error_message)
        logger.debug(traceback.format_exc())
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
            logger.info('WebDriver has been closed.')

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
