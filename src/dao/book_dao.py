"""
图书数据访问层
=============
"""

from typing import Optional
from sqlalchemy.orm import Session

from ..db.models import Book


def create_book(db: Session, book: Book) -> Book:
    """新增图书"""
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def get_book_by_id(db: Session, book_id: int) -> Optional[Book]:
    """按ID查询图书"""
    return db.query(Book).filter(Book.id == book_id).first()


def list_books(
    db: Session,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> tuple:
    """分页查询图书列表，支持关键词搜索与分类筛选"""
    q = db.query(Book)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (Book.book_name.like(like)) | (Book.author.like(like))
        )
    if category:
        q = q.filter(Book.category == category)
    total = q.count()
    books = q.order_by(Book.id.desc()).offset(skip).limit(limit).all()
    return books, total


def update_book(db: Session, book: Book, updates: dict) -> Book:
    """更新图书"""
    for key, value in updates.items():
        if value is not None:
            setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: Book) -> None:
    """删除图书"""
    db.delete(book)
    db.commit()
