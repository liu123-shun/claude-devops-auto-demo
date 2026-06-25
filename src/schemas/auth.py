"""
登录鉴权 Pydantic 校验模型
==========================
"""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求体"""
    username: str = Field(..., min_length=1, max_length=64, description="登录账号")
    password: str = Field(..., min_length=1, max_length=128, description="登录密码")
    role: str = Field(..., pattern="^(admin|student)$", description="登录角色: admin / student")
    captcha_token: Optional[str] = Field(None, description="验证码Token")
    captcha_code: Optional[str] = Field(None, max_length=8, description="验证码输入")


class RegisterRequest(BaseModel):
    """注册请求体"""
    username: str = Field(..., min_length=2, max_length=64, description="登录账号")
    password: str = Field(..., min_length=4, max_length=128, description="登录密码")
    name: str = Field(..., min_length=1, max_length=64, description="真实姓名")
    phone: Optional[str] = Field(None, max_length=32, description="手机号")
    class_name: Optional[str] = Field(None, max_length=64, description="班级")
    captcha_token: Optional[str] = Field(None, description="验证码Token")
    captcha_code: Optional[str] = Field(None, max_length=8, description="验证码输入")


class LoginResponse(BaseModel):
    """登录/注册成功返回体"""
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
