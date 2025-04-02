import json
import logging
import random
import socket
import time
import traceback

import pandas as pd
import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
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
from src.inmail.utils import parse_results_count
from src.inmail.utils import slugify_company
from src.inmail.utils import wait_for_key_signal

socket.setdefaulttimeout(60)  # Set global timeout to 60 seconds


# Configure logger
logger = logging.getLogger(__name__)


socket.setdefaulttimeout(60)  # Set global timeout to 60 seconds
logger = logging.getLogger(__name__)


def process_profile(driver): ...


def process_chunk_of_rows(
    visible_mode,
    control_email_sending,
    prompt,
    run_id,
    job_titles: list[str] = None,
    locations: list[str] = None,
    skills_assessments: list[str] = None,
    companies: list[str] = None,
    schools: list[str] = None,
    industries: list[str] = None,
    keywords: list[str] = None,
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
        # driver = uc.Chrome(options=options)  # auto-detect
        driver = uc.Chrome(
            options=options,
            driver_executable_path=r'C:\Users\Robin\linkedin_email_application\linkedin-recruiter\chromedriver.exe',
        )
        logger.info('Driver installed')

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
        print(f"{job_titles=}")
        print(f"{locations=}")
        print(f"{skills_assessments=}")
        print(f"{companies=}")
        print(f"{schools=}")
        print(f"{industries=}")
        print(f"{keywords=}")
        logger.info('ChromeDriver initialized successfully for this batch.')
        driver.get('https://www.linkedin.com/talent/search')

        logger.info('Search opened')
        time.sleep(random.uniform(2, 5))

        logger.info('Starting search')
        if job_titles:
            # Wait for the button to be clickable, then click it.
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button.facet-edit-button[data-view-name='search-facet-add'][aria-label='Add Job titles or boolean']",
                    ),
                ),
            ).click()
            logger.info('Job title clicked')
            for title in job_titles:
                # Wait for the input to become visible, then send keys
                wait = WebDriverWait(driver, 5)
                input_field = wait.until(
                    EC.visibility_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "input.artdeco-typeahead__input.ts-common-typeahead__input[placeholder*='job title']",
                        ),
                    ),
                )
                input_field.clear()  # optional, if you want to clear existing text
                input_field.send_keys(title)
                input_field.send_keys(Keys.ENTER)
                time.sleep(random.uniform(1, 3))
            input_field.send_keys(Keys.ESCAPE)

        if locations:
            # Wait for the button to be clickable, then click it.
            wait = WebDriverWait(driver, 5)
            locator = (
                By.CSS_SELECTOR,
                "button.facet-edit-button[data-view-name='search-facet-add'][aria-label='Add a Candidate geographic location']",
            )

            location_button = wait.until(EC.element_to_be_clickable(locator))
            location_button.click()
            logger.info('Location clicked')
            for location in locations:
                # Wait for the input to be visible
                wait = WebDriverWait(driver, 2)
                input_locator = (
                    By.CSS_SELECTOR,
                    "input.artdeco-typeahead__input.ts-common-typeahead__input[placeholder='enter a location…']",
                )

                location_field = wait.until(
                    EC.visibility_of_element_located(input_locator),
                )

                # Type your location
                location_field.send_keys(location)

                # Optionally wait a moment for suggestions to appear
                time.sleep(random.uniform(1, 3))

                # Press arrow down
                location_field.send_keys(Keys.ARROW_DOWN)

                # Wait again if needed
                time.sleep(random.uniform(1, 2))

                # Press Enter
                location_field.send_keys(Keys.ENTER)
            location_field.send_keys(Keys.ESCAPE)

        try:
            # Wait for the results element to be present (up to 15 seconds)
            results_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'span[data-live-test-profile-list-num-custom]',
                    ),
                ),
            )
            results_text = results_element.text.strip()
            num_results = parse_results_count(results_text)
            logger.info(f"Number of results: {num_results}")
        except TimeoutException:
            logger.error(
                'Results element not found within the timeout period.',
            )
        page = 1

        for page in range(1, num_results):
            logger.info(f"Processing page {page} of results")
            time.sleep(random.uniform(3, 5))
            current_link = driver.current_url
            print('Current URL:', current_link)
            try:
                # Wait until the profile list container is present using the updated class selector
                container = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//div[contains(@class, 'profile-list-container-card')]",
                        ),
                    ),
                )
                # Optionally wait until it's visible
                container = WebDriverWait(driver, 15).until(
                    EC.visibility_of(container),
                )
            except TimeoutException:
                print('Profile list container not found within the timeout period.')
            else:

                time.sleep(random.uniform(3, 5))

                profile_items = container.find_elements(
                    By.XPATH,
                    ".//li[.//a[@data-test-link-to-profile-link='true']]",
                )
                # for profile in profile_items:
                for profile_index in range(25):
                    driver.get(current_link)
                    time.sleep(random.uniform(6, 10))
                    print('Opened search result')
                    print(f"{profile_index=}")
                    # Locate child profile items; adjust the XPath if needed for your actual HTML structure.
                    # Set the increment and pause duration.
                    increment = 30  # pixels per scroll
                    pause = 0.01  # seconds between scrolls

                    # Get the initial scroll height
                    last_height = driver.execute_script(
                        'return document.body.scrollHeight',
                    )

                    while True:
                        # Scroll down by the increment
                        driver.execute_script(
                            'window.scrollBy(0, arguments[0]);',
                            increment,
                        )
                        time.sleep(pause)

                        # Optionally, check if new content loaded by comparing heights.
                        new_height = driver.execute_script(
                            'return document.body.scrollHeight',
                        )
                        if new_height != last_height:
                            last_height = new_height

                        # Break condition: for example, if you reached near the bottom.
                        # Here, we stop if we've scrolled within 100 pixels of the bottom.
                        current_scroll = driver.execute_script(
                            'return window.pageYOffset;',
                        )
                        if (
                            current_scroll
                            + driver.execute_script('return window.innerHeight;')
                            >= last_height - 100
                        ):
                            break

                    print('Finished scrolling.')
                    time.sleep(random.uniform(2, 6))

                    profile_items = container.find_elements(
                        By.XPATH,
                        ".//li[.//a[@data-test-link-to-profile-link='true']]",
                    )
                    print(f"{len(profile_items)=}")

                    profile = profile_items[profile_index]
                    print(f"{profile.text=}")
                    # Process each profile item (for example, print its text)
                    try:
                        # Hover over the profile item so that any hidden buttons become visible
                        ActionChains(driver).move_to_element(profile).perform()
                        time.sleep(1)  # Allow UI to update

                        # Attempt to locate the Message button within this profile.
                        try:
                            message_button = profile.find_element(
                                By.XPATH,
                                ".//button[contains(., 'Message')]",
                            )
                        except Exception as inner_ex:
                            print(
                                'Message button not found in profile:',
                                profile.text,
                            )
                        #     # continue  # Skip this profile if button not found

                        # # Wait until the button is clickable (if necessary)
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(message_button),
                        )

                        # Try a normal click; if that fails, use JavaScript to click
                        try:
                            message_button.click()
                        except Exception as click_ex:
                            driver.execute_script(
                                'arguments[0].click();',
                                message_button,
                            )
                        print('Message clicked')
                        print(f"{profile.text=}")
                        print(f"{profile_index=}")
                        time.sleep(5)
                        # Locate the element using a CSS selector
                        recipient_profile_elem = driver.find_element(
                            By.CSS_SELECTOR,
                            'div.recipient-profile',
                        )
                        # Within that container, locate and click the "Public profile" button
                        public_profile_button = recipient_profile_elem.find_element(
                            By.CSS_SELECTOR,
                            'button.topcard-condensed__bing-button',
                        )
                        public_profile_button.click()

                        # Now wait for the hovercard anchor to appear.
                        # We can target it by its stable attribute: data-test-public-profile-link
                        profile_link_elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR,
                                 'a[data-test-public-profile-link]'),
                            ),
                        )

                        # Extract the href
                        profile_href = profile_link_elem.get_attribute('href')
                        print('Profile URL:', profile_href)
                        name_elem = recipient_profile_elem.find_element(
                            By.CSS_SELECTOR,
                            'div.artdeco-entity-lockup__title',
                        )
                        name = name_elem.text.strip()
                        print('Name:', name)

                        # Extract the company name from the container
                        company_elem = recipient_profile_elem.find_element(
                            By.CSS_SELECTOR,
                            'a.position-item__company-link',
                        )
                        company_name = company_elem.text.strip()
                        print('Company Name:', company_name)

                        # Extract its text (Selenium automatically returns visible text)
                        all_text = recipient_profile_elem.text
                        print('Extracted text:')
                        print(all_text)
                        print('To profile')
                        driver.get(profile_href)
                        print('profile opened')

                        # Wait until the cancel button (ancestor of the li-icon) is clickable
                        # dismiss_button = WebDriverWait(driver, 10).until(
                        #     EC.element_to_be_clickable(
                        #         (By.XPATH, "//button[@aria-label='Dismiss']"),
                        #     ),
                        # )
                        # dismiss_button.click()
                        # print('dismiss_button clicked')
                        print('To continue next profile')
                        time.sleep(10)

                        continue
                    except Exception as e:
                        print('Error processing profile:', e)
                        continue

                # Wait for the Next button to be clickable (adjust timeout if needed)
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            'a.pagination__quick-link--next[data-test-pagination-next]',
                        ),
                    ),
                )

                # Click the Next button
                next_button.click()
                time.sleep(random.uniform(6, 10))
                logger.info('Next page')
                continue

            # finally:
            #     time.sleep(600)

        time.sleep(600)

        return
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in batch processing: {error_message}")
        traceback.print_exc()
        raise e
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


def run_selenium_automation_with_retries(
    visible_mode: bool,
    control_email_sending: bool,
    prompt: str = None,
    run_id: int = None,
    callback=None,
    job_titles: list[str] = None,
    locations: list[str] = None,
    skills_assessments: list[str] = None,
    companies: list[str] = None,
    schools: list[str] = None,
    industries: list[str] = None,
    keywords: list[str] = None,
):
    logger.info(f"Run ID: {run_id} - Automation started (with retries).")
    run_status = 'Running'
    error_message = None
    print(f"{job_titles=}")
    print(f"{locations=}")
    print(f"{skills_assessments=}")
    print(f"{companies=}")
    print(f"{schools=}")
    print(f"{industries=}")
    print(f"{keywords=}")
    try:
        # This function does the actual row-by-row Selenium logic
        process_chunk_of_rows(
            visible_mode=visible_mode,
            control_email_sending=control_email_sending,
            prompt=prompt,
            run_id=run_id,
            job_titles=job_titles,
            locations=locations,
            skills_assessments=skills_assessments,
            companies=companies,
            schools=schools,
            industries=industries,
            keywords=keywords,
        )
        # If we get here, the batch was processed
        # without raising a fatal error
        batch_success = True

    except WebDriverException as wde:
        logger.debug(traceback.format_exc())

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
