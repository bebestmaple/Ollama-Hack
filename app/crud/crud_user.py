import secrets
import string
from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.models import User
from app.schemas.schemas import UserCreate

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 生成随机密码
def generate_password(length: int = 16) -> str:
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return "".join(secrets.choice(characters) for _ in range(length))


# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# 对密码进行哈希处理
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# 获取所有用户
def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


# 根据用户名获取用户
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


# 创建新用户
def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username, password_hash=hashed_password, is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# 验证用户凭据
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# 检查用户表是否为空
def is_user_table_empty(db: Session) -> bool:
    return db.query(User).count() == 0


# 创建初始管理员账户
def create_initial_admin(db: Session) -> tuple[str, str]:
    username = "admin"
    password = generate_password()

    user_data = UserCreate(username=username, password=password, is_admin=True)
    create_user(db, user_data)

    return username, password


# 更新用户密码
def update_password(db: Session, username: str, new_password: str) -> bool:
    user = get_user_by_username(db, username)
    if not user:
        return False

    hashed_password = get_password_hash(new_password)
    user.password_hash = hashed_password
    db.commit()
    return True
