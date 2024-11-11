import logging
import random
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(level=logging.INFO)


def run_template_email(
    linkedin_email,
    linkedin_password,
    data,
    visible_mode,
    email_template,
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
            print('DRINMVE')
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

        # driver.get('https://www.linkedin.com/login')
        # time.sleep(random.uniform(2, 5))
        # driver.find_element(By.ID, 'username').send_keys(
        #     linkedin_email.strip(),
        # )

        # time.sleep(random.uniform(2, 5))
        # driver.find_element(By.ID, 'password').send_keys(
        #     linkedin_password.strip(),
        # )
        # driver.find_element(By.XPATH, '//button[@type="submit"]').click()

        # Process each item in the data
        # for index, row in data.iterrows():
        #     linkedin_url = row['Person Linkedin Url']
        #     email = row['Email']
        #     # Perform automation steps
        #     driver.get(linkedin_url)
        #     time.sleep(2)  # Wait for the page to load
        # Inject JavaScript to set a flag on Ctrl+Enter
        # driver.execute_script("""
        #     document.addEventListener('keydown', function(event) {
        #         if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        #             localStorage.setItem('continueFlag', 'true');
        #         }
        #     });
        # """)

        # Poll every second to check if the user has pressed Ctrl+Enter
        # while True:
        #     print('polling')
        #     try:
        #         # Check if the flag is set in localStorage
        #         if driver.execute_script("return localStorage.getItem('continueFlag');") == 'true':
        #             print('Ctrl+Enter detected! Continuing with the script...')
        #             break
        #     except Exception as e:
        #         print('Error checking flag:', e)

        #     # Wait a bit before checking again
        #     time.sleep(1)

        # Clear the flag in case this part of the script runs again
        driver.execute_script("localStorage.removeItem('continueFlag');")
        linkedin_profile = 'https://www.linkedin.com/in/ruslan-liska/'
        driver.get(linkedin_profile)
        # Get the full page HTML
        from bs4 import BeautifulSoup

        full_html = driver.page_source
        print('Full HTML Content:')
        print(full_html)  # This prints the full HTML of the page

        # Optional: Parse the HTML with BeautifulSoup to extract only the visible text
        soup = BeautifulSoup(full_html, 'html.parser')
        # Separates lines with newline for readability
        page_text = soup.get_text(separator='\n')
        cleaned_text = '\n'.join(
            line.strip()
            for line in page_text.splitlines() if line.strip()
        )
        print('\nCleaned Visible Page Text:')
        # print(cleaned_text)
        print('FINISH TEMPLARWE')
        time.sleep(10)

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
