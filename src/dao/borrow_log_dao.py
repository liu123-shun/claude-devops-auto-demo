"""
借阅操作日志数据访问层
=====================
"""

from typing import Optional
from sqlalchemy.orm import Session

from ..db.models import BorrowOperationLog


def list_borrow_logs(
    db: Session,
    operate_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> tuple:
    """分页查询借阅操作日志"""
    q = db.query(BorrowOperationLog)
    if operate_type:
        q = q.filter(BorrowOperationLog.operate_type == operate_type)
    total = q.count()
    logs = q.order_by(BorrowOperationLog.id.desc()).offset(skip).limit(limit).all()
    return logs, total
