from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import Endpoint, Model
from app.schemas.schemas import ModelCreate


# 创建新模型
def create_model(db: Session, model: ModelCreate) -> Model:
    db_model = Model(name=model.name, display_name=model.display_name or model.name)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


# 获取或创建模型
def get_or_create_model(db: Session, model_name: str) -> Model:
    db_model = db.query(Model).filter(Model.name == model_name).first()
    if not db_model:
        db_model = Model(name=model_name, display_name=model_name)
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
    return db_model


# 获取所有模型
def get_models(db: Session, skip: int = 0, limit: int = 100) -> tuple[List[Model], int]:
    return db.query(Model).offset(skip).limit(limit).all(), db.query(Model).count()


# 通过ID获取模型
def get_model_by_id(db: Session, model_id: int) -> Optional[Model]:
    return db.query(Model).filter(Model.id == model_id).first()


# 通过名称获取模型
def get_model_by_name(db: Session, model_name: str) -> Optional[Model]:
    return db.query(Model).filter(Model.name == model_name).first()


# 更新模型的首选端点
def update_preferred_endpoint(
    db: Session, model_id: int, endpoint_id: int, assined_by_user: Optional[bool] = None
) -> Model:
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if db_model:
        db_model.preferred_endpoint_id = endpoint_id
        if assined_by_user is not None:
            db_model.user_assigned_preference = assined_by_user
        db.commit()
        db.refresh(db_model)
    return db_model


# 获取可用模型列表（包含有可用端点的模型）
def get_available_models(db: Session) -> List[Model]:
    # 查询与可用端点相关联的所有模型
    available_models = (
        db.query(Model)
        .join(Model.endpoints)
        .filter(
            Endpoint.is_available, Endpoint.is_active, Model.performance_tests.any()
        )
        .distinct()
        .all()
    )
    return available_models


def search_models(
    db: Session, search_term: str, skip: int = 0, limit: int = 100
) -> tuple[List[Model], int]:
    """
    搜索模型，根据名称或显示名称进行模糊匹配
    """
    search_pattern = f"%{search_term}%"
    return (
        db.query(Model)
        .filter(
            or_(
                Model.name.ilike(search_pattern),
                Model.display_name.ilike(search_pattern),
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    ), count_models_by_search(db, search_term)


def count_models_by_search(db: Session, search_term: str) -> int:
    """
    获取搜索结果的总数
    """
    search_pattern = f"%{search_term}%"
    return (
        db.query(Model)
        .filter(
            or_(
                Model.name.ilike(search_pattern),
                Model.display_name.ilike(search_pattern),
            )
        )
        .count()
    )
