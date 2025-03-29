from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import relationship

from app.db.database import Base

# 端点和模型的多对多关系表
endpoint_model = Table(
    "endpoint_model",
    Base.metadata,
    Column("endpoint_id", Integer, ForeignKey("endpoints.id")),
    Column("model_id", Integer, ForeignKey("models.id")),
)


class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float, default=0.0)  # 毫秒

    # 与模型的关系
    models = relationship("Model", secondary=endpoint_model, back_populates="endpoints")

    # 作为性能测试记录的关系
    performance_tests = relationship("PerformanceTest", back_populates="endpoint")


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    display_name = Column(String)

    # 与端点的关系
    endpoints = relationship(
        "Endpoint", secondary=endpoint_model, back_populates="models"
    )

    # 作为性能测试记录的关系
    performance_tests = relationship("PerformanceTest", back_populates="model")

    # 该模型的首选端点
    preferred_endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=True)
    user_assigned_preference = Column(Boolean, default=False)


class PerformanceTest(Base):
    __tablename__ = "performance_tests"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"))
    model_id = Column(Integer, ForeignKey("models.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    tokens_per_second = Column(Float, default=0.0)
    response_time = Column(Float, default=0.0)  # 毫秒

    # 关系
    endpoint = relationship("Endpoint", back_populates="performance_tests")
    model = relationship("Model", back_populates="performance_tests")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
