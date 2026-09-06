import pytest

from backend import main
from backend.models.schemas import CodeGenerationRequest
from backend.services import code_converter


class FakeInsertResult:
    inserted_id = 42


class FakeConversions:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        self.documents.append(document)
        return FakeInsertResult()


class FakeInteraction:
    output_text = '{"detected_language":"Python", "converted_code":"print(\\"hello\\")", "explanation":"Summary:\\n- Prints a greeting."}'


class FakeClient:
    class interactions:
        @staticmethod
        def create(model, input):
            FakeClient.last_prompt = input
            FakeClient.last_model = model
            return FakeInteraction()


def test_generate_code_parses_gemini_json(monkeypatch):
    monkeypatch.setattr(code_converter, "client", FakeClient())

    result = code_converter.generate_code("Print hello in Python")

    assert result["detected_language"] == "Python"
    assert result["converted_code"] == 'print("hello")'
    assert "Summary:" in result["explanation"]
    assert "Print hello in Python" in FakeClient.last_prompt
    assert "identify the programming language" in FakeClient.last_prompt


def test_generate_endpoint_saves_prompt_and_result(monkeypatch):
    conversions = FakeConversions()
    monkeypatch.setattr(main, "conversions_collection", conversions)
    monkeypatch.setattr(main, "require_token", lambda authorization: {"user_id": "user-7"})
    monkeypatch.setattr(
        main,
        "generate_code",
        lambda prompt: {
            "detected_language": "JavaScript",
            "converted_code": "console.log('hello');",
            "explanation": "Summary:\n- Prints a greeting.",
        },
    )

    result = main.generate(
        CodeGenerationRequest(prompt="Print hello in JavaScript"),
        authorization="Bearer test-token",
    )

    assert result["message"] == "Code generated successfully"
    assert result["converted_code"] == "console.log('hello');"
    assert conversions.documents[0]["user_id"] == "user-7"
    assert conversions.documents[0]["source_language"] == "Prompt"
    assert conversions.documents[0]["input_code"] == "Print hello in JavaScript"
    assert conversions.documents[0]["target_language"] == "JavaScript"


def test_generate_endpoint_rejects_empty_prompt(monkeypatch):
    monkeypatch.setattr(main, "require_token", lambda authorization: {"user_id": "user-7"})

    with pytest.raises(main.HTTPException) as error:
        main.generate(
            CodeGenerationRequest(prompt="   "),
            authorization="Bearer test-token",
        )

    assert error.value.status_code == 400
    assert "describe" in error.value.detail.lower()
