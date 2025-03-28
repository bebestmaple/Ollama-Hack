from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.api.web.utils import add_message, templates
from app.crud import crud_endpoint, crud_model
from app.db.database import get_db

router = APIRouter()


# 模型管理页面
@router.get("/models", response_class=HTMLResponse)
async def model_management(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "models.html",
        {
            "request": request,
            "title": "模型管理",
        },
    )


# 更新首选端点
@router.get("/models/{model_id}/set-preferred-endpoint/{endpoint_id}")
async def set_preferred_endpoint(
    request: Request, model_id: int, endpoint_id: int, db: Session = Depends(get_db)
):
    try:
        # 更新模型的首选端点
        model = crud_model.update_preferred_endpoint(db, model_id, endpoint_id, True)
        endpoint = crud_endpoint.get_endpoint_by_id(db, endpoint_id)

        if model and endpoint:
            add_message(
                request,
                f"已将模型 {model.name} 的首选端点设置为 {endpoint.name}",
                "success",
            )
        else:
            add_message(request, "更新首选端点失败", "error")
    except Exception as e:
        add_message(request, f"更新首选端点失败: {str(e)}", "error")

    return RedirectResponse(url="/models", status_code=HTTP_303_SEE_OTHER)


# 刷新模型
@router.get("/models/refresh")
async def refresh_models(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    try:
        # 获取所有可用端点
        endpoints = crud_endpoint.get_available_endpoints(db)

        if not endpoints:
            add_message(request, "没有可用的端点，无法刷新模型", "error")
            return RedirectResponse(url="/models", status_code=HTTP_303_SEE_OTHER)

        # 调用端点服务中的刷新模型函数作为后台任务
        from app.services.endpoint_service import refresh_available_models

        background_tasks.add_task(refresh_available_models, db)

        add_message(request, "模型刷新任务已启动，请稍后查看进度", "info")
    except Exception as e:
        add_message(request, f"刷新模型任务启动失败: {str(e)}", "error")

    return RedirectResponse(url="/models", status_code=HTTP_303_SEE_OTHER)


@router.get("/models/{model_id}/refresh-performance")
async def refresh_model_performance(
    request: Request,
    model_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
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
