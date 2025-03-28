from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import crud_model, crud_performance
from app.db.database import get_db
from app.schemas.schemas import (
    EndpointBase,
    Model,
    ModelGetResponse,
    PerformanceTestsResponse,
    PerformanceTestWithEndpoint,
)
from app.services.endpoint_service import refresh_model_performance

router = APIRouter()


@router.get("/", response_model=ModelGetResponse)
def read_models(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    获取模型列表，支持搜索功能
    """
    if search:
        models, count = crud_model.search_models(db, search, skip=skip, limit=limit)
    else:
        models, count = crud_model.get_models(db, skip=skip, limit=limit)
    return {
        "count": count,
        "models": models,
    }


@router.get("/available", response_model=List[Model])
def read_available_models(db: Session = Depends(get_db)):
    models = crud_model.get_available_models(db)
    return models


@router.get("/{model_id}", response_model=Model)
def read_model(model_id: int, db: Session = Depends(get_db)):
    db_model = crud_model.get_model_by_id(db, model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return db_model


@router.get("/{model_id}/performance", response_model=PerformanceTestsResponse)
def read_model_performance(
    model_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    db_model = crud_model.get_model_by_id(db, model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    performance_tests, count = crud_performance.get_model_performance_tests(
        db, model_id, skip=skip, limit=limit
    )
    return PerformanceTestsResponse(
        count=count,
        performance_tests=[
            PerformanceTestWithEndpoint(
                id=test.id,
                model_id=test.model_id,
                endpoint_id=test.endpoint_id,
                response_time=test.response_time,
                tokens_per_second=test.tokens_per_second,
                timestamp=test.timestamp,
                endpoint=EndpointBase(
                    url=test.endpoint.url,
                    name=test.endpoint.name,
                ),
            )
            for test in performance_tests
        ],
    )


@router.put("/{model_id}/preferred-endpoint/{endpoint_id}")
def update_preferred_endpoint(
    model_id: int, endpoint_id: int, db: Session = Depends(get_db)
):
    db_model = crud_model.get_model_by_id(db, model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    updated_model = crud_model.update_preferred_endpoint(db, model_id, endpoint_id)
    return {
        "detail": f"Preferred endpoint for model {updated_model.name} updated successfully"
    }


@router.post("/{model_id}/refresh-performance")
async def refresh_model_performance_router(
    model_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    try:
        db_model = crud_model.get_model_by_id(db, model_id)
        if db_model is None:
            raise HTTPException(status_code=404, detail="Model not found")

        # 启动后台任务
        background_tasks.add_task(refresh_model_performance, db, model_id)

        return {"detail": f"已开始刷新模型 {db_model.name} 的性能测试"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新模型性能测试失败: {str(e)}")
