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
    1. after_borrow_insert    — 借阅时日志 + 库存 -1
    2. after_borrow_update_return — 归还时日志 + 库存 +1

    注意：每句 SQL 独立提交，避免 ; 分割破坏 BEGIN...END 块。
    """

    drop_statements = [
        "DROP TRIGGER IF EXISTS after_borrow_insert",
        "DROP TRIGGER IF EXISTS after_borrow_update_return",
    ]

    trigger_borrow_insert = """
    CREATE TRIGGER after_borrow_insert
        AFTER INSERT ON borrow_record
        FOR EACH ROW
    BEGIN
        INSERT INTO borrow_operation_log
            (borrow_record_id, operate_type, operate_time, operate_user_id)
        VALUES (NEW.id, 'borrow', NOW(), NEW.reader_id);
        UPDATE book SET stock = stock - 1 WHERE id = NEW.book_id;
    END
    """

    trigger_borrow_return = """
    CREATE TRIGGER after_borrow_update_return
        AFTER UPDATE ON borrow_record
        FOR EACH ROW
    BEGIN
        IF NEW.return_time IS NOT NULL AND OLD.return_time IS NULL THEN
            INSERT INTO borrow_operation_log
                (borrow_record_id, operate_type, operate_time, operate_user_id)
            VALUES (NEW.id, 'return', NOW(), NEW.reader_id);
            UPDATE book SET stock = stock + 1 WHERE id = NEW.book_id;
        END IF;
    END
    """

    create_statements = [trigger_borrow_insert, trigger_borrow_return]

    with engine.connect() as conn:
        for stmt in drop_statements + create_statements:
            try:
                conn.execute(text(stmt))
            except OperationalError as exc:
                msg = str(exc)
                if "already exists" not in msg.lower():
                    print(f"[WARN] 触发器执行警告: {exc}")
        conn.commit()
    print("[OK] 数据库触发器初始化完成")
