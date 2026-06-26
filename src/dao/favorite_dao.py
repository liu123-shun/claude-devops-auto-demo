"""收藏夹数据访问层"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..db.models import BookFavorite


def add_favorite(db: Session, user_id: int, book_id: int) -> BookFavorite:
    """添加收藏"""
    existing = db.query(BookFavorite).filter(
        BookFavorite.user_id == user_id, BookFavorite.book_id == book_id
    ).first()
    if existing:
        return existing
    f = BookFavorite(user_id=user_id, book_id=book_id)
    db.add(f); db.commit(); db.refresh(f)
    return f


def remove_favorite(db: Session, user_id: int, book_id: int) -> bool:
    """取消收藏"""
    f = db.query(BookFavorite).filter(
        BookFavorite.user_id == user_id, BookFavorite.book_id == book_id
    ).first()
    if not f:
        return False
    db.delete(f); db.commit()
    return True


def remove_favorite_by_id(db: Session, favorite_id: int) -> bool:
    """按ID删除收藏"""
    f = db.query(BookFavorite).filter(BookFavorite.id == favorite_id).first()
    if not f:
        return False
    db.delete(f); db.commit()
    return True


def is_favorited(db: Session, user_id: int, book_id: int) -> bool:
    """检查是否已收藏"""
    return db.query(BookFavorite).filter(
        BookFavorite.user_id == user_id, BookFavorite.book_id == book_id
    ).first() is not None


def get_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> tuple:
    """分页获取用户收藏列表"""
    q = db.query(BookFavorite).filter(BookFavorite.user_id == user_id)
    total = q.count()
    items = q.order_by(desc(BookFavorite.id)).offset(skip).limit(limit).all()
    return items, total


def get_user_favorite_ids(db: Session, user_id: int) -> set:
    """获取用户收藏的所有图书ID集合"""
    rows = db.query(BookFavorite.book_id).filter(BookFavorite.user_id == user_id).all()
    return {r[0] for r in rows}
