from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建SQLAlchemy引擎
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})

# 创建SessionLocal类，每个请求的数据库会话将使用这个类的实例
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类，数据库模型将继承这个类
Base = declarative_base()


# 获取数据库会话的依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
