"""
JWT 鉴权依赖 & 角色拦截器
==========================
提供 FastAPI Depends 注入函数，用于：
- get_current_user: 从 Authorization Header 解析 JWT
- require_admin:  仅允许管理员访问
- require_student: 仅允许学生访问
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..service.auth_service import decode_jwt_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """
    从请求头解析 JWT Token，返回当前登录用户信息。
    未登录或 Token 无效返回 401。
    """
    token = credentials.credentials
    payload = decode_jwt_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "user_id": payload.get("user_id"),
        "username": payload.get("username"),
        "role": payload.get("role"),
    }


def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    仅允许管理员角色访问。
    非管理员返回 403。
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限：仅管理员可访问此接口",
        )
    return current_user


def require_student(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    仅允许学生角色访问。
    非学生返回 403。
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限：仅学生可访问此接口",
        )
    return current_user
