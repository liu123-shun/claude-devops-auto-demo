"""
全局配置模块
===========
统一管理 JWT 密钥、数据库地址、过期时间、分页配置。
所有敏感信息通过环境变量注入，提供合理默认值。
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---- 数据库 -----------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:123456@host.docker.internal:3306/library_manage?charset=utf8mb4",
)

# ---- JWT --------------------------------------------------------------
SECRET_KEY: str = os.getenv("SECRET_KEY", "library-manage-secret-key-2024-jwt")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_MINUTES: int = 120

# ---- 分页 --------------------------------------------------------------
PAGE_SIZE: int = 10

# ---- 逾期阈值 (天) -----------------------------------------------------
OVERDUE_DAYS: int = 30

# ---- 管理员默认账号 ----------------------------------------------------
DEFAULT_ADMIN_USERNAME: str = "admin"
DEFAULT_ADMIN_PASSWORD: str = "123456"
