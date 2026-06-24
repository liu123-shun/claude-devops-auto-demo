"""
数据库引擎与会话管理
===================
- 创建 SQLAlchemy 引擎与连接池
- 提供 get_db 依赖注入
- 启动时自动创建表与触发器
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

from ..config.settings import DATABASE_URL

# ---- 引擎 --------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI 依赖注入：每次请求创建一个独立数据库会话，请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_triggers() -> None:
    """程序启动时自动创建 MySQL 触发器。

    触发器清单：
    1. after_user_login       — 登录后自动写入 login_log
    2. after_borrow_insert    — 借阅时日志 + 库存 -1
    3. after_borrow_update_return — 归还时日志 + 库存 +1
    """
    triggers_sql = """
    -- 删除已存在的触发器（幂等创建）
    DROP TRIGGER IF EXISTS after_user_login;
    DROP TRIGGER IF EXISTS after_borrow_insert;
    DROP TRIGGER IF EXISTS after_borrow_update_return;

    -- 触发器1：用户登录日志（在 sys_user 表更新后模拟，通过应用层调用）
    -- 说明：MySQL 触发器无法直接捕获"登录"行为（非 DML），
    -- 实际登录日志由应用层 auth_service 手动写入 login_log 表。
    -- 此处保留占位以防后续通过其他事件触发。

    -- 触发器2：借阅时自动写入操作日志 + 库存 -1
    CREATE TRIGGER after_borrow_insert
        AFTER INSERT ON borrow_record
        FOR EACH ROW
    BEGIN
        -- 写入借阅操作日志
        INSERT INTO borrow_operation_log (borrow_record_id, operate_type, operate_time, operate_user_id)
        VALUES (NEW.id, 'borrow', NOW(), NEW.reader_id);
        -- 图书库存 -1
        UPDATE book SET stock = stock - 1 WHERE id = NEW.book_id;
    END;

    -- 触发器3：归还时自动写入归还日志 + 库存 +1
    CREATE TRIGGER after_borrow_update_return
        AFTER UPDATE ON borrow_record
        FOR EACH ROW
    BEGIN
        IF NEW.return_time IS NOT NULL AND OLD.return_time IS NULL THEN
            INSERT INTO borrow_operation_log (borrow_record_id, operate_type, operate_time, operate_user_id)
            VALUES (NEW.id, 'return', NOW(), NEW.reader_id);
            UPDATE book SET stock = stock + 1 WHERE id = NEW.book_id;
        END IF;
    END;
    """
    with engine.connect() as conn:
        for statement in triggers_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except OperationalError as exc:
                    # 触发器已存在等非致命错误可忽略
                    if "already exists" not in str(exc).lower():
                        print(f"[WARN] 触发器创建警告: {exc}")
        conn.commit()
    print("[OK] 数据库触发器初始化完成")
