from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from app.api.web.utils import add_message, redirect_with_message, templates
from app.crud import crud_endpoint
from app.db.database import get_db
from app.schemas.schemas import EndpointCreate
from app.services.endpoint_service import check_endpoint_availability

router = APIRouter()


# 端点管理页面
@router.get("/endpoints", response_class=HTMLResponse)
async def endpoint_management(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "endpoints.html",
        {"request": request, "title": "端点管理"},
    )


# 添加端点
@router.post("/endpoints/add")
async def add_endpoint(
    request: Request,
    url: str = Form(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        # 检查端点可用性
        is_available, response_time = await check_endpoint_availability(url)

        # 创建端点
        endpoint_data = EndpointCreate(url=url, name=name or url)
        db_endpoint = crud_endpoint.create_endpoint(db, endpoint_data)

        # 更新端点状态
        crud_endpoint.update_endpoint_status(
            db, db_endpoint.id, is_available, response_time
        )

        add_message(request, f"成功添加端点: {db_endpoint.name}", "success")
    except Exception as e:
        add_message(request, f"添加端点失败: {str(e)}", "error")

    return RedirectResponse(url="/endpoints", status_code=HTTP_303_SEE_OTHER)


# 批量导入端点
@router.post("/endpoints/import")
async def import_endpoints(
    request: Request, endpoints_text: str = Form(...), db: Session = Depends(get_db)
):
    try:
        # 解析文本中的端点
        endpoint_list = []
        for line in endpoints_text.strip().split("\n"):
            line = line.strip()
            if line:
                parts = line.split(" ", 1)
                url = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else url

                # 确保URL格式正确
                if not url.startswith("http"):
                    url = "http://" + url

                endpoint_list.append(EndpointCreate(url=url, name=name))

        if not endpoint_list:
            add_message(request, "未找到有效的端点数据", "error")
            return RedirectResponse(url="/endpoints", status_code=HTTP_303_SEE_OTHER)

        # 批量创建端点
        db_endpoints = crud_endpoint.create_endpoints_bulk(db, endpoint_list)

        # 异步检查每个端点的可用性
        # for endpoint in db_endpoints:
        #     is_available, response_time = await check_endpoint_availability(
        #         endpoint.url
        #     )
        #     crud_endpoint.update_endpoint_status(
        #         db, endpoint.id, is_available, response_time
        #     )

        add_message(request, f"成功导入 {len(db_endpoints)} 个端点", "success")
    except Exception as e:
        add_message(request, f"导入端点失败: {str(e)}", "error")

    return RedirectResponse(url="/endpoints", status_code=HTTP_303_SEE_OTHER)


# 删除端点
@router.get("/endpoints/delete/{endpoint_id}")
async def delete_endpoint(
    request: Request, endpoint_id: int, db: Session = Depends(get_db)
):
    try:
        # 获取端点信息用于消息提示
        endpoint = crud_endpoint.get_endpoint_by_id(db, endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=404, detail="端点不存在")

        endpoint_name = endpoint.name
        success = crud_endpoint.delete_endpoint(db, endpoint_id)

        if success:
            add_message(request, f"成功删除端点: {endpoint_name}", "success")
        else:
            add_message(request, "删除端点失败", "error")
    except Exception as e:
        add_message(request, f"删除端点失败: {str(e)}", "error")

    return RedirectResponse(url="/endpoints", status_code=HTTP_303_SEE_OTHER)


# 刷新单个端点可用性
@router.get("/endpoints/refresh/{endpoint_id}")
async def refresh_endpoint(
    request: Request, endpoint_id: int, db: Session = Depends(get_db)
):
    from app.services.endpoint_service import check_endpoint_availability

    try:
        endpoint = crud_endpoint.get_endpoint(db, endpoint_id)
        if not endpoint:
            messages = [{"type": "error", "text": "找不到指定的端点"}]
            return redirect_with_message("/endpoints", messages)

        # 检查端点可用性
        is_available, response_time = await check_endpoint_availability(endpoint.url)

        # 更新端点状态
        crud_endpoint.update_endpoint_status(
            db, endpoint_id, is_available, response_time
        )

        if is_available:
            messages = [
                {
                    "type": "success",
                    "text": f"端点 {endpoint.name or endpoint.url} 已刷新，状态: 可用",
                }
            ]
        else:
            messages = [
                {
                    "type": "error",
                    "text": f"端点 {endpoint.name or endpoint.url} 已刷新，状态: 不可用",
                }
            ]

        return redirect_with_message("/endpoints", messages)
    except Exception as e:
        messages = [{"type": "error", "text": f"刷新端点时出错: {str(e)}"}]
        return redirect_with_message("/endpoints", messages)
