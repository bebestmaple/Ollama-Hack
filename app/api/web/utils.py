import json

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.logging import get_logger

templates = Jinja2Templates(directory="app/templates")

logger = get_logger(__name__)


# 辅助函数：添加消息到请求会话
def add_message(request: Request, message_text: str, message_type: str = "info"):
    if not request.session.get("messages"):
        request.session["messages"] = []
    request.session["messages"].append({"text": message_text, "type": message_type})
    logger.info(f"Added message to session: {message_text}")


# 消息中间件 - 从会话中获取消息并传递给模板
async def message_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.session.get("messages"):
        messages = request.session.pop("messages")
        if isinstance(response, HTMLResponse):
            response.context["messages"] = messages
    return response


# 创建带有消息的重定向响应
def redirect_with_message(url: str, messages: list):
    return RedirectResponse(
        url=url,
        status_code=303,
        headers={"HX-Trigger": json.dumps({"showMessage": messages})},
    )
