from typing import Optional

from aiohttp import ClientResponseError
from fastapi import HTTPException, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from src.apikey.models import ApiKeyDB
from src.apikey.service import (
    check_rate_limits,
    get_api_key_from_request,
    log_api_key_usage,
)
from src.core.dependencies import DBSessionDep
from src.endpoint.models import EndpointDB
from src.logging import get_logger

from .client import OllamaClient

logger = get_logger(__name__)

STREAM_BY_DEFAULT_ROUTES = ["api/generate", "api/chat"]


class RequestInfo(BaseModel):
    full_path: str
    method: str
    request: Optional[dict] = None
    headers: dict
    params: dict
    model_name: str
    model_tag: str
    stream: bool

    @classmethod
    async def from_request(cls, full_path: str, request_raw: Request) -> "RequestInfo":
        # Get possible request parameters
        full_path = full_path.strip("/")
        model_name = full_path.split("/")[-1]
        stream = full_path in STREAM_BY_DEFAULT_ROUTES
        request = None
        method = request_raw.method
        try:
            request = await request_raw.json()
            logger.debug(f"Request body: {request}")
            model_name = request.get("model")
            stream = request.get("stream", stream)
        except Exception as e:
            logger.warning(f"Decoding request body failed: {e}")
            pass
        logger.info(f"Request for model: {model_name}, stream: {stream}")

        headers = {
            key: value
            for key, value in request_raw.headers.items()
            if key.lower() not in ["host", "content-length", "authorization"]
        }
        params = dict(request_raw.query_params)

        if not model_name or ":" not in model_name:
            raise HTTPException(status_code=400, detail="Invalid model name")

        name, tag = model_name.split(":")

        return cls(
            full_path=full_path,
            method=method,
            request=request,
            headers=headers,
            params=params,
            model_name=name,
            model_tag=tag,
            stream=stream,
        )


async def send_request_to_endpoint(
    request_info: RequestInfo,
    session: DBSessionDep,
    api_key: ApiKeyDB,
    endpoint: EndpointDB,
):
    # Create a function to log the API key usage after the request completes
    async def log_usage(status_code):
        await log_api_key_usage(
            session,
            api_key,
            request_info.full_path,
            request_info.method,
            request_info.model_name,
            status_code,
        )

    if request_info.stream:

        async def stream_response():
            try:
                async with OllamaClient(endpoint.url).connect() as client:
                    async for response in await client._request(
                        request_info.method,
                        request_info.full_path,
                        json=request_info.request,
                        headers=request_info.headers,
                        params=request_info.params,
                        stream=True,
                    ):
                        yield response
                # Log successful request
                await log_usage(200)
            except ClientResponseError as e:
                logger.error(f"Error: {e}")
                # Log failed request
                await log_usage(e.status)
                yield f"Error: {e.status} {e.message}"
            except Exception as e:
                logger.error(f"Error: {e}")
                # Log failed request
                await log_usage(500)
                yield "Error: Failed to connect to the endpoint"

        return StreamingResponse(stream_response(), media_type="text/event-stream")
    else:
        try:
            async with OllamaClient(endpoint.url).connect() as client:
                response = await client._request(
                    request_info.method,
                    request_info.full_path,
                    json=request_info.request,
                    headers=request_info.headers,
                    params=request_info.params,
                )
                # Log successful request
                await log_usage(200)
                return PlainTextResponse(response)
        except HTTPException as e:
            # Log failed request
            await log_usage(e.status_code)
            raise e
        except ClientResponseError as e:
            # Log failed request
            await log_usage(e.status)
            raise HTTPException(status_code=e.status, detail=e.message) from e
        except Exception as e:
            logger.error(f"Error: {e}")
            # Log failed request
            await log_usage(500)
            raise HTTPException(
                status_code=500, detail="Error: Failed to connect to the endpoint"
            ) from e


async def request_forwarding(
    full_path: str, request_raw: Request, session: DBSessionDep
) -> StreamingResponse | PlainTextResponse:
    from src.endpoint.service import (
        get_ai_model_by_name_and_tag,
        get_best_endpoint_for_model,
    )

    # Get and validate API key
    api_key, user, plan = await get_api_key_from_request(request_raw, session)

    # Check rate limits
    await check_rate_limits(session, api_key, plan)

    # Get request data
    logger.info(f"Received request for path: {full_path}")

    request_info = await RequestInfo.from_request(full_path, request_raw)

    # Get model
    model = await get_ai_model_by_name_and_tag(
        session, request_info.model_name, request_info.model_tag
    )

    if not model.id:
        raise HTTPException(status_code=400, detail="Model not found")

    # Get best endpoint
    endpoint = await get_best_endpoint_for_model(session, model.id)

    return await send_request_to_endpoint(request_info, session, api_key, endpoint)
