"""
读者业务逻辑层
=============
"""

from typing import Optional
from sqlalchemy.orm import Session

from ..db.models import Reader, SysUser
from ..dao import reader_dao, auth_dao
from ..service.auth_service import hash_password


def add_reader(
    db: Session,
    student_name: str,
    class_name: Optional[str] = None,
    phone: Optional[str] = None,
    bind_username: Optional[str] = None,
    bind_password: Optional[str] = None,
) -> Reader:
    """新增读者，可选择同时创建系统账号并绑定"""
    bind_user_id = None
    if bind_username and bind_password:
        # 创建系统账号
        user = SysUser(
            username=bind_username,
            password=hash_password(bind_password),
            role="student",
            name=student_name,
            phone=phone,
        )
        user = auth_dao.create_user(db, user)
        bind_user_id = user.id

    reader = Reader(
        student_name=student_name,
        class_=class_name,
        phone=phone,
        bind_user_id=bind_user_id,
    )
    return reader_dao.create_reader(db, reader)


def get_reader(db: Session, reader_id: int) -> Optional[Reader]:
    """查询单个读者"""
    return reader_dao.get_reader_by_id(db, reader_id)


def get_reader_by_user(db: Session, user_id: int) -> Optional[Reader]:
    """按关联账号查询读者"""
    return reader_dao.get_reader_by_user_id(db, user_id)


def search_readers(
    db: Session,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """分页搜索读者"""
    skip = (page - 1) * page_size
    readers, total = reader_dao.list_readers(db, keyword, skip, page_size)
    return {
        "items": readers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


def update_reader(db: Session, reader_id: int, updates: dict) -> Optional[Reader]:
    """更新读者"""
    reader = reader_dao.get_reader_by_id(db, reader_id)
    if not reader:
        return None
    # 处理 class_name 到 class_ 的映射
    if "class_name" in updates:
        updates["class_"] = updates.pop("class_name")
    return reader_dao.update_reader(db, reader, updates)


def remove_reader(db: Session, reader_id: int) -> bool:
    """删除读者"""
    reader = reader_dao.get_reader_by_id(db, reader_id)
    if not reader:
        return False
    reader_dao.delete_reader(db, reader)
    return True
