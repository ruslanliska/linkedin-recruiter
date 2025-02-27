from src.agents.email_writer import DEFAULT_EMAIL_INSTRUCTION
from src.agents.email_writer import DEFAULT_USER_PROMPT
from src.agents.email_writer import generate_email
from src.agents.linkedin_info import generate_page_summary


def generate_personal_email(
    page_summary: str,
    user_prompt: str = DEFAULT_USER_PROMPT,
    email_instructions: str = DEFAULT_EMAIL_INSTRUCTION,
) -> str:
    if not user_prompt:
        user_prompt = DEFAULT_USER_PROMPT

    if not email_instructions:
        email_instructions = DEFAULT_EMAIL_INSTRUCTION

    page_summary = generate_page_summary(page_content=page_summary)
    email = generate_email(
        page_summary=page_summary,
        user_prompt=user_prompt,
        email_instructions=email_instructions,
    )

    return email
