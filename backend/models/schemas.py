from pydantic import BaseModel


class CodeConversionRequest(BaseModel):
    source_language: str
    target_language: str
    code: str