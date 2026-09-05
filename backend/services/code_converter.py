import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")


client = genai.Client(api_key=api_key)


def convert_code(source_language, target_language, code):

    prompt = f"""
You are an expert programming language code converter.

Convert the given {source_language} code into {target_language}.

Rules:

1. Preserve the original functionality.
2. Use correct {target_language} syntax.
3. Follow best practices of {target_language}.
4. Return ONLY the converted code.
5. Do NOT provide explanations.
6. Do NOT use Markdown code blocks.
7. Do not add extra text.

Source Language: {source_language}

Target Language: {target_language}

Source Code:

{code}
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    return interaction.output_text