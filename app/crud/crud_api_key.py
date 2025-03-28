import secrets
import string
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import ApiKey
from app.schemas.schemas import ApiKeyCreate


# 生成随机API密钥
def generate_api_key(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# 创建新API密钥
def create_api_key(db: Session, api_key: ApiKeyCreate) -> ApiKey:
    key = generate_api_key()
    db_api_key = ApiKey(key=key, name=api_key.name)
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key


# 获取所有API密钥
def get_api_keys(db: Session, skip: int = 0, limit: int = 100) -> List[ApiKey]:
    return db.query(ApiKey).offset(skip).limit(limit).all()


# 通过ID获取API密钥
def get_api_key_by_id(db: Session, api_key_id: int) -> Optional[ApiKey]:
    return db.query(ApiKey).filter(ApiKey.id == api_key_id).first()


# 通过密钥获取API密钥
def get_api_key_by_key(db: Session, key: str) -> Optional[ApiKey]:
    return db.query(ApiKey).filter(ApiKey.key == key, ApiKey.is_active).first()


# 停用API密钥
def deactivate_api_key(db: Session, api_key_id: int) -> ApiKey:
    db_api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
    if db_api_key:
        db_api_key.is_active = False
        db.commit()
        db.refresh(db_api_key)
    return db_api_key


# 删除API密钥
def delete_api_key(db: Session, api_key_id: int) -> bool:
    db_api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
    if db_api_key:
        db.delete(db_api_key)
        db.commit()
        return True
    return False
