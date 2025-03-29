from typing import Any, Dict

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import crud_model, crud_performance


# 通过模型名称获取最佳端点
def get_best_endpoint_for_model_name(db: Session, model_name: str) -> str:
    model = crud_model.get_model_by_name(db, model_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

    best_endpoint = crud_performance.get_best_endpoint_for_model(db, model.id)
    if not best_endpoint:
        raise HTTPException(
            status_code=404, detail=f"No available endpoint for model {model_name}"
        )

    return best_endpoint.url


# 向Ollama端点发送请求
async def send_request_to_ollama(
    endpoint_url: str, request: Dict[str, Any], stream: bool = False
):
    async with httpx.AsyncClient(timeout=60.0) as client:
        url = f"{endpoint_url}/v1/chat/completions"
        if stream:
            # 流式处理
            async with client.stream(
                "POST",
                url,
                json=request,
                timeout=None,
            ) as response:
                if response.status_code != 200:
                    resp = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama API error: {resp.decode()}",  # 读取错误信息
                    )

                async for chunk in response.aiter_text():
                    yield chunk

        else:
            # 一次性处理
            response = await client.post(url, json=request)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama API error: {response.text}",
                )

            yield response.text
