from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel, ByteSize, Field


class VersionResponse(BaseModel):
    version: str = Field(..., description="Version of ollama")


class GenerateRequest(BaseModel):
    model: str
    prompt: str

    stream: bool = False


class ModelDetails(BaseModel):
    parent_model: Optional[str] = None
    format: Optional[str] = None
    family: Optional[str] = None
    families: Optional[Sequence[str]] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None


class ListModelResponse(BaseModel):
    class Model(BaseModel):
        model: str = ""
        modified_at: Optional[datetime] = None
        digest: Optional[str] = None
        size: Optional[ByteSize] = None
        details: Optional[ModelDetails] = None

    models: Sequence[Model]


class BaseGenerateResponse(BaseModel):
    model: Optional[str] = None
    "Model used to generate response."

    created_at: Optional[str] = None
    "Time when the request was created."

    done: Optional[bool] = None
    "True if response is complete, otherwise False. Useful for streaming to detect the final response."

    done_reason: Optional[str] = None
    "Reason for completion. Only present when done is True."

    total_duration: Optional[int] = None
    "Total duration in nanoseconds."

    load_duration: Optional[int] = None
    "Load duration in nanoseconds."

    prompt_eval_count: Optional[int] = None
    "Number of tokens evaluated in the prompt."

    prompt_eval_duration: Optional[int] = None
    "Duration of evaluating the prompt in nanoseconds."

    eval_count: Optional[int] = None
    "Number of tokens evaluated in inference."

    eval_duration: Optional[int] = None
    "Duration of evaluating inference in nanoseconds."


class GenerateResponse(BaseGenerateResponse):
    """
    Response returned by generate requests.
    """

    response: str
    "Response content. When streaming, this contains a fragment of the response."

    context: Optional[Sequence[int]] = None
    "Tokenized history up to the point of the response."
