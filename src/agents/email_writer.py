from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config import settings

llm = ChatOpenAI(model='gpt-4o-mini', api_key=settings.OPENAI_API_KEY)


SYSTEM_PROMPT = """Write an email to a prospective employer to introduce fitting candidates for their company based on the experience summary provided. A receiver profile will be given, so the email must be addressed directly to this person.

Use the information from the candidate's experience summary to craft a compelling narrative about how your proposed candidates have similar qualities and are an excellent match for the company.

**Note**: Do not mention or imply direct experience of the receiver or any specific individual. Instead, position the proposed candidates as representative of ideal experience aligned with the company's needs and existing goals. Avoid focusing on the receiver's experience.

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

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ('system', SYSTEM_PROMPT),
        ('human', 'Here is receiver profile: {profile_summary}'),
    ],
)


def generate_email(page_summary: str) -> str:
    email_chain = PROMPT_TEMPLATE | llm | StrOutputParser()
    email = email_chain.invoke(
        {
            'profile_summary': page_summary,
        },
    )
    return email