import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crud import crud_api_key, crud_model
from app.db.database import get_db
from app.services.ollama_service import (
    get_best_endpoint_for_model_name,
    send_request_to_ollama,
)

logger = get_logger(__name__)

router = APIRouter()


# API密钥验证依赖项
async def verify_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    api_key = None

    # 从HTTP头中提取API密钥
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "")
    elif x_api_key:
        api_key = x_api_key

    # 如果没有找到API密钥，则抛出异常
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证API密钥
    db_api_key = crud_api_key.get_api_key_by_key(db, api_key)
    if not db_api_key or not db_api_key.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return db_api_key


# 列出所有可用模型
@router.get("/models", response_model=Dict[str, Any])
async def list_models(db: Session = Depends(get_db)):
    models = crud_model.get_available_models(db)

    # 转换为OpenAI兼容格式
    openai_models = []
    for model in models:
        openai_models.append(
            {
                "id": model.name,
                "object": "model",
                "created": 1686935002,
                "owned_by": "ollama-proxy",
            }
        )

    return {"object": "list", "data": openai_models}


# 聊天补全API
@router.post("/chat/completions")
async def chat_completions(
    request_raw: Request,
    db: Session = Depends(get_db),
    _: Any = Depends(verify_api_key),
):
    try:
        # 获取最佳端点
        try:
            request = await request_raw.json()
        except Exception as e:
            logger.error(f"Failed to parse request: {e}")
            raise HTTPException(status_code=400, detail="Invalid request")

        logger.info(f"Request: {request}")
        endpoint_url = get_best_endpoint_for_model_name(db, request.get("model"))
        logger.info(f"Best endpoint for model {request.get("model")}: {endpoint_url}")

        # 处理流式响应
        if request.get("stream", False):

            async def generate_stream():
                async for chunk in send_request_to_ollama(
                    endpoint_url, request, stream=True
                ):
                    logger.info(f"Stream chunk: {chunk}")
                    yield chunk

            return StreamingResponse(generate_stream(), media_type="text/event-stream")

        # 处理非流式响应
        chunks = []
        async for chunk in send_request_to_ollama(endpoint_url, request):
            chunks.append(chunk)
        ollama_response = "".join(chunks)
        return json.loads(ollama_response)
    except Exception as e:
        logger.error(f"Failed to process request: {e}")
        raise HTTPException(status_code=500)
