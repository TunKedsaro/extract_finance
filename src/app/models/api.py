from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExtractionRequest(APIModel):
    input_path: NonEmptyString = Field(
        description="Path relative to the configured INPUT_DIR. Absolute paths are rejected."
    )


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str


class ErrorDetail(APIModel):
    code: str
    message: str


class ErrorResponse(APIModel):
    error: ErrorDetail
