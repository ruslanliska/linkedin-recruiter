from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config import settings

llm = ChatOpenAI(model='gpt-4o-mini', api_key=settings.OPENAI_API_KEY)


SYSTEM_PROMPT = """
Generate a relevant and engaging subject line for the provided email content.

- The subject should be concise, attention-grabbing, and reflect the main point or purpose of the email.
- Tailor the subject to fit the tone, context, and intended audience of the email.
- Avoid using overly generic or vague language.

# Steps
1. Carefully read the provided email content.
2. Identify the primary message or intent (e.g., promotional offer, important update, event invitation).
3. Create a subject line succinctly summarizing or emphasizing this key message.
4. Ensure the subject is under 10 words to maintain focus and maximize readability.

# Output Format
- A single subject line, ideally less than 5 words, suitable for use in email communication.

"""

DEFAULT_USER_PROMPT = 'Generate email in english.'


def generate_prompt_template(
) -> ChatPromptTemplate:
    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', SYSTEM_PROMPT),
            (
                'human',
                'Here is email you need to generate subject for: {email_body}',
            ),
        ],
    )
    return prompt


def generate_subject(
    email_body: str,
) -> str:
    print('Writing subject')
    prompt = generate_prompt_template()
    subject_chain = prompt | llm | StrOutputParser()
    subject = subject_chain.invoke(
        {
            'email_body': email_body,
        },
    )
    return subject
