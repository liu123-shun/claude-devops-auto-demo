"""
鉴权业务逻辑层
=============
- JWT 签发与验证
- 密码加密存储（bcrypt）
- 角色校验
- 登录日志写入
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

from ..config.settings import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES
from ..db.models import SysUser
from ..dao import auth_dao, login_log_dao

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """将明文密码加密为 bcrypt 哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(user_id: int, username: str, role: str) -> str:
    """签发 JWT Token"""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Optional[dict]:
    """解析 JWT Token，失败返回 None"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def authenticate(
    db: Session,
    username: str,
    password: str,
    role: str,
    login_ip: Optional[str] = None,
) -> Optional[dict]:
    """
    登录鉴权：
    1. 按用户名+角色查询账号
    2. 验证密码
    3. 写入登录日志
    4. 返回 JWT Token + 用户信息
    """
    user = auth_dao.get_user_by_username_and_role(db, username, role)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None

    # 写入登录日志
    login_log_dao.create_login_log(db, user.id, login_ip, user.role)

    token = create_jwt_token(user.id, user.username, user.role)
    return {
        "token": token,
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "name": user.name,
    }


def create_default_admin(db: Session) -> None:
    """程序启动时自动创建默认管理员账号 admin / 123456"""
    existing = auth_dao.get_user_by_username(db, "admin")
    if existing:
        return
    admin = SysUser(
        username="admin",
        password=hash_password("123456"),
        role="admin",
        name="系统管理员",
        phone="",
    )
    auth_dao.create_user(db, admin)
    print("[OK] 默认管理员账号已创建: admin / 123456")
