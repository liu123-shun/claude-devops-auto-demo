"""
学生专属接口
===========
- 个人资料查看与修改
- 密码修改
- 增强看板（公告、热门图书）
- 图书浏览与搜索
- 借书/还书
- 借阅记录（状态筛选）
- 登录日志（时间筛选）
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.database import get_db
from ..db.models import Book, BorrowRecord
from ..schemas.borrow import BorrowCreate
from ..service import borrow_service, auth_service
from ..dao import login_log_dao, reader_dao, book_dao, borrow_dao
from ..dao.announcement_dao import list_latest
from ..common.dependencies import require_student
from ..config.settings import PAGE_SIZE

router = APIRouter(prefix="/api/student", tags=["学生"])


def _get_student_reader_id(db: Session, user_id: int) -> int:
    """通过 sys_user.id 获取对应 reader.id"""
    reader = reader_dao.get_reader_by_user_id(db, user_id)
    return reader.id if reader else 0


# ==================== 个人资料 ====================

@router.get("/profile")
def my_profile(
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """查看当前学生个人信息"""
    user_id = current_user["user_id"]
    reader = reader_dao.get_reader_by_user_id(db, user_id)
    from ..dao.auth_dao import get_user_by_id
    user = get_user_by_id(db, user_id)
    return {
        "user_id": user_id, "username": current_user["username"],
        "role": current_user["role"], "name": user.name if user else None,
        "reader": {
            "id": reader.id if reader else None,
            "student_name": reader.student_name if reader else None,
            "class": reader.class_ if reader else None,
            "phone": reader.phone if reader else None,
        },
    }


@router.put("/profile")
def update_my_profile(
    phone: str = Query(None, max_length=32),
    class_name: str = Query(None, max_length=64),
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """学生修改自己的手机号和班级"""
    reader = reader_dao.get_reader_by_user_id(db, current_user["user_id"])
    if not reader:
        raise HTTPException(status_code=400, detail="未绑定读者信息")
    if phone is not None:
        reader.phone = phone
    if class_name is not None:
        reader.class_ = class_name
    # 同步更新 sys_user.phone
    from ..dao.auth_dao import get_user_by_id
    user = get_user_by_id(db, current_user["user_id"])
    if user and phone is not None:
        user.phone = phone
    db.commit()
    return {"message": "资料更新成功"}


@router.put("/change-password")
def student_change_password(
    old_password: str = Query(..., min_length=1),
    new_password: str = Query(..., min_length=1, max_length=128),
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """学生修改自己的密码"""
    from ..dao.auth_dao import get_user_by_id
    user = get_user_by_id(db, current_user["user_id"])
    if not auth_service.verify_password(old_password, user.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password = auth_service.hash_password(new_password)
    db.commit()
    return {"message": "密码修改成功"}


# ==================== 看板 ====================

@router.get("/dashboard")
def student_dashboard(
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """学生首页增强看板"""
    reader_id = _get_student_reader_id(db, current_user["user_id"])
    active_borrows = 0
    total_borrows = 0
    overdue_count = 0
    if reader_id:
        active_borrows = db.query(BorrowRecord).filter(
            BorrowRecord.reader_id == reader_id, BorrowRecord.return_time.is_(None)
        ).count()
        total_borrows = db.query(BorrowRecord).filter(BorrowRecord.reader_id == reader_id).count()
        # 逾期数
        from datetime import datetime, timedelta
        threshold = datetime.now() - timedelta(days=30)
        overdue_count = db.query(BorrowRecord).filter(
            BorrowRecord.reader_id == reader_id, BorrowRecord.return_time.is_(None),
            BorrowRecord.borrow_time < threshold
        ).count()

    # 热门图书 Top 5
    hot_books = db.query(Book).order_by(Book.total_borrows.desc()).limit(5).all()
    hot_list = [{"id": b.id, "book_name": b.book_name, "author": b.author, "stock": b.stock, "total_borrows": b.total_borrows} for b in hot_books]

    # 最新公告 3条
    announcements = list_latest(db, 3)
    ann_list = [{"id": a.id, "title": a.title, "content": a.content[:200] + ("..." if len(a.content) > 200 else ""), "create_time": a.create_time.isoformat() if a.create_time else None} for a in announcements]

    # 图书总数
    total_books = db.query(Book).count()

    return {
        "active_borrows": active_borrows, "total_borrows": total_borrows,
        "overdue_count": overdue_count, "total_books": total_books,
        "hot_books": hot_list, "announcements": ann_list,
    }


# ==================== 公告详情 ====================

@router.get("/announcements/{a_id}")
def get_announcement(a_id: int, db: Session = Depends(get_db)):
    """查看单条公告详情"""
    from ..dao.announcement_dao import get_by_id
    a = get_by_id(db, a_id)
    if not a:
        raise HTTPException(status_code=404, detail="公告不存在")
    return {
        "id": a.id, "title": a.title, "content": a.content,
        "publisher_name": a.publisher.name if a.publisher else None,
        "create_time": a.create_time.isoformat() if a.create_time else None,
    }


# ==================== 图书浏览 ====================

@router.get("/books")
def list_available_books(
    keyword: str = Query(None),
    category: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """图书浏览（卡片式），分页+搜索+分类筛选"""
    skip = (page - 1) * page_size
    books, total = book_dao.list_books(db, keyword=keyword, category=category, skip=skip, limit=page_size)
    items = []
    for b in books:
        items.append({
            "id": b.id, "book_name": b.book_name, "author": b.author,
            "category": b.category, "isbn": b.isbn, "publisher": b.publisher,
            "description": b.description[:150] if b.description else None,
            "cover_url": b.cover_url, "stock": b.stock,
            "total_borrows": b.total_borrows,
            "publish_time": b.publish_time.isoformat() if b.publish_time else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0}


@router.get("/books/{book_id}")
def get_book_detail(book_id: int, db: Session = Depends(get_db)):
    """获取单本图书详情"""
    book = book_dao.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    return {
        "id": book.id, "book_name": book.book_name, "author": book.author,
        "category": book.category, "isbn": book.isbn, "publisher": book.publisher,
        "description": book.description, "cover_url": book.cover_url,
        "publish_time": book.publish_time.isoformat() if book.publish_time else None,
        "stock": book.stock, "total_borrows": book.total_borrows,
    }


# ==================== 分类 ====================

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """获取所有已有分类"""
    rows = db.query(Book.category, func.count(Book.id)).filter(
        Book.category.isnot(None), Book.category != ""
    ).group_by(Book.category).all()
    return [{"name": c, "count": n} for c, n in rows]


# ==================== 我的借阅 ====================

@router.get("/borrows")
def my_borrows(
    status: str = Query(None),
    current_user: dict = Depends(require_student),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """仅查看当前学生的借阅记录，支持按状态筛选"""
    reader_id = _get_student_reader_id(db, current_user["user_id"])
    if reader_id == 0:
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    return borrow_service.get_borrow_records(db, reader_id=reader_id, status=status, page=page, page_size=page_size)


@router.post("/borrows", status_code=status.HTTP_201_CREATED)
def student_borrow_book(
    body: BorrowCreate,
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """学生给自己借书"""
    user_id = current_user["user_id"]
    reader_id = _get_student_reader_id(db, user_id)
    if reader_id == 0:
        raise HTTPException(status_code=400, detail="当前学生尚未绑定读者信息")
    if body.reader_id and body.reader_id != reader_id:
        raise HTTPException(status_code=403, detail="学生只能给自己借书")

    record = borrow_service.borrow_book(db, body.book_id, reader_id)
    if not record:
        raise HTTPException(status_code=400, detail="借书失败")
    book = book_dao.get_book_by_id(db, record.book_id)
    return {
        "id": record.id, "book_id": record.book_id, "reader_id": record.reader_id,
        "borrow_time": record.borrow_time.isoformat() if record.borrow_time else None,
        "status": record.status, "book_name": book.book_name if book else None,
    }


@router.put("/borrows/{borrow_id}/return")
def student_return_book(
    borrow_id: int,
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """学生还书：仅允许归还自己的"""
    reader_id = _get_student_reader_id(db, current_user["user_id"])
    if reader_id == 0:
        raise HTTPException(status_code=400, detail="未绑定读者信息")
    record = borrow_dao.get_borrow_by_id(db, borrow_id)
    if not record:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    if record.reader_id != reader_id:
        raise HTTPException(status_code=403, detail="只能归还自己的借阅记录")
    updated = borrow_service.return_book(db, borrow_id)
    if not updated:
        raise HTTPException(status_code=400, detail="还书失败")
    return {
        "id": updated.id, "book_id": updated.book_id, "reader_id": updated.reader_id,
        "return_time": updated.return_time.isoformat() if updated.return_time else None,
        "status": updated.status,
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
            "id": log.id, "user_id": log.user_id, "login_ip": log.login_ip,
            "login_time": log.login_time.isoformat() if log.login_time else None,
            "logout_time": log.logout_time.isoformat() if log.logout_time else None,
            "login_role": log.login_role,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0}
