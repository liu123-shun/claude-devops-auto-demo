"""
学生专属接口
===========
- 查看自身信息
- 查看自己的借阅记录
- 查看可借图书列表
- 借书操作（仅限给自己借）
- 查看自己的登录日志
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schemas.borrow import BorrowCreate, BorrowResponse
from ..service import borrow_service
from ..dao import login_log_dao, reader_dao, book_dao
from ..common.dependencies import require_student, get_current_user
from ..config.settings import PAGE_SIZE

router = APIRouter(prefix="/api/student", tags=["学生"])


def _get_student_reader_id(db: Session, user_id: int) -> int:
    """通过 sys_user.id 获取对应 reader.id"""
    reader = reader_dao.get_reader_by_user_id(db, user_id)
    if not reader:
        return 0
    return reader.id


# ==================== 个人信息 ====================

@router.get("/profile")
def my_profile(
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """查看当前学生个人信息"""
    user_id = current_user["user_id"]
    reader = reader_dao.get_reader_by_user_id(db, user_id)
    return {
        "user_id": user_id,
        "username": current_user["username"],
        "role": current_user["role"],
        "reader": {
            "id": reader.id if reader else None,
            "student_name": reader.student_name if reader else None,
            "class": reader.class_ if reader else None,
            "phone": reader.phone if reader else None,
        },
    }


@router.get("/dashboard")
def student_dashboard(
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """学生首页看板数据"""
    reader_id = _get_student_reader_id(db, current_user["user_id"])
    active_borrows = 0
    total_borrows = 0
    if reader_id:
        from ..db.models import BorrowRecord
        active_borrows = (
            db.query(BorrowRecord)
            .filter(BorrowRecord.reader_id == reader_id, BorrowRecord.return_time.is_(None))
            .count()
        )
        total_borrows = (
            db.query(BorrowRecord)
            .filter(BorrowRecord.reader_id == reader_id)
            .count()
        )
    return {
        "active_borrows": active_borrows,
        "total_borrows": total_borrows,
    }


# ==================== 可借图书列表 ====================

@router.get("/books")
def list_available_books(
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """获取所有库存 > 0 的图书列表（供学生借书下拉选择）"""
    books, _ = book_dao.list_books(db, keyword=None, category=None, skip=0, limit=1000)
    result = []
    for b in books:
        result.append({
            "id": b.id,
            "book_name": b.book_name,
            "author": b.author,
            "category": b.category,
            "stock": b.stock,
        })
    return {"items": result}


# ==================== 我的借阅 ====================

@router.get("/borrows")
def my_borrows(
    current_user: dict = Depends(require_student),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """仅查看当前学生的借阅记录"""
    reader_id = _get_student_reader_id(db, current_user["user_id"])
    if reader_id == 0:
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    return borrow_service.get_borrow_records(db, reader_id=reader_id, page=page, page_size=page_size)


@router.post("/borrows", status_code=status.HTTP_201_CREATED)
def student_borrow_book(
    body: BorrowCreate,
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    学生给自己借书。
    自动从当前登录学生 token 解析 reader_id，仅允许给自己借。
    """
    user_id = current_user["user_id"]
    reader_id = _get_student_reader_id(db, user_id)
    if reader_id == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前学生尚未绑定读者信息，请联系管理员",
        )
    # 仅允许给自己借，不允许代借
    if body.reader_id and body.reader_id != reader_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="学生只能给自己借书，不能代他人借阅",
        )

    record = borrow_service.borrow_book(db, body.book_id, reader_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="借书失败")

    # 补全图书名返回
    book = book_dao.get_book_by_id(db, record.book_id)
    return {
        "id": record.id,
        "book_id": record.book_id,
        "reader_id": record.reader_id,
        "borrow_time": record.borrow_time.isoformat() if record.borrow_time else None,
        "status": record.status,
        "book_name": book.book_name if book else None,
    }


# ==================== 我的登录日志 ====================

@router.get("/login-logs")
def my_login_logs(
    current_user: dict = Depends(require_student),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """仅查看当前学生的登录日志"""
    user_id = current_user["user_id"]
    logs, total = login_log_dao.list_login_logs(db, user_id=user_id, skip=(page - 1) * page_size, limit=page_size)
    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "login_ip": log.login_ip,
            "login_time": log.login_time.isoformat() if log.login_time else None,
            "logout_time": log.logout_time.isoformat() if log.logout_time else None,
            "login_role": log.login_role,
        })
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }
