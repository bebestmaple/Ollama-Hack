from app.crud import crud_user
from app.db.database import SessionLocal


# 检查并创建初始管理员账户
def create_initial_admin_if_needed():
    db = SessionLocal()
    try:
        if crud_user.is_user_table_empty(db):
            username, password = crud_user.create_initial_admin(db)
            print("\n" + "=" * 60)
            print("初始管理员账户已创建：")
            print(f"用户名: {username}")
            print(f"密码: {password}")
            print("请登录后立即修改密码！")
            print("=" * 60 + "\n")
    finally:
        db.close()
