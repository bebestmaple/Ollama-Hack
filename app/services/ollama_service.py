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
    def __init__(self, status_code: int, json_response: Dict[str, Any] | str):
        """
        自定义异常类，用于处理JSON响应
        :param json_response: JSON响应内容
        """
        self.status_code = status_code
        if isinstance(json_response, str):
            json_response = {"detail": json_response}
        elif not isinstance(json_response, dict):
            raise ValueError("json_response must be a dict or str")
        self.json_response = json_response
        super().__init__(json_response)


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


# 向Ollama端点发送请求
async def send_chat_completions_request_to_ollama(
    endpoint_url: str, request: Dict[str, Any], stream: bool = False
):
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
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


# 获取模型详情
async def send_model_info_request_to_ollama(endpoint_url: str, model_name: str):
    async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
        url = f"{endpoint_url}/v1/models/{model_name}"
        # 发送请求到Ollama获取模型详情
        response = await client.get(url)

        if response.status_code != 200:
            if json_response := response.json():
                # 如果响应是JSON格式，解析并返回
                raise JsonHTTPException(
                    status_code=response.status_code,
                    json_response=json_response,
                )

            raise JsonHTTPException(
                status_code=response.status_code,
                json_response=f"Failed to get model info: {response.text}",
            )

        return response.json()
