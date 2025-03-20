import json
import logging
import random
import socket
import time
import traceback

import pandas as pd
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.agents.main import generate_personal_email
from src.agents.subject_writer import generate_subject
from src.config import settings
from src.database.handlers import log_email
from src.database.handlers import log_run_end
from src.inmail.utils import get_user_data_dir
from src.inmail.utils import inject_key_listeners
from src.inmail.utils import slugify_company
from src.inmail.utils import wait_for_key_signal

socket.setdefaulttimeout(60)  # Set global timeout to 60 seconds


# Configure logger
logger = logging.getLogger(__name__)


socket.setdefaulttimeout(60)  # Set global timeout to 60 seconds
logger = logging.getLogger(__name__)


def process_chunk_of_rows(
    batch_df,
    visible_mode,
    control_email_sending,
    prompt,
    reference_email,
    run_id,
    email_subject,
):
    """
    Process a batch (chunk) of rows in one WebDriver session.
    """
    driver = None
    error_message = None

    try:
        # === 1) Initialize WebDriver once for this batch ===
        options = uc.ChromeOptions()
        if not visible_mode:
            options.add_argument('--headless')

        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument(f"--user-data-dir={get_user_data_dir()}")
        print(f"{settings.DRIVER_PATH=}")
        # driver = uc.Chrome(options=options)  # auto-detect
        driver = uc.Chrome(
            options=options,
            driver_executable_path=r'C:\Users\RebeccaHannan\linkedin-automation\linkedin-recruiter\chromedriver.exe',
        )

        # Optional: stealth, if you want to keep it
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
        time.sleep(random.uniform(2, 5))

        logger.info('ChromeDriver initialized successfully for this batch.')

        # === 2) Loop through all rows in this chunk ===
        for index, row in batch_df.iterrows():
            try:
                email_status = None
                error_message = None
                linkedin_profile = row['Person Linkedin Url']
                logger.info(
                    f"Processing row {index}: {linkedin_profile=}",
                )

                profile_email_address = row['Email']
                if pd.isna(profile_email_address):
                    # Guess the email if missing
                    logger.warning(f"Guessing email for row {index}")
                    first_name = row['First Name'].lower()
                    last_name = row['Last Name'].lower()
                    company_slug = slugify_company(row['Company'])
                    profile_email_address = (
                        f"{first_name}.{last_name}@{company_slug}.com"
                    )
                    logger.info(
                        f"Guessed {profile_email_address=}",
                    )

                # Navigate directly to the profile
                # (You can remove these forced reloads if not strictly needed)
                driver.get(linkedin_profile)
                time.sleep(random.uniform(4, 7))

                # Extract main content from the page
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
                logger.debug(f"Cleaned Text snippet: {cleaned_text[:100]}...")

                # Generate the personal email
                email = generate_personal_email(
                    page_summary=cleaned_text,
                    user_prompt=prompt,
                    email_instructions=reference_email,
                )
                if not email_subject:
                    subject = generate_subject(email_body=email)
                    logger.info(f"Email Subject by AI: {subject}")

                else:
                    subject = email_subject
                    logger.info(f"Email Subject Default: {subject}")

                # Extract profile ID from <code> elements
                code_elements = driver.find_elements(By.TAG_NAME, 'code')
                profile_id = None
                for code_element in code_elements:
                    code_content = code_element.get_attribute('innerHTML')
                    if 'identityDashProfilesByMemberIdentity' in code_content:
                        try:
                            data_json = json.loads(code_content)
                            profile_urn = data_json['data']['data'][
                                'identityDashProfilesByMemberIdentity'
                            ]['*elements'][
                                0
                            ]  # noqa: E501
                            profile_id = profile_urn.split(':')[-1]
                            break
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"JSON parsing error: {e}")
                            continue

                if not profile_id:
                    logger.warning('Profile ID not found.')
                    raise ValueError('Profile ID extraction failed.')

                logger.info(f"Extracted Profile ID: {profile_id}")

                # Navigate to messaging composer
                target_url = f"https://www.linkedin.com/talent/profile/{profile_id}"  # noqa: E501
                logger.debug(f"Navigate to {target_url}")
                driver.get(target_url)
                time.sleep(random.uniform(10, 20))

                # Wait for the contact info element
                contact_info = driver.find_element(
                    By.CLASS_NAME,
                    'contact-info',
                )

                # Check if email is saved
                try:
                    existing_email = contact_info.find_element(
                        By.XPATH,
                        './/span[@data-test-contact-email-address]',
                    )
                    logger.debug(f"Email found: {existing_email.text}")
                except NoSuchElementException:
                    # If no email, add it
                    logger.debug(
                        "No email found. Looking for 'Add email' button...",
                    )
                    add_email_button = driver.find_element(
                        By.XPATH,
                        ".//button[@class='button-small-muted-tertiary contact-info__add']",  # noqa: E501
                    )
                    add_email_button.click()
                    email_input = driver.find_element(
                        By.XPATH,
                        ".//input[@type='email']",
                    )
                    email_input.send_keys(profile_email_address)
                    email_input.send_keys(Keys.ENTER)
                    logger.debug('Email saved')
                    time.sleep(random.uniform(4, 7))

                driver.refresh()
                time.sleep(random.uniform(4, 7))

                # Open message composer
                email_button = driver.find_element(
                    By.XPATH,
                    "//button[contains(@class, 'artdeco-button') and contains(@data-live-test-component, 'message-icon-btn')]",  # noqa: E501
                )
                email_button.click()
                time.sleep(random.uniform(4, 7))

                # Detect if it's InMail or Email
                send_info = driver.find_element(
                    By.XPATH,
                    "//div[contains(@class, 'single-message-composer__trigger-message')]",  # noqa: E501
                )
                text_content = send_info.text.strip()

                if 'Send immediately via InMail' in text_content:
                    logger.info(
                        'Detected: Send immediately via InMail -> switching to Email',  # noqa: E501
                    )
                    settings_button = driver.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'single-message-composer__trigger-message-gear-icon')]",  # noqa: E501
                    )
                    settings_button.click()
                    time.sleep(random.uniform(3, 6))

                    # Wait for the modal, switch to Email
                    modal = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located(
                            (
                                By.XPATH,
                                "//div[@role='dialog' and contains(@class, 'inline-modal__container')]",  # noqa: E501
                            ),
                        ),
                    )
                    # Click the Email radio label
                    email_label = WebDriverWait(modal, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, ".//label[normalize-space(.)='Email']"),
                        ),
                    )
                    driver.execute_script('arguments[0].click();', email_label)
                    time.sleep(random.uniform(1, 2))

                    save_button = WebDriverWait(modal, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                ".//button[.//span[contains(normalize-space(), 'Save')]]",  # noqa: E501
                            ),
                        ),
                    )
                    driver.execute_script('arguments[0].click();', save_button)
                    time.sleep(random.uniform(2, 4))

                    # Check for error
                    try:
                        error_message_element = driver.find_element(
                            By.XPATH,
                            "//h3[contains(@class, 'trigger-conditions-modal__message-channel-error')]",  # noqa: E501
                        )
                        if error_message_element.is_displayed():
                            logger.warning(
                                'Error: No recipient email found. Switching to InMail instead.',  # noqa: E501
                            )
                            # Possibly skip or handle differently
                            driver.refresh()
                            time.sleep(random.uniform(4, 7))

                            continue
                    except NoSuchElementException:
                        pass

                elif 'Send immediately via Email' in text_content:
                    logger.info('Detected: Send immediately via Email')

                else:
                    logger.warning(
                        'Unknown message mode text. Proceed carefully.',
                    )

                # Fill in subject
                subject_input = driver.find_element(
                    By.CSS_SELECTOR,
                    "input[aria-label='Message subject'][placeholder='Add a subject']",  # noqa: E501
                )
                subject_input.click()
                subject_input.send_keys(subject)

                # Fill in the message body
                editor = driver.find_element(
                    By.CSS_SELECTOR,
                    ".ql-editor[contenteditable='true']",
                )
                editor.click()

                chunk_size = 20
                for i in range(0, len(email), chunk_size):
                    editor.send_keys(email[i: i + chunk_size])

                # If control_email_sending, wait for user key press
                if control_email_sending:
                    inject_key_listeners(driver)
                    try:
                        pressed_key = wait_for_key_signal(
                            driver,
                            timeout=300,
                        )  # 5 min
                        logger.info(f"Key pressed: {pressed_key}")
                        if pressed_key == 'Enter':
                            logger.info('User pressed Enter -> sending email.')
                        elif pressed_key == 'Backspace':
                            logger.info('User pressed Backspace -> skipping.')
                            email_status = 'Skipped'
                            log_email(
                                run_id=run_id,
                                linkedin_profile_url=linkedin_profile,
                                email_text=email,
                                email_status=email_status,
                                error_message='User skipped sending.',
                                row_number=index,
                            )
                            continue
                        else:
                            logger.warning('Unrecognized key press.')
                            email_status = 'Failed'
                            error_message = 'Unrecognized key press.'
                            log_email(
                                run_id=run_id,
                                linkedin_profile_url=linkedin_profile,
                                email_text=email,
                                email_status=email_status,
                                error_message=error_message,
                                row_number=index,
                            )
                            continue
                    except TimeoutException:
                        logger.error('Timeout waiting for user input.')
                        email_status = 'Failed'
                        error_message = 'Timeout waiting for user input.'
                        log_email(
                            run_id=run_id,
                            linkedin_profile_url=linkedin_profile,
                            email_text=email,
                            email_status=email_status,
                            error_message=error_message,
                            row_number=index,
                        )
                        continue

                # Send
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

                # Log email result
                log_email(
                    run_id=run_id,
                    linkedin_profile_url=linkedin_profile,
                    email_text=email,
                    email_status=email_status,
                    error_message=error_message,
                    row_number=index,
                )

                # Optional: reload or navigate to next.
                # If you do not need a reload here, you can remove it.
                driver.refresh()
                logger.info('Page refreshed.')
                time.sleep(random.uniform(15, 60))

            except Exception as e:
                # Per-row error
                email_status = 'Failed'
                error_message = str(e)
                logger.error(
                    f"Error processing profile {linkedin_profile}: {e}",
                )  # noqa: E501
                logger.debug(traceback.format_exc())
                log_email(
                    run_id=run_id,
                    linkedin_profile_url=linkedin_profile,
                    email_text='',  # or email if defined
                    email_status=email_status,
                    error_message=error_message,
                    row_number=index,
                )
                # Attempt reload and continue
                driver.refresh()
                logger.info('Page refreshed.')
                time.sleep(random.uniform(3, 6))
                continue

    finally:
        if driver:
            driver.quit()
            logger.info('WebDriver has been closed for this batch.')


def run_selenium_automation(
    data: pd.DataFrame,
    visible_mode: bool,
    control_email_sending: bool,
    prompt: str = None,
    reference_email: str = None,
    run_id: int = None,
    callback=None,
    batch_size: int = 50,  # Adjust as needed
):
    logger.info(f"Run ID: {run_id} - Automation started.")
    run_status = 'Running'
    error_message = None

    try:
        total_rows = len(data)
        start_index = 0

        while start_index < total_rows:
            end_index = min(start_index + batch_size, total_rows)
            batch_df = data.iloc[start_index:end_index]

            logger.info(
                f"Processing batch rows {start_index} to {end_index - 1}",
            )  # noqa: E501
            process_chunk_of_rows(
                batch_df=batch_df,
                visible_mode=visible_mode,
                control_email_sending=control_email_sending,
                prompt=prompt,
                reference_email=reference_email,
                run_id=run_id,
            )

            start_index = end_index

        # If we reach here, we processed all batches
        run_status = 'Completed'
        log_run_end(
            run_id=run_id,
            status=run_status,
            error_message='Run completed successfully.',
        )
        logger.info(f"Run ID: {run_id} - Automation completed successfully.")
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
            run_id=run_id,
            status=run_status,
            error_message=error_message,
        )
        if callback:
            callback(success=False, message=error_message)

    except Exception as e:
        run_status = 'Failed'
        error_message = f"An unexpected error occurred: {e}"
        logger.error(error_message)
        logger.debug(traceback.format_exc())
        log_run_end(
            run_id=run_id,
            status=run_status,
            error_message=error_message,
        )
        if callback:
            callback(success=False, message=error_message)

    finally:
        # If the run was interrupted or failed, ensure the run end is logged
        if run_id and run_status not in ['Completed', 'Failed', 'Interrupted']:
            run_status = 'Failed'
            error_message = 'Run ended unexpectedly.'
            log_run_end(
                run_id=run_id,
                status=run_status,
                error_message=error_message,
            )
            if callback:
                callback(success=False, message=error_message)


def run_selenium_automation_with_retries(
    data: pd.DataFrame,
    visible_mode: bool,
    control_email_sending: bool,
    prompt: str = None,
    reference_email: str = None,
    run_id: int = None,
    callback=None,
    batch_size: int = 50,  # How many rows per batch
    max_retries: int = 2,  # How many times to retry a failing batch
    email_subject: str = None,  # Optional: subject for emails
):
    logger.info(f"Run ID: {run_id} - Automation started (with retries).")
    run_status = 'Running'
    error_message = None

    try:
        total_rows = len(data)
        start_index = 0

        # Loop over data in batches
        while start_index < total_rows:
            end_index = min(start_index + batch_size, total_rows)
            batch_df = data.iloc[start_index:end_index]

            logger.info(
                f"Processing batch rows {start_index} to {end_index - 1}",
            )  # noqa: E501

            # Attempt to process this batch up to max_retries times
            attempts = 0
            batch_success = False
            while attempts < max_retries and not batch_success:
                attempts += 1
                try:
                    # This function does the actual row-by-row Selenium logic
                    process_chunk_of_rows(
                        batch_df=batch_df,
                        visible_mode=visible_mode,
                        control_email_sending=control_email_sending,
                        prompt=prompt,
                        reference_email=reference_email,
                        run_id=run_id,
                        email_subject=email_subject,
                    )
                    # If we get here, the batch was processed
                    # without raising a fatal error
                    batch_success = True

                except WebDriverException as wde:
                    logger.warning(f"WebDriverException on batch {start_index}-{end_index - 1}, attempt {attempts}/{max_retries}: {wde}")  # noqa: E501
                    logger.debug(traceback.format_exc())

                    # If it's the last attempt, decide whether to skip or abort
                    if attempts == max_retries:
                        logger.error(
                            f"Batch {start_index}-{end_index-1} failed after {max_retries} attempts. Skipping.",  # noqa: E501
                        )
                        # Optionally, you could `break`
                        # the entire loop or `return`
                        # if you want to stop the run entirely.

                except Exception as e:
                    logger.error(f"Unexpected exception on batch {start_index}-{end_index - 1}, attempt {attempts}/{max_retries}: {e}")  # noqa: E501
                    # Same logic: decide if you want
                    # to skip or break on final attempt.
                    if attempts == max_retries:
                        logger.error(f"Batch {start_index}-{end_index - 1} failed after {max_retries} attempts.")  # noqa: E501

            # Move on to the next batch, even if this batch ultimately failed
            start_index = end_index

        # If we reach here, we've attempted all batches
        run_status = 'Completed'
        logger.info(
            'All batches processed (with potential skips after max_retries).',
        )

        # Callback if needed
        if callback:
            callback(success=True, message='Run completed with retries.')

    except KeyboardInterrupt:
        run_status = 'Interrupted'
        error_message = 'Run was interrupted by the user (KeyboardInterrupt).'
        logger.warning(error_message)
        if callback:
            callback(success=False, message=error_message)

    except Exception as e:
        run_status = 'Failed'
        error_message = f"An unexpected error occurred: {e}"
        logger.error(error_message)
        logger.debug(traceback.format_exc())
        if callback:
            callback(success=False, message=error_message)

    finally:
        if run_id and run_status not in ['Completed', 'Failed', 'Interrupted']:
            run_status = 'Failed'
            error_message = 'Run ended unexpectedly.'
            if callback:
                callback(success=False, message=error_message)


def run_selenium_automation_old(
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
        logger.info(f"Chrome directory: {get_user_data_dir()}")

        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument(f"--user-data-dir={get_user_data_dir()}")

        # Initialize the WebDriver
        try:

            driver = uc.Chrome(
                options=options,
                driver_executable_path=r'C:\Users\RebeccaHannan\linkedin-automation\linkedin-recruiter\chromedriver.exe',
            )

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
                run_id=run_id,
                status=run_status,
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
                time.sleep(5)
                # Set up Selenium WebDriver options
                options = uc.ChromeOptions()

                if not visible_mode:
                    options.add_argument('--headless')
                logger.info(f"Chrome directory: {get_user_data_dir()}")
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--start-maximized')
                options.add_argument(f"--user-data-dir={get_user_data_dir()}")

                driver = uc.Chrome(
                    options=options,
                    driver_executable_path=r'C:\Users\RebeccaHannan\linkedin-automation\linkedin-recruiter\chromedriver.exe',
                )

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
                    logger.warning(f"Guessing email for row {index} due to missing email address.")  # noqa: E501
                    first_name = row['First Name'].lower()
                    last_name = row['Last Name'].lower()
                    company_slug = slugify_company(row['Company'])
                    profile_email_address = f"{first_name}.{last_name}@{company_slug}.com"  # noqa: E501
                    logger.info(f"Guessed {profile_email_address=}")

                # Force a hard reload
                driver.refresh()
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
                            profile_urn = data_json['data']['data'][
                                'identityDashProfilesByMemberIdentity'
                            ]['*elements'][
                                0
                            ]  # noqa:E501
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
                logger.debug(f"Navigate to https://www.linkedin.com/talent/profile/{profile_id}")  # noqa: E501
                driver.get(
                    f"https://www.linkedin.com/talent/profile/{profile_id}",
                )

                time.sleep(random.uniform(10, 20))

                # Wait for the contact info element to load
                contact_info = driver.find_element(
                    By.CLASS_NAME,
                    'contact-info',
                )

                # Check if an email already exists
                try:
                    existing_email = contact_info.find_element(
                        By.XPATH,
                        './/span[@data-test-contact-email-address]',
                    )
                    logger.debug(f"Email found: {existing_email.text}")
                except NoSuchElementException:
                    # If no email exists, look for the "Add email" button
                    logger.debug(
                        "No email found. Looking for 'Add email' button...",
                    )
                    add_email_button = driver.find_element(
                        By.XPATH,
                        ".//button[@class='button-small-muted-tertiary contact-info__add']",  # noqa:E501
                    )
                    logger.debug("Clicking on the 'Add email' button...")
                    add_email_button.click()
                    # Wait for the email input field to appear
                    email_input = driver.find_element(
                        By.XPATH,
                        ".//input[@type='email']",
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
                    By.XPATH,
                    "//button[contains(@class, 'artdeco-button') and contains(@data-live-test-component, 'message-icon-btn')]",  # noqa:E501
                )
                email_button.click()
                time.sleep(random.uniform(4, 7))

                # Locate the parent element
                send_info = driver.find_element(
                    By.XPATH,
                    "//div[contains(@class, 'single-message-composer__trigger-message')]",  # noqa:E501
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

                    modal = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located(
                            (
                                By.XPATH,
                                "//div[@role='dialog' and contains(@class, 'inline-modal__container')]",  # noqa: E501
                            ),
                        ),
                    )
                    logger.info('Modal is visible')
                    # Debug: log the modal's inner HTML
                    modal_html = modal.get_attribute('innerHTML')
                    logger.info('Modal HTML: %s', modal_html)
                    time.sleep(
                        2,
                    )  # Short pause, if needed, to ensure modal fully rendered
                    email_label = WebDriverWait(modal, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, ".//label[normalize-space(.)='Email']"),
                        ),
                    )

                    # Scroll the element into view
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        email_label,
                    )

                    # Pause a bit to ensure everything settles
                    # (you may adjust or remove this if unnecessary)
                    time.sleep(random.uniform(1, 2))

                    # Click the label
                    # using JavaScript click to avoid potential overlay issues
                    driver.execute_script('arguments[0].click();', email_label)
                    logger.info('Clicked on the email label')
                    # Optionally, wait a moment if needed
                    time.sleep(random.uniform(1, 2))

                    # Locate and click the Save button.
                    # Here we use a relative XPath to search within the modal.
                    save_button = WebDriverWait(modal, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                ".//button[.//span[contains(normalize-space(), 'Save')]]",  # noqa: E501
                            ),
                        ),
                    )
                    logger.info(
                        'Save button HTML: %s',
                        save_button.get_attribute(
                            'outerHTML',
                        ),
                    )
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        save_button,
                    )
                    time.sleep(random.uniform(1, 2))
                    driver.execute_script('arguments[0].click();', save_button)
                    logger.info('Clicked on the Save button.')

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
                            driver.refresh()
                            time.sleep(random.uniform(4, 7))

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
                    By.CSS_SELECTOR,
                    ".ql-editor[contenteditable='true']",
                )
                editor.click()

                # Type the email in chunks to mimic human typing
                chunk_size = 20
                for i in range(0, len(email), chunk_size):
                    editor.send_keys(email[i: i + chunk_size])

                # Control email sending if required
                if control_email_sending:
                    inject_key_listeners(driver)

                    try:
                        pressed_key = wait_for_key_signal(
                            driver,
                            timeout=300,
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
                                row_number=index,
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
                                row_number=index,
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
                            row_number=index,
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
                    row_number=index,
                )
                time.sleep(random.uniform(61, 82))
                # Force a hard reload
                driver.refresh()
                time.sleep(random.uniform(4, 7))

                logger.info('Page refreshed.')

            except Exception as e:
                email_status = 'Failed'
                error_message = str(e)
                logger.error(
                    f"Error processing profile {linkedin_profile}: {e}",
                )  # noqa:E501
                logger.debug(traceback.format_exc())
                # Log the error for this email
                log_email(
                    run_id=run_id,
                    linkedin_profile_url=linkedin_profile,
                    email_text=email if email else '',
                    email_status=email_status,
                    error_message=error_message,
                    row_number=index,
                )
                # Force a hard reload
                driver.refresh()
                time.sleep(random.uniform(4, 7))

                logger.info('Page refreshed.')
                continue

        # Update run status to Completed
        run_status = 'Completed'
        log_run_end(
            run_id=run_id,
            status=run_status,
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
            run_id=run_id,
            status=run_status,
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
            run_id=run_id,
            status=run_status,
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
                run_id=run_id,
                status=run_status,
                error_message=error_message,
            )
            if callback:
                callback(
                    success=False,
                    message=error_message,
                )
