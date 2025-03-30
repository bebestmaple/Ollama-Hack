from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.api_v1.endpoints.auth import require_auth
from app.crud import crud_endpoint
from app.db.database import get_db
from app.schemas.schemas import (
    Endpoint,
    EndpointBulkImport,
    EndpointCreate,
    EndpointResponse,
)
from app.services.endpoint_service import check_endpoint_availability

router = APIRouter(dependencies=[Depends(require_auth)])


@router.post("/", response_model=Endpoint)
async def create_endpoint(endpoint: EndpointCreate, db: Session = Depends(get_db)):
    # 检查端点可用性
    is_available, response_time = check_endpoint_availability(endpoint.url)

    # 创建端点
    db_endpoint = crud_endpoint.create_endpoint(db, endpoint)

    # 更新端点状态
    crud_endpoint.update_endpoint_status(
        db, db_endpoint.id, is_available, response_time
    )

    return db_endpoint


@router.post("/bulk", response_model=List[Endpoint])
async def create_endpoints_bulk(
    endpoints: EndpointBulkImport, db: Session = Depends(get_db)
):
    # 批量创建端点
    db_endpoints = crud_endpoint.create_endpoints_bulk(db, endpoints.endpoints)

    return db_endpoints


@router.get("/", response_model=EndpointResponse)
def read_endpoints(
    skip: int = 0,
    limit: int = 100,
    only_available: bool = False,
    db: Session = Depends(get_db),
):
    endpoints, total_count = crud_endpoint.get_endpoints(
        db, skip=skip, limit=limit, only_available=only_available
    )
    return {
        "count": total_count,
        "endpoints": endpoints,
    }


@router.get("/active", response_model=List[Endpoint])
def read_active_endpoints(db: Session = Depends(get_db)):
    endpoints = crud_endpoint.get_active_endpoints(db)
    return endpoints


@router.get("/available", response_model=List[Endpoint])
def read_available_endpoints(db: Session = Depends(get_db)):
    endpoints = crud_endpoint.get_available_endpoints(db)
    return endpoints


@router.get("/{endpoint_id}", response_model=Endpoint)
def read_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    db_endpoint = crud_endpoint.get_endpoint_by_id(db, endpoint_id)
    if db_endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return db_endpoint


@router.delete("/{endpoint_id}")
def delete_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    success = crud_endpoint.delete_endpoint(db, endpoint_id)
    if not success:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return {"detail": "Endpoint deleted successfully"}
