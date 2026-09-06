import os
import json

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
4. Return one valid JSON object with exactly two keys: converted_code and explanation.
5. converted_code must contain only the converted code, with no Markdown fences.
6. explanation must be a complete, beginner-friendly explanation covering the overall approach, important line or block changes, syntax differences, and how the converted code works.
7. Do not add text outside the JSON object.

Source Language: {source_language}

Target Language: {target_language}

Source Code:

{code}
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    raw_output = interaction.output_text.strip()
    try:
        result = json.loads(raw_output)
        return {
            "converted_code": str(result.get("converted_code", "")),
            "explanation": str(result.get("explanation", "")),
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "converted_code": raw_output,
            "explanation": (
                f"The code was converted from {source_language} to {target_language}. "
                "Review the translated syntax and runtime-specific behavior before using it in production."
            ),
        }


def generate_code(prompt):
    generation_prompt = f"""
You are an expert software developer generating production-quality code.

Analyze the user's request and identify the programming language that best matches
it. If the user explicitly names a language, use that language. Otherwise choose
the most appropriate language based on the requested framework, runtime, or task.
Then create a complete, runnable solution in that language.

Rules:

1. Return one valid JSON object with exactly three keys: detected_language, converted_code, and explanation.
2. detected_language must contain only the language name, such as Python or JavaScript.
3. converted_code must contain only the code, with no Markdown fences.
4. explanation must be concise and structured as plain text with these exact sections:
   Summary:
   Key decisions:
   How to run:
   Each section must contain short bullet points beginning with '-'. Do not write a long paragraph.
5. Make reasonable assumptions when the request is incomplete and state them under Key decisions.
6. Include helpful comments in the code only where they improve clarity.
7. Do not add text outside the JSON object.

User Request:

{prompt}
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=generation_prompt
    )

    raw_output = interaction.output_text.strip()
    try:
        result = json.loads(raw_output)
        return {
            "detected_language": str(result.get("detected_language", "Unknown")),
            "converted_code": str(result.get("converted_code", "")),
            "explanation": str(result.get("explanation", "")),
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "detected_language": "Unknown",
            "converted_code": raw_output,
            "explanation": (
                "Summary:\n"
                "- Code was generated from your request.\n\n"
                "Key decisions:\n"
                "- The language was inferred from your prompt.\n\n"
                "How to run:\n"
                "- Review the generated code and follow the setup steps included in it."
            ),
        }