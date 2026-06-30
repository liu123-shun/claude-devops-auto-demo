"""
FastAPI 图书借阅管理系统入口
============================
- 挂载全部 API 路由
- 托管前端静态页面
- 启动时自动创建数据表、触发器和默认管理员账号
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .db.database import engine, init_triggers
from .db.models import Base
from .api.auth import router as auth_router
from .api.admin import router as admin_router
from .api.student import router as student_router
from .common.exception import register_exception_handlers

# ---- 前端静态文件目录 --------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


def _migrate_schema(engine):
    """自动追加新增字段，避免旧数据库缺少列导致报错。"""
    from sqlalchemy import text, exc as sa_exc
    migrations = [
        "ALTER TABLE book ADD COLUMN isbn VARCHAR(32) NULL COMMENT 'ISBN编号'",
        "ALTER TABLE book ADD COLUMN publisher VARCHAR(64) NULL COMMENT '出版社'",
        "ALTER TABLE book ADD COLUMN description TEXT NULL COMMENT '图书简介'",
        "ALTER TABLE book ADD COLUMN cover_url VARCHAR(512) NULL COMMENT '封面图片URL'",
        "ALTER TABLE book MODIFY COLUMN cover_url VARCHAR(4096)",  # 扩容支持长URL
        "ALTER TABLE book ADD COLUMN total_borrows INT NOT NULL DEFAULT 0 COMMENT '累计借阅次数'",
    ]
    # 新表在 create_all 时自动创建，无需手动 migrate
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
            except sa_exc.OperationalError:
                pass  # 字段已存在则跳过
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库"""
    # 创建全部数据表 & 自动迁移新字段
    Base.metadata.create_all(bind=engine)
    _migrate_schema(engine)
    print("[OK] 数据库表创建/迁移完成")

    # 创建触发器
    init_triggers()

    # 创建默认管理员账号
    from .db.database import SessionLocal
    from .service.auth_service import create_default_admin
    from .dao.config_dao import init_defaults
    db = SessionLocal()
    try:
        create_default_admin(db)
        init_defaults(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="图书借阅管理系统",
    version="2.0.0",
    description="分角色图书借阅管理系统 — FastAPI + MySQL + JWT",
    lifespan=lifespan,
)

# ---- CORS 中间件 -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 注册异常处理器 ----------------------------------------------------
register_exception_handlers(app)

# ---- 挂载 API 路由 -----------------------------------------------------
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(student_router)


# ---- 托管前端静态页面 ---------------------------------------------------
@app.get("/")
@app.get("/login.html")
@app.get("/pages/{page}")
async def serve_frontend(page: str = "login.html"):
    """重定向到前端页面"""
    from fastapi.responses import FileResponse
    path = os.path.join(FRONTEND_DIR, page)
    if os.path.isfile(path):
        return FileResponse(path)
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


# 挂载前端静态资源（CSS/JS）
if os.path.isdir(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")
