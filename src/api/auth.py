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
from ..dao import login_log_dao
from ..common.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["鉴权"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    用户登录（管理员/学生双角色）。
    校验账号密码，成功返回 JWT Token 并自动写入登录日志。
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
def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    退出登录：
    1. 更新 login_log 表中当前用户最新未登出记录的 logout_time
    2. 前端清除本地 Token
    """
    user_id = current_user.get("user_id")
    if user_id:
        updated = login_log_dao.update_logout_time(db, int(user_id))
        if updated:
            return {"message": "退出成功", "logout_time": updated.logout_time.isoformat()}
    return {"message": "退出成功"}


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user
