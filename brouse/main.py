import asyncio

from browser_use import Agent
from browser_use import Browser
from browser_use import BrowserConfig
from browser_use import Controller
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# Configure the browser to connect to your Chrome instance
browser = Browser(
    config=BrowserConfig(
        # Specify the path to your Chrome executable
        # browser_binary_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        browser_binary_path=r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # windows path
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'
    ),
)


initial_actions = [
    {
        "open_tab": {
            "url": "http://linkedin.com/talent/hire/1645278338/discover/recruiterSearch?savedSearch=urn%3Ali%3Ats_cap_saved_search%3A1907552162&savedSearchAction=GET&searchContextId=f3acd4d4-469e-4e0a-bf40-76e774eda1fc&searchHistoryId=20619306290&searchRequestId=cce9405e-aab0-4d53-b6cb-97cb19e3b094&start=0&uiOrigin=SAVED_SEARCH"
        }
    },
    {"wait": {"seconds": 30}},
]

controller = Controller()


@controller.registry.action("Generate email body with profile experience")
async def generate_email_body(profile_experience: str):
    from src.agents.email_writer import generate_email

    email = generate_email(page_summary=profile_experience)
    print(f"{email=}")
    return email


@controller.registry.action("Guess email if no email provided in contact info")
async def guess_email(first_name: str, last_name: str, current_company_name: str):
    import re

    slug = (
        re.sub(
            r"[^\w\s-]",
            "",
            current_company_name,
        )
        .lower()
        .replace(" ", "-")
    )
    return (
        f"{first_name.lower().strip()}.{last_name.lower().strip()}@{slug.strip()}.com"
    )


async def main():
    # Create the agent with your configured browser
    agent = Agent(
        task=f"""
        You have search result, there is some amount of pages, yur task to write a message to each person on the page, then go to the next page and write all people from search
        Follow next steps in strong order.
        
        Step 1:
        For each profile, open it in by clicking on name
        
        Step 2:
        input email (Use guess_email if no user email provided in contact info) and create message

        Step 3:
        Click on send message and wait 4 seconds

        Step 4:
        Find text Initial message
        Send immediately via InMail in message container

        Switch from InMail to Email BY CLICKING ON send Immediately via InMail
        if you see send Immediately via InMail - click on it and change to Send as EMAIL (Index 31)
        Click Save button to save setup for Email, and go to next step!
        THIS IS REQUIRED, IF THIS STEP IS NOT COMPLETED, OTHER STEPS CANT BE DONE.

        Step 5:
        Generate a subject.

        Step 6:
        Use generate_email_body to create email to send. 
        For profile_experience get the profile experience 
        Use only this action to generate email body!
        Fill in message field with outpur from generate_email_body.
        Input it to index 40

        Step 7:
        Validation of all steps
        Check if Initial message is Send via Email
        Check if subject present and valid
        Check if email body valid. If not, fix it and continue
        WRITE MESSAGE, BUT DONT SEND IT
        Reload page
        wait for 10 seconds

        Step 8:
        and go to next profile (Click index 1), If you can click it, reload page and then click
        Retry from step 1.
        """,
        llm=ChatOpenAI(
            model="gpt-4o",
        ),
        browser=browser,
        memory_interval=10,
        initial_actions=initial_actions,
        controller=controller,
    )
    await agent.run()

    input("Press Enter to close the browser...")
    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
