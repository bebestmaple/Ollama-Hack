from typing import Any, Mapping

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from app.core.logging import get_logger

templates = Jinja2Templates(directory="app/templates")

logger = get_logger(__name__)


# 辅助函数：添加消息到请求会话
def add_message(request: Request, message_text: str, message_type: str = "info"):
    if not request.session.get("messages"):
        request.session["messages"] = []
    request.session["messages"].append({"text": message_text, "type": message_type})
    logger.info(f"Added message to session: {message_text}")


def template_response(
    name: str,
    context: dict[str, Any] | None = None,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> HTMLResponse:
    if context is not None:
        request = context.get("request")
        if request and hasattr(request, "session") and request.session.get("messages"):
            messages = request.session.pop("messages")
            context["messages"] = messages
            logger.info(f"Retrieved messages from session: {messages}")
    return templates.TemplateResponse(
        name,
        context,
        status_code=status_code,
        headers=headers,
        media_type=media_type,
        background=background,
    )
