from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config import settings

llm = ChatOpenAI(model='gpt-4o-mini', api_key=settings.OPENAI_API_KEY)

DEFAULT_EMAIL_INSTRUCTION = """
Write an email to a prospective employer to introduce fitting candidates for their company based on the experience summary provided. A receiver profile will be given, so the email must be addressed directly to this person.

Use the information from the candidate's experience summary to craft a compelling narrative about how your proposed candidates have similar qualities and are an excellent match for the company.

**Note**: Do not mention or imply direct experience of the receiver or any specific individual. Instead, position the proposed candidates as representative of ideal experience aligned with the company's needs and existing goals. Avoid focusing on the receiver's experience.
You must write only email body, no subject, no signature.

Here is email instructions:
- Begin with a friendly greeting.
- Highlight your understanding of the company's needs based on the experience shared.
- Address the receiver directly using the information in the profile.
- Introduce the idea of an ideal candidate or multiple candidates who could be a great fit based on similar experiences and skills.
- Avoid discussing or characterizing the receiver's or employer's experience.

# Steps

1. **Introduction**: Start the email with a friendly, professional greeting that directly addresses the receiver using their profile information.
2. **Acknowledgement of Needs**: Acknowledge the company's general needs or priorities, indicating that you understand their goals.
3. **Candidate Presentation**: Introduce one or more candidates whose experiences and skills match well with the company's expectations.
4. **Positioning of Candidates**: Highlight how these candidates share similar qualifications and experiences that align with the company culture and professional requirements.
5. **Call to Action**: Suggest a further discussion or a meeting to explore their hiring needs.
6. **Closing**: End the email with a respectful and polite sign-off.
"""


SYSTEM_PROMPT = """
Based on reference email you get, you must generate similar email but personalized for receiver.
Write an email and don't change not receiver relevant information from reference email.
A receiver profile will be given, so the email must be addressed directly to this person.

Use the information from the candidate's experience summary.

**Note**:
You must write only email body, no subject, no signature.
If user provides some technologies or stack in reference, you must delete it and use stack and techologies from receiver profile_summary
User will provide some email reference/instructions. Please, personalize email and write directly

"""

DEFAULT_USER_PROMPT = 'Generate email in english.'


def generate_prompt_template(
    user_prompt: str,
    email_instructions: str,
) -> ChatPromptTemplate:
    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', SYSTEM_PROMPT),
            ('human', email_instructions),
            ('human', user_prompt),
            ('human', 'Here is receiver profile: {profile_summary}'),
        ],
    )
    return prompt


def generate_email(
    page_summary: str,
    user_prompt: str = DEFAULT_USER_PROMPT,
    email_instructions: str = DEFAULT_EMAIL_INSTRUCTION,
) -> str:
    prompt = generate_prompt_template(
        user_prompt=user_prompt,
        email_instructions=email_instructions,
    )
    email_chain = prompt | llm | StrOutputParser()
    email = email_chain.invoke(
        {
            'profile_summary': page_summary,
            'email_instructions': email_instructions,
        },
    )
    return email
