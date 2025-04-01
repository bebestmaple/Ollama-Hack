import json as json_lib
from threading import Lock
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crud import crud_model
from app.models.models import Endpoint, PerformanceTest

db_lock = Lock()
logger = get_logger(__name__)


class JsonHTTPException(Exception):
    json_response: Dict[str, Any]
    status_code: int

    def __init__(self, status_code: int, response: Dict[str, Any] | str):
        """
        自定义异常类，用于处理JSON响应
        :param json_response: JSON响应内容
        """
        self.status_code = status_code
        if isinstance(response, str):
            try:
                response = json_lib.loads(response)
            except json_lib.JSONDecodeError:
                response = {
                    "detail": response,
                }

        self.json_response = response
        super().__init__(response)


def json_http_exception_handler(request, exc: JsonHTTPException):
    """
    自定义异常处理器
    :param request: 请求对象
    :param exc: JsonHTTPException异常对象
    :return: JSON响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.json_response,
    )


def initJsonHTTPException(app: FastAPI):
    """
    初始化JsonHTTPException类
    :param app: FastAPI应用实例
    """
    app.add_exception_handler(JsonHTTPException, json_http_exception_handler)


# 获取支持指定模型的所有端点URL，按tokens per second降序排序
def get_endpoints_for_model_name(db: Session, model_name: str) -> List[str]:
    """获取支持指定模型的所有端点URL，按tokens per second降序排序"""
    with db_lock:
        model = crud_model.get_model_by_name(db, model_name)
        if not model:
            logger.warning(f"Model {model_name} not found")
            return []

        # 获取支持该模型的所有端点的性能测试记录
        performance_tests = (
            db.query(PerformanceTest)
            .filter(
                PerformanceTest.model_id == model.id,
                PerformanceTest.tokens_per_second > 0,
            )
            .order_by(PerformanceTest.tokens_per_second.desc())
            .all()
        )

        # 获取这些端点的URL
        endpoint_ids = [test.endpoint_id for test in performance_tests]
        endpoints = (
            db.query(Endpoint)
            .filter(
                Endpoint.id.in_(endpoint_ids),
                Endpoint.is_available,
                Endpoint.is_active,
                Endpoint.is_fake == False,  # noqa: E712
            )
            .all()
        )

        # 按照性能测试记录的顺序排序端点
        endpoint_dict = {endpoint.id: endpoint for endpoint in endpoints}
        sorted_endpoints = [
            endpoint_dict[id] for id in endpoint_ids if id in endpoint_dict
        ]

        return [endpoint.url for endpoint in sorted_endpoints]


# 通过模型名称获取最佳端点
def get_best_endpoint_for_model_name(db: Session, model_name: str) -> Optional[str]:
    """获取支持指定模型的最佳端点URL（向后兼容）"""
    endpoints = get_endpoints_for_model_name(db, model_name)
    return endpoints[0] if endpoints else None


async def send_request_to_ollama(
    url: str,
    method: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    stream: bool = False,
):
    async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
        if stream:
            async with client.stream(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                files=files,
            ) as response:
                if response.status_code != 200:
                    resp_raw = (await response.aread()).decode()
                    raise JsonHTTPException(
                        status_code=response.status_code,
                        response=resp_raw,
                    )

                async for chunk in response.aiter_text():
                    yield chunk
        else:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                files=files,
            )
            if response.status_code != 200:
                raise JsonHTTPException(
                    status_code=response.status_code,
                    response=response.text,
                )
            yield response.json()


async def send_request_to_best_endpoint(
    db: Session,
    model_name: str,
    path: str,
    method: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    stream: bool = False,
):
    endpoints = get_endpoints_for_model_name(db, model_name)
    if not endpoints:
        raise HTTPException(
            status_code=404,
            detail=f"No available endpoints for model {model_name}",
        )

    last_exp = None
    for idx, endpoint in enumerate(endpoints):
        url = f"{endpoint}/{path}"
        logger.info(f"Trying {idx + 1} of {len(endpoints)} endpoints")
        try:
            if stream:
                async for chunk in send_request_to_ollama(
                    url,
                    method,
                    headers=headers,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    stream=stream,
                ):
                    yield chunk
                return
            else:
                chunks = []
                async for chunk in send_request_to_ollama(
                    url,
                    method,
                    headers=headers,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    stream=stream,
                ):
                    chunks.append(chunk)
                if len(chunks) == 1:
                    yield chunks[0]
                else:
                    try:
                        yield json_lib.loads("".join(chunks))
                    except json_lib.JSONDecodeError:
                        # 如果解析失败，返回原始字符串
                        yield "".join(chunks)
                return
        except Exception as e:
            last_exp = e
            continue
    if last_exp:
        logger.warning(f"All endpoints failed for model {model_name}: {last_exp}")
        raise last_exp
