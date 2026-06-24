"""
借阅业务逻辑层
=============
- 借书：校验库存，创建借阅记录
- 还书：更新归还时间，触发库存变更
- 逾期统计
"""

from typing import Optional
from sqlalchemy.orm import Session

from ..db.models import BorrowRecord, Book
from ..dao import borrow_dao, book_dao


def borrow_book(db: Session, book_id: int, reader_id: int) -> Optional[BorrowRecord]:
    """
    借书操作：
    1. 校验图书是否存在且库存 > 0
    2. 创建借阅记录（触发器自动扣库存+写日志）
    """
    book = book_dao.get_book_by_id(db, book_id)
    if not book:
        raise ValueError("图书不存在")
    if book.stock <= 0:
        raise ValueError("图书库存不足，无法借阅")

    record = BorrowRecord(
        book_id=book_id,
        reader_id=reader_id,
        status="borrowed",
    )
    return borrow_dao.create_borrow(db, record)


def return_book(db: Session, borrow_id: int) -> Optional[BorrowRecord]:
    """
    还书操作：
    1. 查询借阅记录
    2. 更新归还时间和状态（触发器自动加库存+写日志）
    """
    record = borrow_dao.get_borrow_by_id(db, borrow_id)
    if not record:
        raise ValueError("借阅记录不存在")
    if record.return_time is not None:
        raise ValueError("该记录已归还，请勿重复操作")

    return borrow_dao.return_book(db, record)


def get_borrow_records(
    db: Session,
    reader_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """分页查询借阅记录"""
    skip = (page - 1) * page_size
    records, total = borrow_dao.list_borrows(db, reader_id, status, skip, page_size)

    # 补充图书名和读者名
    items = []
    for r in records:
        book = book_dao.get_book_by_id(db, r.book_id)
        from ..dao.reader_dao import get_reader_by_id
        reader = get_reader_by_id(db, r.reader_id)
        items.append({
            "id": r.id,
            "book_id": r.book_id,
            "reader_id": r.reader_id,
            "borrow_time": r.borrow_time,
            "return_time": r.return_time,
            "status": r.status,
            "book_name": book.book_name if book else None,
            "student_name": reader.student_name if reader else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


def get_overdue_borrows(db: Session, overdue_days: int = 30) -> list:
    """获取逾期借阅列表"""
    records = borrow_dao.list_overdue_borrows(db, overdue_days)
    items = []
    for r in records:
        book = book_dao.get_book_by_id(db, r.book_id)
        from ..dao.reader_dao import get_reader_by_id
        reader = get_reader_by_id(db, r.reader_id)
        items.append({
            "id": r.id,
            "book_id": r.book_id,
            "reader_id": r.reader_id,
            "borrow_time": r.borrow_time,
            "return_time": r.return_time,
            "status": "overdue",
            "book_name": book.book_name if book else None,
            "student_name": reader.student_name if reader else None,
        })
    return items


def get_dashboard_stats(db: Session) -> dict:
    """获取管理端看板统计数据"""
    from ..dao.login_log_dao import count_today_logins
    total_books = db.query(Book).count()
    active_borrows = borrow_dao.count_active_borrows(db)
    overdue_count = len(borrow_dao.list_overdue_borrows(db))
    today_logins = count_today_logins(db)
    return {
        "total_books": total_books,
        "active_borrows": active_borrows,
        "overdue_count": overdue_count,
        "today_logins": today_logins,
    }
