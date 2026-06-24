"""
图书业务逻辑层
=============
"""

from typing import Optional
from sqlalchemy.orm import Session

from ..db.models import Book
from ..dao import book_dao


def add_book(
    db: Session,
    book_name: str,
    author: str,
    category: Optional[str] = None,
    publish_time=None,
    stock: int = 0,
) -> Book:
    """新增图书"""
    book = Book(
        book_name=book_name,
        author=author,
        category=category,
        publish_time=publish_time,
        stock=stock,
    )
    return book_dao.create_book(db, book)


def get_book(db: Session, book_id: int) -> Optional[Book]:
    """查询单本图书"""
    return book_dao.get_book_by_id(db, book_id)


def search_books(
    db: Session,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """分页搜索图书"""
    skip = (page - 1) * page_size
    books, total = book_dao.list_books(db, keyword, category, skip, page_size)
    return {
        "items": books,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


def update_book(db: Session, book_id: int, updates: dict) -> Optional[Book]:
    """更新图书"""
    book = book_dao.get_book_by_id(db, book_id)
    if not book:
        return None
    return book_dao.update_book(db, book, updates)


def remove_book(db: Session, book_id: int) -> bool:
    """删除图书"""
    book = book_dao.get_book_by_id(db, book_id)
    if not book:
        return False
    book_dao.delete_book(db, book)
    return True
