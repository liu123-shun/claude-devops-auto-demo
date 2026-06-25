"""
管理员专属接口
=============
- 数据看板（增强统计）
- 图书管理 CRUD + 热门图书
- 学生管理 CRUD
- 借阅管理
- 公告管理 CRUD
- 逾期统计（含罚金计算）
- 登录日志 / 借阅操作日志
"""

from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.database import get_db
from ..db.models import Book, BorrowRecord, Reader, SysUser, BorrowOperationLog, LoginLog
from ..schemas.book import BookCreate, BookUpdate
from ..schemas.reader import ReaderCreate, ReaderUpdate
from ..schemas.borrow import BorrowCreate
from ..schemas.announcement import AnnouncementCreate, AnnouncementUpdate
from ..service import book_service, reader_service, borrow_service, auth_service
from ..dao import login_log_dao, borrow_log_dao, book_dao, reader_dao, borrow_dao
from ..dao.announcement_dao import (
    create_announcement, get_by_id, list_announcements,
    update_announcement, delete_announcement,
)
from ..common.dependencies import require_admin
from ..config.settings import PAGE_SIZE, OVERDUE_DAYS

router = APIRouter(prefix="/api/admin", tags=["管理员"], dependencies=[Depends(require_admin)])


# ==================== 数据看板 ====================

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """管理端增强数据看板"""
    stats = borrow_service.get_dashboard_stats(db)

    # 学生总数
    stats["total_students"] = db.query(Reader).count()

    # 各分类图书数量
    cat_rows = db.query(Book.category, func.count(Book.id)).filter(Book.category.isnot(None)).group_by(Book.category).all()
    stats["category_stats"] = [{"category": c, "count": n} for c, n in cat_rows]

    # 热门图书 Top 6
    top_books = db.query(Book).order_by(Book.total_borrows.desc()).limit(6).all()
    stats["hot_books"] = [{"id": b.id, "book_name": b.book_name, "author": b.author, "total_borrows": b.total_borrows} for b in top_books]

    # 最近借阅 (5条)
    recent = db.query(BorrowRecord).order_by(BorrowRecord.id.desc()).limit(5).all()
    recent_items = []
    for r in recent:
        bk = book_dao.get_book_by_id(db, r.book_id)
        rd = reader_dao.get_reader_by_id(db, r.reader_id)
        recent_items.append({
            "id": r.id, "book_name": bk.book_name if bk else None,
            "student_name": rd.student_name if rd else None,
            "borrow_time": r.borrow_time.isoformat() if r.borrow_time else None,
            "status": r.status,
        })
    stats["recent_borrows"] = recent_items

    # 最近公告 (3条)
    from ..dao.announcement_dao import list_latest
    announcements = list_latest(db, 3)
    stats["announcements"] = [{"id": a.id, "title": a.title, "create_time": a.create_time.isoformat() if a.create_time else None} for a in announcements]

    return stats


# ==================== 数据可视化 ====================

@router.get("/charts/overview")
def charts_overview(db: Session = Depends(get_db)):
    """综合可视化数据：分类饼图、月度趋势、读者排行、逾期分布、借阅热度"""
    from datetime import datetime, timedelta
    now = datetime.now()

    # 1) 分类饼图
    cat_rows = db.query(Book.category, func.count(Book.id)).filter(Book.category.isnot(None), Book.category != "").group_by(Book.category).all()
    pie_labels = [c for c, _ in cat_rows]
    pie_data = [n for _, n in cat_rows]
    pie_colors = ["#4a90d9","#27ae60","#f39c12","#e74c3c","#9b59b6","#1abc9c","#e67e22","#3498db","#2ecc71","#f1c40f"]

    # 2) 月度借阅趋势（近12个月）
    monthly_labels = []; monthly_borrow = []; monthly_return = []
    for i in range(11, -1, -1):
        start = (now.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) if start.month == 12 else start.replace(month=start.month+1, day=1)
        monthly_labels.append(start.strftime("%Y-%m"))
        monthly_borrow.append(db.query(BorrowRecord).filter(
            BorrowRecord.borrow_time >= start, BorrowRecord.borrow_time < end).count())
        monthly_return.append(db.query(BorrowRecord).filter(
            BorrowRecord.return_time >= start, BorrowRecord.return_time < end).count())

    # 3) 读者借阅排行 Top 10
    reader_rows = db.query(Reader.student_name, func.count(BorrowRecord.id)).join(
        BorrowRecord, BorrowRecord.reader_id == Reader.id
    ).group_by(Reader.id).order_by(func.count(BorrowRecord.id).desc()).limit(10).all()
    reader_labels = [r[0] for r in reader_rows]
    reader_data = [r[1] for r in reader_rows]

    # 4) 库存分布直方图
    all_stocks = [s[0] for s in db.query(Book.stock).all()]
    bins = {"0":0,"1-2":0,"3-5":0,"6-10":0,"10+":0}
    for s in all_stocks:
        if s == 0: bins["0"]+=1
        elif s <= 2: bins["1-2"]+=1
        elif s <= 5: bins["3-5"]+=1
        elif s <= 10: bins["6-10"]+=1
        else: bins["10+"]+=1
    hist_labels = list(bins.keys())
    hist_data = list(bins.values())

    # 5) 每天借阅热力（近30天按星期分布）
    daily_labels = ["周一","周二","周三","周四","周五","周六","周日"]
    daily_borrows = [0]*7; daily_returns = [0]*7
    cutoff = now - timedelta(days=30)
    records = db.query(BorrowRecord).filter(BorrowRecord.borrow_time >= cutoff).all()
    for r in records:
        if r.borrow_time:
            daily_borrows[r.borrow_time.weekday()] += 1
        if r.return_time and r.return_time >= cutoff:
            daily_returns[r.return_time.weekday()] += 1

    # 6) 逾期天数分布
    threshold = now - timedelta(days=30)
    overdue_records = db.query(BorrowRecord).filter(
        BorrowRecord.return_time.is_(None), BorrowRecord.borrow_time < threshold).all()
    overdue_days_data = [max(0, (now - r.borrow_time).days - 30) for r in overdue_records]
    od_bins = {"30-40天":0,"41-50天":0,"51-60天":0,"60天+":0}
    for d in overdue_days_data:
        if d <= 40: od_bins["30-40天"]+=1
        elif d <= 50: od_bins["41-50天"]+=1
        elif d <= 60: od_bins["51-60天"]+=1
        else: od_bins["60天+"]+=1

    # 7) 出版社分布
    pub_rows = db.query(Book.publisher, func.count(Book.id)).filter(
        Book.publisher.isnot(None), Book.publisher != ""
    ).group_by(Book.publisher).order_by(func.count(Book.id).desc()).limit(8).all()

    # 8) 学生年级分布
    class_rows = db.query(Reader.class_, func.count(Reader.id)).filter(
        Reader.class_.isnot(None), Reader.class_ != ""
    ).group_by(Reader.class_).all()

    return {
        "pie": {"labels": pie_labels, "data": pie_data, "colors": pie_colors[:len(pie_labels)]},
        "monthly": {"labels": monthly_labels, "borrow": monthly_borrow, "return": monthly_return},
        "readers": {"labels": reader_labels, "data": reader_data},
        "histogram": {"labels": hist_labels, "data": hist_data},
        "daily": {"labels": daily_labels, "borrows": daily_borrows, "returns": daily_returns},
        "overdue_bins": {"labels": list(od_bins.keys()), "data": list(od_bins.values())},
        "publishers": {"labels": [p[0] or "未知" for p in pub_rows], "data": [p[1] for p in pub_rows]},
        "classes": {"labels": [c[0] or "未设置" for c in class_rows], "data": [c[1] for c in class_rows]},
    }


# ==================== 图书管理 ====================

@router.get("/books")
def list_books(
    keyword: str = Query(None),
    category: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """分页查询图书列表"""
    return book_service.search_books(db, keyword, category, page, page_size)


@router.get("/books/{book_id}")
def get_book_detail(book_id: int, db: Session = Depends(get_db)):
    """获取单本图书详情（含借阅历史）"""
    book = book_dao.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    # 最近借阅记录
    recent_records = db.query(BorrowRecord).filter(BorrowRecord.book_id == book_id).order_by(BorrowRecord.id.desc()).limit(10).all()
    records = []
    for r in recent_records:
        rd = reader_dao.get_reader_by_id(db, r.reader_id)
        records.append({
            "id": r.id, "student_name": rd.student_name if rd else None,
            "borrow_time": r.borrow_time.isoformat() if r.borrow_time else None,
            "return_time": r.return_time.isoformat() if r.return_time else None,
            "status": r.status,
        })
    return {
        "id": book.id, "book_name": book.book_name, "author": book.author,
        "category": book.category, "isbn": book.isbn, "publisher": book.publisher,
        "description": book.description, "cover_url": book.cover_url,
        "publish_time": book.publish_time.isoformat() if book.publish_time else None,
        "stock": book.stock, "total_borrows": book.total_borrows,
        "create_time": book.create_time.isoformat() if book.create_time else None,
        "recent_records": records,
    }


@router.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(body: BookCreate, db: Session = Depends(get_db)):
    """新增图书"""
    return book_service.add_book(
        db, body.book_name, body.author, body.category,
        body.isbn, body.publisher, body.description, body.cover_url,
        body.publish_time, body.stock,
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


# ==================== 分类 ====================

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """获取所有已有分类及数量"""
    rows = db.query(Book.category, func.count(Book.id)).filter(Book.category.isnot(None), Book.category != "").group_by(Book.category).all()
    return [{"name": c, "count": n} for c, n in rows]


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
    """新增学生读者（同时创建登录账号）"""
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
    """全部借阅记录"""
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
def overdue_books(
    keyword: str = Query(None),
    db: Session = Depends(get_db),
):
    """查询逾期图书（含罚金计算：每天1元）"""
    items = borrow_service.get_overdue_borrows(db)
    if keyword:
        kw = keyword.lower()
        items = [i for i in items if (i.get("book_name") and kw in i["book_name"].lower()) or (i.get("student_name") and kw in i["student_name"].lower())]
    now = datetime.now()
    for item in items:
        if item.get("borrow_time"):
            bt = datetime.fromisoformat(item["borrow_time"]) if isinstance(item["borrow_time"], str) else item["borrow_time"]
            overdue_days = max(0, (now - bt).days - OVERDUE_DAYS)
            item["overdue_days"] = overdue_days
            item["fine"] = overdue_days  # 每天1元
    return items


# ==================== 公告管理 ====================

@router.get("/announcements")
def list_announcements_api(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """分页查询公告"""
    items, total = list_announcements(db, (page - 1) * page_size, page_size)
    data = []
    for a in items:
        data.append({
            "id": a.id, "title": a.title, "content": a.content,
            "publisher_name": a.publisher.name if a.publisher else None,
            "is_pinned": a.is_pinned,
            "create_time": a.create_time.isoformat() if a.create_time else None,
            "update_time": a.update_time.isoformat() if a.update_time else None,
        })
    return {"items": data, "total": total, "page": page, "page_size": page_size}


@router.post("/announcements", status_code=status.HTTP_201_CREATED)
def create_announcement_api(
    body: AnnouncementCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """发布公告"""
    a = create_announcement(db, body.title, body.content, current_user["user_id"], body.is_pinned)
    return {"id": a.id, "title": a.title, "create_time": a.create_time.isoformat() if a.create_time else None}


@router.put("/announcements/{a_id}")
def update_announcement_api(
    a_id: int,
    body: AnnouncementUpdate,
    db: Session = Depends(get_db),
):
    """更新公告"""
    a = get_by_id(db, a_id)
    if not a:
        raise HTTPException(status_code=404, detail="公告不存在")
    updates = body.model_dump(exclude_none=True)
    a = update_announcement(db, a, updates)
    return {"id": a.id, "title": a.title, "message": "更新成功"}


@router.delete("/announcements/{a_id}")
def delete_announcement_api(a_id: int, db: Session = Depends(get_db)):
    """删除公告"""
    a = get_by_id(db, a_id)
    if not a:
        raise HTTPException(status_code=404, detail="公告不存在")
    delete_announcement(db, a)
    return {"message": "删除成功"}


# ==================== 密码修改（管理员自己） ====================

@router.put("/change-password")
def admin_change_password(
    old_password: str = Query(..., min_length=1),
    new_password: str = Query(..., min_length=1, max_length=128),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """管理员修改自己的密码"""
    from ..dao.auth_dao import get_user_by_id
    user = get_user_by_id(db, current_user["user_id"])
    if not auth_service.verify_password(old_password, user.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password = auth_service.hash_password(new_password)
    db.commit()
    return {"message": "密码修改成功"}


# ==================== 日志查询 ====================

@router.get("/login-logs")
def list_login_logs(
    user_id: int = Query(None), keyword: str = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """全局登录日志"""
    logs, total = login_log_dao.list_login_logs(db, user_id, keyword, (page - 1) * page_size, page_size)
    items = []
    for log in logs:
        items.append({
            "id": log.id, "user_id": log.user_id, "login_ip": log.login_ip,
            "login_time": log.login_time.isoformat() if log.login_time else None,
            "logout_time": log.logout_time.isoformat() if log.logout_time else None,
            "login_role": log.login_role,
            "username": log.user.username if log.user else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0}


@router.get("/borrow-logs")
def list_borrow_operation_logs(
    operate_type: str = Query(None), keyword: str = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(PAGE_SIZE, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """全局借阅操作日志"""
    logs, total = borrow_log_dao.list_borrow_logs(db, operate_type, (page - 1) * page_size, page_size)
    items = []
    for log in logs:
        record = borrow_dao.get_borrow_by_id(db, log.borrow_record_id)
        book_name = None; student_name = None
        if record:
            book = book_dao.get_book_by_id(db, record.book_id)
            reader = reader_dao.get_reader_by_id(db, record.reader_id)
            book_name = book.book_name if book else None
            student_name = reader.student_name if reader else None
        items.append({
            "id": log.id, "borrow_record_id": log.borrow_record_id,
            "operate_type": log.operate_type,
            "operate_time": log.operate_time.isoformat() if log.operate_time else None,
            "operate_user_id": log.operate_user_id,
            "book_name": book_name, "student_name": student_name,
        })
    if keyword:
        kw = keyword.lower()
        items = [i for i in items if (i.get("book_name") and kw in i["book_name"].lower()) or (i.get("student_name") and kw in i["student_name"].lower())]
    return {"items": items, "total": len(items), "page": page, "page_size": page_size,
            "total_pages": (len(items) + page_size - 1) // page_size if items else 0}
