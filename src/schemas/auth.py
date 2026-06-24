"""
登录鉴权 Pydantic 校验模型
==========================
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求体"""
    username: str = Field(..., min_length=1, max_length=64, description="登录账号")
    password: str = Field(..., min_length=1, max_length=128, description="登录密码")
    role: str = Field(..., pattern="^(admin|student)$", description="登录角色: admin / student")


class LoginResponse(BaseModel):
    """登录成功返回体"""
    token: str = Field(..., description="JWT Token")
    user_id: int
    username: str
    role: str
    name: str


class TokenPayload(BaseModel):
    """JWT Token 解析后的载荷"""
    user_id: int
    username: str
    role: str
