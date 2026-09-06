"""Manual Gemini smoke test.

Run this file directly when a valid GEMINI_API_KEY is configured. Keeping the
API call behind the main guard prevents pytest collection from making a live
request.
"""

import os

from dotenv import load_dotenv
from google import genai


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    prompt = """
You are an expert programming code converter.

Convert the following Python code into JavaScript.

Rules:
1. Preserve the same functionality.
2. Use correct JavaScript syntax.
3. Return only the converted code.
4. Do not add explanations.
5. Do not use Markdown code blocks.

Python Code:
print("Hello World")
"""
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )
    print(interaction.output_text)