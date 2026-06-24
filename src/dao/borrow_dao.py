"""
借阅数据访问层
=============
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..db.models import BorrowRecord, Book, Reader


def create_borrow(db: Session, record: BorrowRecord) -> BorrowRecord:
    """新增借阅记录"""
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_borrow_by_id(db: Session, borrow_id: int) -> Optional[BorrowRecord]:
    """按ID查询借阅记录"""
    return db.query(BorrowRecord).filter(BorrowRecord.id == borrow_id).first()


def return_book(db: Session, record: BorrowRecord) -> BorrowRecord:
    """归还图书：更新 return_time + status"""
    record.return_time = datetime.now()
    record.status = "returned"
    db.commit()
    db.refresh(record)
    return record


def list_borrows(
    db: Session,
    reader_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> tuple:
    """分页查询借阅记录，支持按读者/状态筛选"""
    q = db.query(BorrowRecord)
    if reader_id:
        q = q.filter(BorrowRecord.reader_id == reader_id)
    if status:
        q = q.filter(BorrowRecord.status == status)
    total = q.count()
    records = (
        q.order_by(BorrowRecord.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records, total


def list_overdue_borrows(db: Session, overdue_days: int = 30) -> list:
    """查询逾期借阅（借出超过 N 天未归还）"""
    from datetime import timedelta
    threshold = datetime.now() - timedelta(days=overdue_days)
    return (
        db.query(BorrowRecord)
        .filter(
            and_(
                BorrowRecord.return_time.is_(None),
                BorrowRecord.borrow_time < threshold,
            )
        )
        .order_by(BorrowRecord.borrow_time.asc())
        .all()
    )


def count_active_borrows(db: Session) -> int:
    """统计在借数量"""
    return (
        db.query(BorrowRecord)
        .filter(BorrowRecord.return_time.is_(None))
        .count()
    )
