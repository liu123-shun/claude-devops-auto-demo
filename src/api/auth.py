"""
登录鉴权接口
===========
- POST /api/auth/login        — 登录（含验证码校验）
- POST /api/auth/logout       — 退出登录
- POST /api/auth/register     — 学生自助注册
- GET  /api/auth/captcha      — 获取图形验证码
- GET  /api/auth/me           — 当前用户信息
"""

import base64
import io
import random
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from jose import jwt

from ..db.database import get_db
from ..db.models import SysUser, Reader
from ..schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from ..service import auth_service
from ..dao import login_log_dao, auth_dao
from ..common.dependencies import get_current_user
from ..config.settings import SECRET_KEY, JWT_ALGORITHM

router = APIRouter(prefix="/api/auth", tags=["鉴权"])

# ---- 验证码工具 ----
_captcha_store: dict = {}  # token -> code (简单内存存储)

CAPTCHA_WIDTH, CAPTCHA_HEIGHT = 140, 50

def _make_captcha_image(code: str) -> str:
    """用纯色+干扰线生成验证码图片的 base64 data URI"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        # 无 PIL 时回退到纯文本
        return ""

    img = Image.new("RGB", (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), (245, 248, 252))
    draw = ImageDraw.Draw(img)

    # 干扰线
    for _ in range(6):
        x1 = random.randint(0, CAPTCHA_WIDTH)
        y1 = random.randint(0, CAPTCHA_HEIGHT)
        x2 = random.randint(0, CAPTCHA_WIDTH)
        y2 = random.randint(0, CAPTCHA_HEIGHT)
        draw.line([(x1, y1), (x2, y2)], fill=(200, 210, 225), width=2)

    # 干扰点
    for _ in range(40):
        x = random.randint(0, CAPTCHA_WIDTH - 1)
        y = random.randint(0, CAPTCHA_HEIGHT - 1)
        draw.point((x, y), fill=(180, 190, 210))

    # 文字（模拟手写体）
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()

    colors = [(74, 144, 217), (231, 76, 60), (39, 174, 96), (155, 89, 182)]
    for i, ch in enumerate(code):
        x = 15 + i * 30 + random.randint(-4, 4)
        y = random.randint(5, 15)
        draw.text((x, y), ch, fill=random.choice(colors), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@router.get("/captcha")
def get_captcha():
    """生成验证码图片，返回 captcha_token + 图片 base64"""
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    token = jwt.encode(
        {"code": code, "exp": datetime.utcnow() + timedelta(minutes=5)},
        SECRET_KEY, algorithm=JWT_ALGORITHM,
    )
    img_data = _make_captcha_image(code) or ""
    return {"captcha_token": token, "image": img_data, "code_hint": code}


def _verify_captcha(token: str, user_input: str) -> bool:
    """校验验证码"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        stored = payload.get("code", "")
        return stored.upper() == user_input.upper().strip()
    except Exception:
        return False


# ---- 登录 ----

@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    用户登录（管理员/学生双角色）。
    校验账号密码+验证码，成功返回 JWT Token。
    """
    # 验证码校验
    if not _verify_captcha(body.captcha_token or "", body.captcha_code or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

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


# ---- 注册 ----

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    学生自助注册：创建系统账号 + 绑定读者信息。
    用户名不可重复，自动分配 student 角色。
    """
    # 验证码校验
    if not _verify_captcha(body.captcha_token or "", body.captcha_code or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

    # 查重
    existing = auth_dao.get_user_by_username(db, body.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被占用，请换一个")

    # 创建账号
    user = SysUser(
        username=body.username.strip(),
        password=auth_service.hash_password(body.password),
        role="student",
        name=body.name.strip(),
        phone=body.phone.strip() if body.phone else None,
    )
    user = auth_dao.create_user(db, user)

    # 创建读者信息
    reader = Reader(
        student_name=body.name.strip(),
        class_=body.class_name.strip() if body.class_name else None,
        phone=body.phone.strip() if body.phone else None,
        bind_user_id=user.id,
    )
    db.add(reader)
    db.commit()

    # 自动签发 Token
    token = auth_service.create_jwt_token(user.id, user.username, user.role)
    return LoginResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        role=user.role,
        name=user.name,
    )


# ---- 退出 ----

@router.post("/logout")
def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """退出登录，更新 login_log 登出时间"""
    user_id = current_user.get("user_id")
    if user_id:
        updated = login_log_dao.update_logout_time(db, int(user_id))
        if updated:
            return {"message": "退出成功", "logout_time": updated.logout_time.isoformat()}
    return {"message": "退出成功"}


# ---- 当前用户 ----

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user
