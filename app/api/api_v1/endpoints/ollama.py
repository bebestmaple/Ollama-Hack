from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crud import crud_api_key, crud_model
from app.db.database import get_db
from app.services.ollama_service import (
    JsonHTTPException,
    send_request_to_best_endpoint,
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


# async def try_send_request(
#     endpoint_url: str, request: Dict[str, Any], stream: bool = False
# ):
#     """尝试向端点发送请求，如果失败则抛出异常"""
#     try:
#         if stream:
#             # 直接返回异步生成器，而不是包装它的函数
#             return send_chat_completions_request_to_ollama(
#                 endpoint_url, request, stream=True
#             )
#         else:
#             chunks = []
#             async for chunk in send_chat_completions_request_to_ollama(
#                 endpoint_url, request
#             ):
#                 chunks.append(chunk)
#             return "".join(chunks)
#     except Exception as e:
#         logger.error(f"Failed to send request to {endpoint_url}: {str(e)}")
#         raise e

# @router.get("/models/{model_name}", response_model=Dict[str, Any])
# async def get_model(
#     model_name: str, db: Session = Depends(get_db), _: Any = Depends(verify_api_key)
# ):
#     """获取指定模型的详细信息"""
#     model = crud_model.get_model_by_name(db, model_name)
#     if not model:
#         raise HTTPException(status_code=404, detail="Model not found")

#     # 获取支持该模型的所有端点，按性能排序
#     endpoint_urls = get_endpoints_for_model_name(db, model_name)
#     if not endpoint_urls:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No available endpoints found for model {model_name}",
#         )

#     logger.info(f"{len(endpoint_urls)} endpoints found for model {model_name}")

#     exp = None
#     try:
#         for endpoint_url in endpoint_urls:
#             try:
#                 # 向端点发送请求以获取模型信息
#                 return await send_model_info_request_to_ollama(endpoint_url, model_name)
#             except Exception as e:
#                 logger.warning(
#                     f"Failed to get model info from {endpoint_url}: {str(e)}"
#                 )
#                 continue
#         # 如果所有端点都失败，抛出异常
#         raise (
#             exp
#             if exp
#             else HTTPException(
#                 status_code=500,
#                 detail="Failed to get model info from all endpoints",
#             )
#         )
#     except JsonHTTPException:
#         raise
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed to get model info: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail="Failed to get model info from all endpoints",
#         )


# async def try_send_request(
#     endpoint_url: str, request: Dict[str, Any], stream: bool = False
# ):
#     """尝试向端点发送请求，如果失败则抛出异常"""
#     try:
#         if stream:
#             # 直接返回异步生成器，而不是包装它的函数
#             return send_chat_completions_request_to_ollama(
#                 endpoint_url, request, stream=True
#             )
#         else:
#             chunks = []
#             async for chunk in send_chat_completions_request_to_ollama(
#                 endpoint_url, request
#             ):
#                 chunks.append(chunk)
#             return "".join(chunks)
#     except Exception as e:
#         logger.error(f"Failed to send request to {endpoint_url}: {str(e)}")
#         raise e


# 聊天补全API
@router.post("/{full_path:path}", response_model=Dict[str, Any])
@router.get("/{full_path:path}", response_model=Dict[str, Any])
async def chat_completions(
    full_path: str,
    request_raw: Request,
    db: Session = Depends(get_db),
    _: Any = Depends(verify_api_key),
):
    try:
        # 获取请求数据
        full_path = f"v1/{full_path}"
        logger.info(f"Received request for path: {full_path}")
        model_name = ""
        stream = False
        request = None
        try:
            if request_raw.method == "GET":
                raise

            request = await request_raw.json()
            model_name = request.get("model")
            stream = request.get("stream", False)
        except Exception:
            model_name = full_path.split("/")[-1]
        logger.info(f"Request for model: {model_name}")

        headers = {
            key: value
            for key, value in request_raw.headers.items()
            if key.lower() not in ["host", "content-length", "authorization"]
        }
        params = {key: value for key, value in request_raw.query_params.items()}

        # 处理流式响应
        if stream:

            async def generate_stream():
                async for chunk in await send_request_to_best_endpoint(
                    db,
                    model_name,
                    path=full_path,
                    method=request_raw.method,
                    headers=headers,
                    params=params,
                    json=request,
                    stream=True,
                ):
                    logger.debug(f"Chunk received: {chunk}")
                    yield chunk
                return

            return StreamingResponse(generate_stream(), media_type="text/event-stream")
        else:
            # 处理非流式响应
            response = await send_request_to_best_endpoint(
                db,
                model_name,
                path=full_path,
                method=request_raw.method,
                headers=headers,
                params=params,
                json=request,
            )
            return response
    except HTTPException:
        raise
    except JsonHTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
