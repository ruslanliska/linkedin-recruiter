from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config import settings

llm = ChatOpenAI(model='gpt-4o-mini', api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """
Transform the given LinkedIn page content into a concise professional description, focusing primarily on the technologies used. Ensure the specific technical details are highlighted while removing any unnecessary or irrelevant information. Do not include previous company names.

# Sections to Include

- **Name**: Include the individual's full name.
- **Current company**: Name of the current company.
- **Headline**: Provide a concise, impactful headline that captures the main technical expertise or role.
- **About**: Summarize the individual’s professional background, focusing on technical skills, key technologies, and relevant achievements.
- **Technical Stack**: List the main technologies used, including languages, frameworks, or tools. Focus on highlighting expertise level if possible.
- **Skills Endorsement**: Highlight key technical skills that have notable endorsements or recognitions, indicating expertise areas.

# Steps

1. **Extract key technical details**: Identify and focus on the main technical skills, technologies, experience, and qualifications.
2. **Remove non-essential information**: Omit redundant or irrelevant content (e.g., soft skills, personal interests, phrases like "passionate about", etc.) unless critical to understanding technical ability.
3. **Condense content**: Reformat the description to ensure it is short, precise, and impactful, while retaining all important technical competencies and achievements.

# Output Format

Provide a structured summary in the following format:
- **Name**: [Full Name]
- **Headline**: [One-sentence headline summarizing expertise]
- **About**: [Brief paragraph focusing on technical expertise and significant achievements]
- **Technical Stack**: [List of relevant technologies, languages, and tools]
- **Skills Endorsement**: [Key endorsed skills with notable recognitions, if available]

Ensure that the summary emphasizes the most relevant technologies and technical competencies throughout the content.

"""
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ('system', SYSTEM_PROMPT),
        ('human', '{page_content}'),
    ],
)


def generate_page_summary(page_content: str) -> str:
    page_summary_chain = PROMPT_TEMPLATE | llm | StrOutputParser()
    page_summary = page_summary_chain.invoke(
        {
            'page_content': page_content,
        },
    )
    return page_summary
