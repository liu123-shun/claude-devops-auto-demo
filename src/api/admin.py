"""
管理员专属接口
=============
- 图书管理 CRUD
- 学生管理 CRUD
- 全局借阅记录查询
- 全局登录日志
- 全局借阅操作日志
- 逾期统计
- 数据看板
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schemas.book import BookCreate, BookUpdate, BookResponse
from ..schemas.reader import ReaderCreate, ReaderUpdate, ReaderResponse
from ..schemas.borrow import BorrowCreate, BorrowResponse
from ..schemas.log import LoginLogResponse, BorrowOperationLogResponse
from ..service import book_service, reader_service, borrow_service
from ..dao import login_log_dao, borrow_log_dao, book_dao, reader_dao, borrow_dao
from ..common.dependencies import require_admin
from ..config.settings import PAGE_SIZE

router = APIRouter(prefix="/api/admin", tags=["管理员"], dependencies=[Depends(require_admin)])


# ==================== 数据看板 ====================

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """管理端数据看板统计"""
    return borrow_service.get_dashboard_stats(db)


# ==================== 图书管理 ====================

@router.get("/books")
def list_books(
    keyword: str = Query(None, description="搜索关键词"),
    category: str = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """分页查询图书列表"""
    return book_service.search_books(db, keyword, category, page, page_size)


@router.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(body: BookCreate, db: Session = Depends(get_db)):
    """新增图书"""
    return book_service.add_book(
        db, body.book_name, body.author, body.category, body.publish_time, body.stock
    )


@router.put("/books/{book_id}")
def update_book(book_id: int, body: BookUpdate, db: Session = Depends(get_db)):
    """更新图书"""
    book = book_service.update_book(db, book_id, body.model_dump(exclude_none=True))
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    return book


@router.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """删除图书"""
    if not book_service.remove_book(db, book_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    return {"message": "删除成功"}


# ==================== 学生管理 ====================

@router.get("/readers")
def list_readers(
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """分页查询学生读者"""
    return reader_service.search_readers(db, keyword, page, page_size)


@router.post("/readers", status_code=status.HTTP_201_CREATED)
def create_reader(body: ReaderCreate, db: Session = Depends(get_db)):
    """新增学生读者"""
    class_name = body.class_ if hasattr(body, 'class_') else None
    return reader_service.add_reader(
        db, body.student_name, class_name, body.phone, body.bind_user_id
    )


@router.put("/readers/{reader_id}")
def update_reader(reader_id: int, body: ReaderUpdate, db: Session = Depends(get_db)):
    """更新学生读者"""
    r = reader_service.update_reader(db, reader_id, body.model_dump(exclude_none=True))
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="读者不存在")
    return r


@router.delete("/readers/{reader_id}")
def delete_reader(reader_id: int, db: Session = Depends(get_db)):
    """删除学生读者"""
    if not reader_service.remove_reader(db, reader_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="读者不存在")
    return {"message": "删除成功"}


# ==================== 借阅管理 ====================

@router.get("/borrows")
def list_borrows(
    reader_id: int = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """全部借阅记录（管理员可查看所有学生）"""
    return borrow_service.get_borrow_records(db, reader_id, status, page, page_size)


@router.post("/borrows", status_code=status.HTTP_201_CREATED)
def create_borrow(body: BorrowCreate, db: Session = Depends(get_db)):
    """管理员代学生借书"""
    return borrow_service.borrow_book(db, body.book_id, body.reader_id)


@router.put("/borrows/{borrow_id}/return")
def return_book(borrow_id: int, db: Session = Depends(get_db)):
    """管理员处理还书"""
    record = borrow_service.return_book(db, borrow_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="借阅记录不存在")
    return record


@router.get("/overdue")
def overdue_books(db: Session = Depends(get_db)):
    """查询逾期图书"""
    return borrow_service.get_overdue_borrows(db)


# ==================== 日志查询 ====================

@router.get("/login-logs")
def list_login_logs(
    user_id: int = Query(None),
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """全局登录日志"""
    logs, total = login_log_dao.list_login_logs(db, user_id, keyword, (page - 1) * page_size, page_size)
    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "login_ip": log.login_ip,
            "login_time": log.login_time.isoformat() if log.login_time else None,
            "logout_time": log.logout_time.isoformat() if log.logout_time else None,
            "login_role": log.login_role,
            "username": log.user.username if log.user else None,
        })
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get("/borrow-logs")
def list_borrow_operation_logs(
    operate_type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """全局借阅操作日志"""
    logs, total = borrow_log_dao.list_borrow_logs(db, operate_type, (page - 1) * page_size, page_size)
    items = []
    for log in logs:
        record = borrow_dao.get_borrow_by_id(db, log.borrow_record_id)
        book_name = None
        student_name = None
        if record:
            book = book_dao.get_book_by_id(db, record.book_id)
            reader = reader_dao.get_reader_by_id(db, record.reader_id)
            book_name = book.book_name if book else None
            student_name = reader.student_name if reader else None
        items.append({
            "id": log.id,
            "borrow_record_id": log.borrow_record_id,
            "operate_type": log.operate_type,
            "operate_time": log.operate_time.isoformat() if log.operate_time else None,
            "operate_user_id": log.operate_user_id,
            "book_name": book_name,
            "student_name": student_name,
        })
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }
