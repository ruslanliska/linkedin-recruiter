import asyncio

from browser_use import Agent
from browser_use import Browser
from browser_use import BrowserConfig
from browser_use import Controller
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pydantic import Field

load_dotenv()

# Configure the browser to connect to your Chrome instance
browser = Browser(
    config=BrowserConfig(
        # Specify the path to your Chrome executable
        # browser_binary_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        browser_binary_path=r'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',  # windows path
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'
    ),
)


initial_action_agent_1 = [
    {
        'open_tab': {
            'url': 'http://linkedin.com/talent/hire/1645278338/discover/recruiterSearch?savedSearch=urn%3Ali%3Ats_cap_saved_search%3A1907552162&savedSearchAction=GET&searchContextId=f3acd4d4-469e-4e0a-bf40-76e774eda1fc&searchHistoryId=20619306290&searchRequestId=cce9405e-aab0-4d53-b6cb-97cb19e3b094&start=0&uiOrigin=SAVED_SEARCH',
        },
    },
    {'wait': {'seconds': 300}},
]
initial_action_agent_2 = [
    {'wait': {'seconds': 30}},
]

# Define the output format as a Pydantic model


class ProfilesCount(BaseModel):
    number_of_profiles: int = Field(description='Number of profiles found')


class ProfileOpened(BaseModel):
    if_correct_profile_opened: bool = Field(
        description='If correct profile opened, return True, else False',
    )


class TaskCompleted(BaseModel):
    is_task_completed: bool = Field(
        description='If task completed, return True, else False',
    )


controller = Controller()
controller_agent_1 = Controller(output_model=ProfilesCount)
controller_agent_2 = Controller(output_model=ProfileOpened)
controller_agent_3 = Controller(output_model=TaskCompleted)
controller_agent_4 = Controller(output_model=TaskCompleted)
controller_agent_5 = Controller(output_model=TaskCompleted)


@controller_agent_5.registry.action('Generate email body with profile experience')
async def generate_email_body(profile_experience: str):
    from src.agents.email_writer import generate_email

    email = generate_email(page_summary=profile_experience)
    print(f"{email=}")
    return email


@controller_agent_3.registry.action('Guess email if no email provided in contact info')
async def guess_email(first_name: str, last_name: str, current_company_name: str):
    import re

    slug = (
        re.sub(
            r'[^\w\s-]',
            '',
            current_company_name,
        )
        .lower()
        .replace(' ', '-')
    )
    return f"{first_name.lower().strip()}.{last_name.lower().strip()}@{slug.strip()}.com"  # noqa: E501


extend_system_message = """
You are recruiter. You must control all steps in task executed properly and in correct order
"""


async def main():
    async with await browser.new_context() as context:
        model = ChatOpenAI(model='gpt-4o')

        # Initialize browser agent
        agent1 = Agent(
            task='''You have search result opened, you must get number of results and click on first name to open profile, and return only number of results
            If no search, then return 0''',
            llm=model,
            browser_context=context,
            initial_actions=initial_action_agent_1,
            controller=controller_agent_1,
        )
        profiles_count = await agent1.run()
        result = profiles_count.final_result()
        if result:
            parsed: ProfilesCount = ProfilesCount.model_validate_json(result)
            print(f"{parsed.number_of_profiles=}")
            profiles = parsed.number_of_profiles
            for i in range(1, profiles):
                try:
                    agent2 = Agent(
                        task=f"""You are processing profile number {i}! You must see text {i} of {profiles},
                        confirm it is true, if not, navigate to that profile by clicking arrows right or left, if you click and current number doesnt change, refresh page and try again.""",
                        llm=model,
                        browser_context=context,
                        controller=controller_agent_2,
                        max_failures=3,
                    )

                    profile_opened = await agent2.run()
                    result_opened = profile_opened.final_result()
                    result_opened: ProfileOpened = ProfileOpened.model_validate_json(
                        result_opened,
                    )
                    print(f"{result_opened.if_correct_profile_opened=}")
                    if not result_opened.if_correct_profile_opened:
                        continue
                    agent3 = Agent(
                        task=f"""The task is to enter email for user if email is not provided in contact information and save email. If email provided, just mark the task as completed.
                        Use guess_email
                        Task is complete when email saved in contact info and present there.
                        """,
                        llm=model,
                        browser_context=context,
                        controller=controller_agent_3,
                    )
                    result_agent_3 = await agent3.run()
                    result_agent_3 = result_agent_3.final_result()
                    result_agent_3: TaskCompleted = TaskCompleted.model_validate_json(
                        result_agent_3,
                    )
                    print(f"{result_agent_3.is_task_completed=}")
                    if not result_agent_3.is_task_completed:
                        continue

                    print('Email input completed')
                    agent4 = Agent(
                        task=f"""The task is to click on Send message to candidate, wait for 5 seconds and in new window (Compose Message) which appears, find text Send immediately via InMail,
                        and click arrow down and Select option for 'Send as' - Email (Click button with text Email, then save changes, by clicking buttorn with text Save in the same container) you must confirm that Email is used as option, then click Save, to save this option,
                        After this the text 'Send immediately via Email' must appear, if 'Send immediately via InMail' present, then task is completed. Ifg you encounter error with saving - Refresh the page and start again
                        NOTE! The Save button is not visible sometimes, try to look for button with Text 'Save' in the same component when you change Send as
                        """,
                        llm=model,
                        browser_context=context,
                        max_failures=3,
                        controller=controller_agent_4,
                    )
                    result_agent_4 = await agent4.run()
                    result_agent_4 = result_agent_4.final_result()
                    result_agent_4: TaskCompleted = TaskCompleted.model_validate_json(
                        result_agent_4,
                    )
                    print(f"{result_agent_4.is_task_completed=}")
                    if not result_agent_4.is_task_completed:
                        continue
                    print('Email option Done')
                    agent5 = Agent(
                        task=f"""The task is to input subject and Email to input fields
                        You must input real values, make this message ready to go
                        First generate email body, use generate_email_body, for input get User job experience (Find component with header 'Experience'). (Enter the result to field with placeholder - Compose a message) and wait for 40 seconds
                        Generate subject based on email body and input it (Enter to field with placeholder - Add a subject)
                        When all fields filled. Click on Send button (Ignore errors if any)
                        Refresh page
                        """,
                        llm=model,
                        browser_context=context,
                        controller=controller_agent_5,
                        max_failures=1,
                    )
                    result_agent_5 = await agent5.run()
                    result_agent_5 = result_agent_5.final_result()
                    result_agent_5: TaskCompleted = TaskCompleted.model_validate_json(
                        result_agent_5,
                    )
                    print(f"{result_agent_5.is_task_completed=}")
                    if not result_agent_5.is_task_completed:
                        continue
                    print('Subject and email option Done')

                    print('Run completed')

                except Exception as e:
                    print(e)
                    continue

        else:
            print('No result')

    # Create the agent with your configured browser
    # agent = Agent(
    #     task=f"""
    #     You have search result, there is some amount of pages, yur task to write a message to each person on the page, then go to the next page and write all people from search
    #     Follow next steps in strong order.

    #     Step 1:
    #     For each profile, open it in by clicking on name

    #     Step 2:
    #     input email (Use guess_email if no user email provided in contact info) and create message

    #     Step 3:
    #     Click on send message and wait 4 seconds

    #     Step 4:
    #     THIS IS REQUIRED, IF THIS STEP IS NOT COMPLETED, OTHER STEPS CANT BE DONE.
    #     Find text Initial message
    #     Send immediately via InMail in message container

    #     Switch from InMail to Email BY CLICKING ON send Immediately via InMail
    #     change to Send as EMAIL
    #     Click Save button to save setup for Email, and go to next step!

    #     Step 5:
    #     Generate a subject.

    #     Step 6:
    #     Use generate_email_body to create email to send.
    #     For profile_experience get the profile experience
    #     Use only this action to generate email body!
    #     Fill in message field with outpur from generate_email_body.
    #     Input it to index 40

    #     Step 7:
    #     Validation of all steps
    #     Check if Initial message is Send via Email
    #     Check if subject present and valid
    #     Check if email body valid. If not, fix it and continue
    #     WRITE MESSAGE, BUT DONT SEND IT
    #     Reload page
    #     wait for 10 seconds

    #     Step 8:
    #     and go to next profile (Click index 1), If you can click it, reload page and then click
    #     Retry from step 1.
    #     """,
    #     llm=ChatOpenAI(
    #         model='gpt-4o',
    #         temperature=0,
    #     ),
    #     browser=browser,
    #     memory_interval=10,
    #     initial_actions=initial_actions,
    #     controller=controller,
    #     extend_system_message=extend_system_message,
    # )
    # await agent.run()

    # input('Press Enter to close the browser...')
    # await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
