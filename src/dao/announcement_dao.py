"""
系统公告数据访问层
=================
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db.models import Announcement


def create_announcement(
    db: Session, title: str, content: str, publisher_id: int, is_pinned: int = 0
) -> Announcement:
    """发布公告"""
    a = Announcement(title=title, content=content, publisher_id=publisher_id, is_pinned=is_pinned)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def get_by_id(db: Session, a_id: int) -> Optional[Announcement]:
    """按ID查公告"""
    return db.query(Announcement).filter(Announcement.id == a_id).first()


def list_announcements(db: Session, skip: int = 0, limit: int = 20) -> tuple:
    """分页查询公告列表（置顶优先+时间倒序）"""
    q = db.query(Announcement)
    total = q.count()
    items = q.order_by(desc(Announcement.is_pinned), desc(Announcement.id)).offset(skip).limit(limit).all()
    return items, total


def list_latest(db: Session, limit: int = 5) -> list:
    """获取最新N条公告（供首页展示）"""
    return (
        db.query(Announcement)
        .order_by(desc(Announcement.is_pinned), desc(Announcement.id))
        .limit(limit)
        .all()
    )


def update_announcement(db: Session, a: Announcement, updates: dict) -> Announcement:
    """更新公告"""
    for k, v in updates.items():
        if v is not None:
            setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


def delete_announcement(db: Session, a: Announcement) -> None:
    """删除公告"""
    db.delete(a)
    db.commit()
