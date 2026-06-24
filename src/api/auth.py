"""
登录鉴权接口
===========
- POST /api/auth/login
- POST /api/auth/logout
- GET  /api/auth/me
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schemas.auth import LoginRequest, LoginResponse
from ..service import auth_service
from ..common.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["鉴权"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    用户登录（管理员/学生双角色）。
    校验账号密码，成功返回 JWT Token。
    """
    client_ip = request.client.host if request.client else None
    result = auth_service.authenticate(
        db, body.username, body.password, body.role, client_ip
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误，或角色不匹配",
        )
    return LoginResponse(**result)


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """
    退出登录（前端清除 Token，后端记录可扩展）。
    """
    return {"message": "退出成功"}


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user
