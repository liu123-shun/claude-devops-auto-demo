"""
读者数据访问层
=============
"""

from typing import Optional
from sqlalchemy.orm import Session

from ..db.models import Reader


def create_reader(db: Session, reader: Reader) -> Reader:
    """新增读者"""
    db.add(reader)
    db.commit()
    db.refresh(reader)
    return reader


def get_reader_by_id(db: Session, reader_id: int) -> Optional[Reader]:
    """按ID查询读者"""
    return db.query(Reader).filter(Reader.id == reader_id).first()


def get_reader_by_user_id(db: Session, user_id: int) -> Optional[Reader]:
    """按关联账号ID查询读者"""
    return db.query(Reader).filter(Reader.bind_user_id == user_id).first()


def list_readers(
    db: Session,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> tuple:
    """分页查询读者列表"""
    q = db.query(Reader)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (Reader.student_name.like(like)) | (Reader.class_.like(like))
        )
    total = q.count()
    readers = q.order_by(Reader.id.desc()).offset(skip).limit(limit).all()
    return readers, total


def update_reader(db: Session, reader: Reader, updates: dict) -> Reader:
    """更新读者"""
    for key, value in updates.items():
        if value is not None:
            setattr(reader, key, value)
    db.commit()
    db.refresh(reader)
    return reader


def delete_reader(db: Session, reader: Reader) -> None:
    """删除读者"""
    db.delete(reader)
    db.commit()
