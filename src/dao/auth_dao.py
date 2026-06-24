"""
系统账号数据访问层
=================
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..db.models import SysUser


def get_user_by_username(db: Session, username: str) -> Optional[SysUser]:
    """按用户名查询账号"""
    return db.query(SysUser).filter(SysUser.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[SysUser]:
    """按ID查询账号"""
    return db.query(SysUser).filter(SysUser.id == user_id).first()


def get_user_by_username_and_role(
    db: Session, username: str, role: str
) -> Optional[SysUser]:
    """按用户名+角色查询账号"""
    return db.query(SysUser).filter(
        and_(SysUser.username == username, SysUser.role == role)
    ).first()


def create_user(db: Session, user: SysUser) -> SysUser:
    """新增账号"""
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users_by_role(db: Session, role: str) -> list:
    """按角色查询账号列表"""
    return db.query(SysUser).filter(SysUser.role == role).all()


def list_all_users(db: Session) -> list:
    """查询全部账号"""
    return db.query(SysUser).all()
