from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Endpoint, Model
from app.schemas.schemas import EndpointCreate


# 创建新端点
def create_endpoint(db: Session, endpoint: EndpointCreate) -> Endpoint:
    # 检查端点是否已存在
    existing_endpoint = db.query(Endpoint).filter(Endpoint.url == endpoint.url).first()
    if existing_endpoint:
        # 如果已存在，更新名称
        existing_endpoint.name = endpoint.name or existing_endpoint.url
        db.commit()
        db.refresh(existing_endpoint)
        return existing_endpoint

    # 如果不存在，创建新的端点
    db_endpoint = Endpoint(
        url=endpoint.url,
        name=endpoint.name or endpoint.url,
    )
    db.add(db_endpoint)
    db.commit()
    db.refresh(db_endpoint)
    return db_endpoint


# 批量创建端点
def create_endpoints_bulk(
    db: Session, endpoints: List[EndpointCreate]
) -> List[Endpoint]:
    db_endpoints = []
    existing_urls = set(row[0] for row in db.query(Endpoint.url).all())

    for endpoint in endpoints:
        # 检查端点是否已存在
        if endpoint.url not in existing_urls:
            db_endpoint = Endpoint(
                url=endpoint.url,
                name=endpoint.name or endpoint.url,
                is_available=False,  # 初始设为不可用，后续检查
                response_time=0,
                last_checked=datetime.utcnow(),
            )
            db.add(db_endpoint)
            db_endpoints.append(db_endpoint)
            existing_urls.add(endpoint.url)  # 添加到已存在集合中防止重复
        else:
            # 如果已存在，更新名称
            existing_endpoint = (
                db.query(Endpoint).filter(Endpoint.url == endpoint.url).first()
            )
            if existing_endpoint:
                existing_endpoint.name = endpoint.name or existing_endpoint.url
                db_endpoints.append(existing_endpoint)

    if db_endpoints:
        db.commit()
        for endpoint in db_endpoints:
            db.refresh(endpoint)

    return db_endpoints


# 获取所有端点
def get_endpoints(
    db: Session, skip: int = 0, limit: int | None = None, only_available: bool = False
) -> tuple[List[Endpoint], int]:
    query = db.query(Endpoint)
    if only_available:
        query = query.filter(Endpoint.is_available)
    return (
        (
            query.offset(skip).limit(limit).all()
            if limit is not None
            else query.offset(skip).all()
        ),
        query.count(),
    )


# 获取活跃端点
def get_active_endpoints(db: Session) -> List[Endpoint]:
    return db.query(Endpoint).filter(Endpoint.is_active).all()


# 获取可用端点
def get_available_endpoints(db: Session) -> List[Endpoint]:
    return db.query(Endpoint).filter(Endpoint.is_active, Endpoint.is_available).all()


# 通过ID获取端点
def get_endpoint_by_id(db: Session, endpoint_id: int) -> Optional[Endpoint]:
    return db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()


# 更新端点状态
def update_endpoint_status(
    db: Session, endpoint_id: int, is_available: bool, response_time: float = 0.0
) -> Endpoint:
    db_endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if db_endpoint:
        db_endpoint.is_available = is_available
        db_endpoint.last_checked = datetime.utcnow()
        db_endpoint.response_time = response_time
        db.commit()
        db.refresh(db_endpoint)
    return db_endpoint


# 删除端点
def delete_endpoint(db: Session, endpoint_id: int) -> bool:
    db_endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if db_endpoint:
        db.delete(db_endpoint)
        db.commit()
        return True
    return False


# 关联端点和模型
def associate_endpoint_with_model(db: Session, endpoint_id: int, model_id: int) -> bool:
    db_endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    db_model = db.query(Model).filter(Model.id == model_id).first()

    if db_endpoint and db_model:
        if db_model not in db_endpoint.models:
            db_endpoint.models.append(db_model)
            db.commit()
        return True
    return False
