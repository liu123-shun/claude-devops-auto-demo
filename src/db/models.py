"""
数据库表模型（共7张表）
======================
使用 SQLAlchemy ORM 定义全部业务表结构。
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SysUser(Base):
    """系统账号表 — 区分管理员/学生角色"""
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True, comment="登录账号")
    password = Column(String(255), nullable=False, comment="bcrypt加密密码")
    role = Column(String(16), nullable=False, default="student", comment="角色: admin / student")
    name = Column(String(64), nullable=False, comment="真实姓名")
    phone = Column(String(32), nullable=True, comment="手机号")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    reader = relationship("Reader", back_populates="user", uselist=False)
    login_logs = relationship("LoginLog", back_populates="user")


class Book(Base):
    """图书表"""
    __tablename__ = "book"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_name = Column(String(128), nullable=False, comment="书名")
    author = Column(String(64), nullable=False, comment="作者")
    category = Column(String(64), nullable=True, comment="分类")
    isbn = Column(String(32), nullable=True, comment="ISBN编号")
    publisher = Column(String(64), nullable=True, comment="出版社")
    description = Column(Text, nullable=True, comment="图书简介")
    cover_url = Column(String(512), nullable=True, comment="封面图片URL")
    publish_time = Column(DateTime, nullable=True, comment="出版时间")
    stock = Column(Integer, nullable=False, default=0, comment="库存数量")
    total_borrows = Column(Integer, nullable=False, default=0, comment="累计借阅次数")
    create_time = Column(DateTime, default=datetime.now, comment="入库时间")


class Reader(Base):
    """学生读者基础信息表"""
    __tablename__ = "reader"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_name = Column(String(64), nullable=False, comment="学生姓名")
    class_ = Column("class", String(64), nullable=True, comment="班级")
    phone = Column(String(32), nullable=True, comment="手机号")
    bind_user_id = Column(Integer, ForeignKey("sys_user.id"), unique=True, nullable=True, comment="关联系统账号ID")

    user = relationship("SysUser", back_populates="reader")


class BorrowRecord(Base):
    """借阅记录表"""
    __tablename__ = "borrow_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("book.id"), nullable=False, comment="图书ID")
    reader_id = Column(Integer, ForeignKey("reader.id"), nullable=False, comment="读者ID")
    borrow_time = Column(DateTime, default=datetime.now, comment="借阅时间")
    return_time = Column(DateTime, nullable=True, comment="归还时间")
    status = Column(String(16), nullable=False, default="borrowed", comment="borrowed / returned / overdue")


class LoginLog(Base):
    """登录日志表"""
    __tablename__ = "login_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="登录用户ID")
    login_ip = Column(String(64), nullable=True, comment="登录IP")
    login_time = Column(DateTime, default=datetime.now, comment="登录时间")
    logout_time = Column(DateTime, nullable=True, comment="退出时间")
    login_role = Column(String(16), nullable=True, comment="登录时角色")

    user = relationship("SysUser", back_populates="login_logs")


class BorrowOperationLog(Base):
    """借阅操作日志表"""
    __tablename__ = "borrow_operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    borrow_record_id = Column(Integer, ForeignKey("borrow_record.id"), nullable=False, comment="借阅记录ID")
    operate_type = Column(String(16), nullable=False, comment="borrow / return")
    operate_time = Column(DateTime, default=datetime.now, comment="操作时间")
    operate_user_id = Column(Integer, nullable=False, comment="操作人ID")


class Announcement(Base):
    """系统公告表"""
    __tablename__ = "announcement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False, comment="公告标题")
    content = Column(Text, nullable=False, comment="公告内容")
    publisher_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="发布人ID")
    is_pinned = Column(Integer, nullable=False, default=0, comment="是否置顶: 0=否 1=是")
    create_time = Column(DateTime, default=datetime.now, comment="发布时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    publisher = relationship("SysUser")


class BookReview(Base):
    """图书评分评论表"""
    __tablename__ = "book_review"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("book.id"), nullable=False, comment="图书ID")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="评论用户ID")
    rating = Column(Integer, nullable=False, comment="评分: 1-5")
    comment = Column(Text, nullable=True, comment="评论内容")
    create_time = Column(DateTime, default=datetime.now, comment="评论时间")

    user = relationship("SysUser")
    book = relationship("Book")
