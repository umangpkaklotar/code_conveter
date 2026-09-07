import os
import json
import re

from dotenv import load_dotenv
from google import genai
from google.genai._gaos.lib.compat_errors import RateLimitError


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")


client = genai.Client(api_key=api_key)


class GeminiRateLimitError(RuntimeError):
    """Raised when Gemini temporarily refuses a request because of quota."""

    def __init__(self, retry_after_seconds=60):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            "AI quota reached. Please wait and try again, or check your Gemini API billing and limits."
        )


def _strip_code_fences(value):
    """Remove optional Markdown fences without changing code indentation."""
    text = str(value or "").strip()
    match = re.match(r"^```[^\r\n]*\r?\n([\s\S]*?)\r?\n```\s*$", text)
    return match.group(1).strip("\r\n") if match else text


def _parse_json_response(raw_output):
    """Parse JSON even when the model wraps the response in a code fence."""
    try:
        return json.loads(_strip_code_fences(raw_output))
    except (json.JSONDecodeError, TypeError):
        return None


def _create_interaction(prompt):
    try:
        return client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
        )
    except RateLimitError as error:
        message = str(error)
        retry_match = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", message, re.IGNORECASE)
        retry_after = int(float(retry_match.group(1))) + 1 if retry_match else 60
        raise GeminiRateLimitError(retry_after) from error


def convert_code(source_language, target_language, code):

    prompt = f"""
You are an expert programming language code converter.

Convert the complete {source_language} code into {target_language}.

Rules:

1. Preserve the original functionality.
2. Use correct {target_language} syntax.
3. Follow best practices of {target_language}.
4. Return one valid JSON object with exactly two keys: converted_code and explanation.
5. converted_code must be complete, runnable code and contain no Markdown fences, labels, or commentary.
6. Check for missing imports, undefined variables, invalid syntax, and incomplete functions before returning it.
7. Preserve meaningful whitespace, indentation, line breaks, and blank lines. Never minify or compress the code.
8. Organize the file clearly: imports, constants/configuration, functions or classes, and the executable entry point where appropriate.
9. explanation must be plain text with Summary:, Important changes:, and How to run: sections. Use short bullets, not one long paragraph.
10. Do not add text outside the JSON object.

Source Language: {source_language}

Target Language: {target_language}

Source Code:

{code}
"""

    interaction = _create_interaction(prompt)

    raw_output = interaction.output_text.strip()
    result = _parse_json_response(raw_output)
    if isinstance(result, dict):
        converted_code = _strip_code_fences(result.get("converted_code", ""))
        return {
            "converted_code": converted_code,
            "explanation": str(result.get("explanation", "")).strip(),
        }
    else:
        return {
            "converted_code": _strip_code_fences(raw_output),
            "explanation": (
                "Summary:\n"
                f"- Converted the complete program from {source_language} to {target_language}.\n\n"
                "Important changes:\n"
                "- Review library-specific behavior and input/output differences.\n\n"
                "How to run:\n"
                "- Save the code with the correct file extension and run it with the target runtime."
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
4. Preserve meaningful whitespace, indentation, line breaks, and blank lines. Never minify or compress the code.
5. Organize the file clearly: imports, constants/configuration, functions or classes, and the executable entry point where appropriate.
6. explanation must be concise and structured as plain text with these exact sections:
   Summary:
   Key decisions:
   How to run:
   Each section must contain short bullet points beginning with '-'. Do not write a long paragraph.
7. Make reasonable assumptions when the request is incomplete and state them under Key decisions.
8. Include helpful comments in the code only where they improve clarity.
9. Do not add text outside the JSON object.

User Request:

{prompt}
"""

    interaction = _create_interaction(generation_prompt)

    raw_output = interaction.output_text.strip()
    result = _parse_json_response(raw_output)
    if isinstance(result, dict):
        return {
            "detected_language": str(result.get("detected_language", "Unknown")),
            "converted_code": _strip_code_fences(result.get("converted_code", "")),
            "explanation": str(result.get("explanation", "")),
        }
    else:
        return {
            "detected_language": "Unknown",
            "converted_code": _strip_code_fences(raw_output),
            "explanation": (
                "Summary:\n"
                "- Code was generated from your request.\n\n"
                "Key decisions:\n"
                "- The language was inferred from your prompt.\n\n"
                "How to run:\n"
                "- Review the generated code and follow the setup steps included in it."
            ),
        }