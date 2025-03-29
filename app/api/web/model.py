from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.api.api_v1.endpoints.auth import require_auth
from app.api.web.utils import add_message, template_response
from app.crud import crud_model
from app.db.database import get_db

router = APIRouter(dependencies=[Depends(require_auth)])


# 模型管理页面
@router.get("/models", response_class=HTMLResponse)
async def model_management(request: Request, db: Session = Depends(get_db)):
    return template_response(
        "models.html",
        {
            "request": request,
            "title": "模型管理",
        },
    )


@router.get("/models/{model_id}/refresh-performance")
async def refresh_model_performance(
    request: Request,
    model_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(require_auth),
):
    try:
        model = crud_model.get_model_by_id(db, model_id)
        if not model:
            add_message(request, "未找到指定模型", "error")
            return RedirectResponse(url="/models", status_code=HTTP_303_SEE_OTHER)

        # 调用服务中的性能测试函数作为后台任务
        from app.services.endpoint_service import refresh_model_performance

        background_tasks.add_task(refresh_model_performance, db, model_id)

        add_message(request, f"已开始刷新模型 {model.name} 的性能测试", "info")
    except Exception as e:
        add_message(request, f"刷新模型性能测试失败: {str(e)}", "error")

    return RedirectResponse(url="/models", status_code=HTTP_303_SEE_OTHER)
