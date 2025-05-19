import asyncio
import json as json_lib
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Literal, Type, TypeVar, overload

import aiohttp
from pydantic import BaseModel

from src.logging import get_logger

from .schema import (
    GenerateRequest,
    GenerateResponse,
    ListModelResponse,
    VersionResponse,
)

T = TypeVar("T", bound=BaseModel)

logger = get_logger(__name__)


class OllamaClient:
    def __init__(self, url: str, timeout: int = 10 * 60):
        self.url = url
        self.timeout = timeout

    @property
    def session(self) -> aiohttp.ClientSession:
        """
        Get the session.
        """
        if not hasattr(self, "_session") or self._session is None:
            raise RuntimeError("Not connected, please call connect() first.")
        return self._session

    @asynccontextmanager
    async def connect(self) -> AsyncIterator["OllamaClient"]:
        """
        Create a session context manager.
        """
        try:
            self._session = aiohttp.ClientSession(
                self.url.rstrip("/"), timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            yield self
        finally:
            if self._session is not None:
                await self._session.close()
                self._session = None

    async def _request_raw(
        self, method: str, path: str, *args, json: Any | None = None, **kwargs
    ) -> bytes:
        """
        Make a raw request to the Ollama endpoint.
        Returns:
            bytes: the response content
        """
        async with self.session.request(
            method, path, *args, json=json, ssl=False, **kwargs
        ) as response:
            if response.status >= 300 or response.status < 200:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Error fetching {path}: {response.reason}",
                )
            return await response.content.read()

    async def _streamed_request_raw(
        self,
        method: str,
        path: str,
        *args,
        json: Any | None = None,
        response_model: Type[T] | None = None,
        **kwargs,
    ) -> AsyncIterator[T] | AsyncIterator[bytes]:
        async with self.session.request(
            method, path, *args, json=json, ssl=False, **kwargs
        ) as response:
            if response.status >= 300 or response.status < 200:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Error fetching {path}: {response.reason}",
                )
            async for item in response.content:
                if response_model:
                    try:
                        yield response_model(**json_lib.loads(item))
                    except Exception as e:
                        logger.debug(f"Error parsing response: {e}")
                        logger.debug(f"Response content: {item}")
                        continue
                else:
                    yield item
        return

    @overload
    async def _request(
        self,
        method: str,
        path: str,
        *args,
        json: Any | None = None,
        response_model: Type[T],
        stream: Literal[False] = False,
        **kwargs,
    ) -> T: ...

    @overload
    async def _request(
        self,
        method: str,
        path: str,
        *args,
        json: Any | None = None,
        response_model: Type[T],
        stream: Literal[True] = True,
        **kwargs,
    ) -> AsyncIterator[T]: ...

    @overload
    async def _request(
        self,
        method: str,
        path: str,
        *args,
        json: Any | None = None,
        response_model: Type[T],
        stream: bool,
        **kwargs,
    ) -> AsyncIterator[T] | T: ...

    @overload
    async def _request(
        self,
        method: str,
        path: str,
        *args,
        json: Any | None = None,
        response_model: Literal[None] = None,
        stream: Literal[False] = False,
        **kwargs,
    ) -> bytes: ...

    @overload
    async def _request(
        self,
        method: str,
        path: str,
        *args,
        json: Any | None = None,
        response_model: Literal[None] = None,
        stream: Literal[True] = True,
        **kwargs,
    ) -> AsyncIterator[bytes]: ...

    async def _request(
        self,
        method: str,
        path: str,
        *args,
        json: Any | None = None,
        response_model: Type[T] | None = None,
        stream: bool = False,
        **kwargs,
    ) -> T | AsyncIterator[T] | bytes | AsyncIterator[bytes]:
        """
        Make a request to the Ollama endpoint.

        Returns:
            T | bytes: if stream is False, the response model
            AsyncIterator[T] | AsyncIterator[bytes]: if stream is True, an async iterator of the response model
        """

        if stream:
            return self._streamed_request_raw(
                method, path, *args, json=json, response_model=response_model, **kwargs
            )  # type: ignore

        result = await self._request_raw(method, path, *args, json=json, **kwargs)
        return response_model(**json_lib.loads(result)) if response_model else result

    async def version(self) -> VersionResponse:
        """
        Get the version of the Ollama endpoint.
        """
        return await self._request(
            "GET",
            "/api/version",
            response_model=VersionResponse,
        )

    async def tags(self) -> ListModelResponse:
        """
        Get the tags of the Ollama endpoint.
        """
        return await self._request("GET", "/api/tags", response_model=ListModelResponse)

    @overload
    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        stream: Literal[True] = True,
    ) -> AsyncIterator[GenerateResponse]: ...

    @overload
    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        stream: Literal[False] = False,
    ) -> GenerateResponse: ...

    async def generate(
        self, model: str, prompt: str, *, stream: bool = True
    ) -> GenerateResponse | AsyncIterator[GenerateResponse]:
        """
        Generate a response from the Ollama endpoint.
        """
        return await self._request(
            "POST",
            "/api/generate",
            json=GenerateRequest(model=model, prompt=prompt, stream=stream).model_dump(
                exclude_none=True
            ),
            response_model=GenerateResponse,
            stream=stream,
        )


if __name__ == "__main__":
    import os

    async def main():
        async with OllamaClient(os.environ["ENDPOINT"]).connect() as client:
            print(await client.version())
            print(await client.tags())
            async for response in await client.generate(
                model="deepseek-r1:1.5b",
                prompt="Hello, how are you?",
                stream=True,
            ):
                print(response)

    asyncio.run(main())
