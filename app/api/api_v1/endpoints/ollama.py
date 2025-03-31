import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crud import crud_api_key, crud_model
from app.db.database import get_db
from app.services.ollama_service import (
    get_endpoints_for_model_name,
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


async def try_send_request(
    endpoint_url: str, request: Dict[str, Any], stream: bool = False
):
    """尝试向端点发送请求，如果失败则抛出异常"""
    try:
        if stream:
            # 直接返回异步生成器，而不是包装它的函数
            return send_request_to_ollama(endpoint_url, request, stream=True)
        else:
            chunks = []
            async for chunk in send_request_to_ollama(endpoint_url, request):
                chunks.append(chunk)
            return "".join(chunks)
    except Exception as e:
        logger.error(f"Failed to send request to {endpoint_url}: {str(e)}")
        raise e


# 聊天补全API
@router.post("/chat/completions")
async def chat_completions(
    request_raw: Request,
    db: Session = Depends(get_db),
    _: Any = Depends(verify_api_key),
):
    try:
        # 获取请求数据
        try:
            request = await request_raw.json()
        except Exception as e:
            logger.error(f"Failed to parse request: {e}")
            raise HTTPException(status_code=400, detail="Invalid request")

        # 获取所有支持该模型的端点，按性能排序
        model_name = request.get("model")
        logger.info(f"Request for model: {model_name}")
        endpoint_urls = get_endpoints_for_model_name(db, model_name)

        if not endpoint_urls:
            raise HTTPException(
                status_code=404,
                detail=f"No available endpoints found for model {model_name}",
            )

        logger.info(f"{len(endpoint_urls)} endpoints found for model {model_name}")

        # 处理流式响应
        if request.get("stream", False):

            async def generate_stream():
                # 按顺序尝试每个端点
                for idx, endpoint_url in enumerate(endpoint_urls):
                    try:
                        logger.info(
                            f"Trying endpoint {idx+1}/{len(endpoint_urls)}: {endpoint_url}"
                        )
                        generator = await try_send_request(
                            endpoint_url, request, stream=True
                        )
                        async for chunk in generator:
                            yield chunk
                        # 如果成功完成，则退出循环
                        return
                    except Exception as e:
                        logger.warning(f"Endpoint {endpoint_url} failed: {str(e)}")
                        # 如果这是最后一个端点，抛出异常
                        if idx == len(endpoint_urls) - 1:
                            logger.error("All endpoints failed")
                            yield json.dumps({"error": "All endpoints failed"})
                            return
                        # 否则尝试下一个端点
                        continue

            return StreamingResponse(generate_stream(), media_type="text/event-stream")

        # 处理非流式响应
        last_error = None
        for idx, endpoint_url in enumerate(endpoint_urls):
            try:
                logger.info(
                    f"Trying endpoint {idx+1}/{len(endpoint_urls)}: {endpoint_url}"
                )
                response = await try_send_request(endpoint_url, request, stream=False)
                return json.loads(response)
            except Exception as e:
                last_error = e
                logger.warning(f"Endpoint {endpoint_url} failed: {str(e)}")
                continue

        # 如果所有端点都失败
        logger.error(f"All endpoints failed. Last error: {str(last_error)}")
        raise HTTPException(
            status_code=500, detail="All endpoints failed to process the request"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
