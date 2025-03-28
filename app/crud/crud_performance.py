from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Endpoint, Model, PerformanceTest
from app.schemas.schemas import PerformanceTestCreate


# 创建性能测试记录
def create_performance_test(
    db: Session, test: PerformanceTestCreate
) -> PerformanceTest:
    # 如果已有相同的测试记录，更新其值
    existing_test = (
        db.query(PerformanceTest)
        .filter(
            PerformanceTest.endpoint_id == test.endpoint_id,
            PerformanceTest.model_id == test.model_id,
        )
        .first()
    )
    if existing_test:
        existing_test.tokens_per_second = test.tokens_per_second
        existing_test.response_time = test.response_time
        existing_test.timestamp = datetime.utcnow()
        db.commit()
        db.refresh(existing_test)
        return existing_test

    # 创建新的测试记录
    db_test = PerformanceTest(
        endpoint_id=test.endpoint_id,
        model_id=test.model_id,
        tokens_per_second=test.tokens_per_second,
        response_time=test.response_time,
        timestamp=datetime.utcnow(),
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test


# 获取模型最佳端点
def get_best_endpoint_for_model(db: Session, model_id: int) -> Optional[Endpoint]:
    # 首先检查是否有手动设置的首选端点
    model = db.query(Model).filter(Model.id == model_id).first()
    if model and model.preferred_endpoint_id and model.user_assigned_preference:
        preferred_endpoint = (
            db.query(Endpoint)
            .filter(
                Endpoint.id == model.preferred_endpoint_id,
                Endpoint.is_available,
                Endpoint.is_active,
            )
            .first()
        )
        if preferred_endpoint:
            return preferred_endpoint

    # 查找性能测试中响应最快的端点
    best_test = (
        db.query(PerformanceTest)
        .filter(PerformanceTest.model_id == model_id)
        .join(Endpoint)
        .filter(Endpoint.is_available, Endpoint.is_active)
        .order_by(PerformanceTest.tokens_per_second.desc())
        .order_by(PerformanceTest.response_time.asc())
        .first()
    )

    # 如果找到性能测试记录，返回相应的端点
    if best_test:
        return best_test.endpoint

    # 如果没有性能测试记录，返回响应时间最快的可用端点
    endpoints = (
        db.query(Endpoint)
        .join(Model.endpoints)
        .filter(
            Model.id == model_id,
            Endpoint.is_available,
            Endpoint.is_active,
        )
        .order_by(Endpoint.response_time.asc())
        .all()
    )

    return endpoints[0] if endpoints else None


# 获取模型的所有端点性能测试
def get_model_performance_tests(
    db: Session, model_id: int, skip: int = 0, limit: int = 10
) -> tuple[List[PerformanceTest], int]:
    return (
        db.query(PerformanceTest)
        .filter(PerformanceTest.model_id == model_id)
        .join(Endpoint)
        .filter(Endpoint.is_active, Endpoint.is_available)
        .order_by(PerformanceTest.tokens_per_second.desc())
        .order_by(PerformanceTest.response_time.asc())
        .offset(skip)
        .limit(limit)
        .all()
    ), (db.query(PerformanceTest).filter(PerformanceTest.model_id == model_id).count())


def delete_performance_test_if_exists(db: Session, model_id: int, endpoint_id: int):
    db_test = (
        db.query(PerformanceTest)
        .filter(
            PerformanceTest.model_id == model_id,
            PerformanceTest.endpoint_id == endpoint_id,
        )
        .first()
    )
    if db_test:
        db.delete(db_test)
        db.commit()
        return True
    return False
