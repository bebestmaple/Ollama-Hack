from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, StreamingResponse

from .services import request_forwarding

ollama_router = APIRouter(tags=["ollama"])


@ollama_router.post(
    "/{full_path:path}",
    description="Forward request to best ollama endpoint for the model",
    response_description="Json response from the best ollama endpoint for the model",
)
@ollama_router.get(
    "/{full_path:path}",
    description="Forward request to best ollama endpoint for the model",
    response_description="Json response from the best ollama endpoint for the model",
)
async def _request_forwarding(
    response: StreamingResponse | PlainTextResponse = Depends(request_forwarding),
):
    return response
