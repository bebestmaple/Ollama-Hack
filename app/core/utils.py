from app.core.logging import get_logger
from app.crud import crud_user
from app.db.database import SessionLocal

logger = get_logger(__name__)


# 检查并创建初始管理员账户
def create_initial_admin_if_needed():
    db = SessionLocal()
    try:
        if crud_user.is_user_table_empty(db):
            username, password = crud_user.create_initial_admin(db)
            logger.warning("\n" + "=" * 60)
            logger.warning("初始管理员账户已创建：")
            logger.warning(f"用户名: {username}")
            logger.warning(f"密码: {password}")
            logger.warning("请登录后立即修改密码！")
            logger.warning("=" * 60 + "\n")
    finally:
        db.close()
