"""
登录日志数据访问层
=================
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from ..db.models import LoginLog, SysUser


def create_login_log(
    db: Session,
    user_id: int,
    login_ip: Optional[str] = None,
    login_role: Optional[str] = None,
) -> LoginLog:
    """写入登录日志"""
    log = LoginLog(
        user_id=user_id,
        login_ip=login_ip,
        login_time=datetime.now(),
        login_role=login_role,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_logout_time(db: Session, log: LoginLog) -> LoginLog:
    """更新退出时间"""
    log.logout_time = datetime.now()
    db.commit()
    db.refresh(log)
    return log


def list_login_logs(
    db: Session,
    user_id: Optional[int] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> tuple:
    """分页查询登录日志"""
    q = db.query(LoginLog)
    if user_id:
        q = q.filter(LoginLog.user_id == user_id)
    if keyword:
        # 关联 sys_user 表按用户名搜索
        q = q.join(SysUser).filter(SysUser.username.like(f"%{keyword}%"))
    total = q.count()
    logs = q.order_by(LoginLog.id.desc()).offset(skip).limit(limit).all()
    return logs, total


def count_today_logins(db: Session) -> int:
    """统计今日登录人数"""
    from sqlalchemy import func
    today = datetime.now().date()
    return (
        db.query(func.count(func.distinct(LoginLog.user_id)))
        .filter(func.date(LoginLog.login_time) == today)
        .scalar()
    ) or 0
