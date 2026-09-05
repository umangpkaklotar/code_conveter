import os
from dotenv import load_dotenv
from google import genai


# Load .env file
load_dotenv()


# Get API key from .env
api_key = os.getenv("GEMINI_API_KEY")


# Create Gemini client
client = genai.Client(api_key=api_key)


# Prompt for code conversion
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


# Send request to Gemini
interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input=prompt
)


# Print converted code
print(interaction.output_text)