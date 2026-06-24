"""
日志 Pydantic 校验模型
======================
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LoginLogResponse(BaseModel):
    """登录日志响应"""
    id: int
    user_id: int
    login_ip: Optional[str] = None
    login_time: Optional[datetime] = None
    logout_time: Optional[datetime] = None
    login_role: Optional[str] = None
    username: Optional[str] = None

    class Config:
        from_attributes = True


class BorrowOperationLogResponse(BaseModel):
    """借阅操作日志响应"""
    id: int
    borrow_record_id: int
    operate_type: str
    operate_time: Optional[datetime] = None
    operate_user_id: int
    book_name: Optional[str] = None
    student_name: Optional[str] = None

    class Config:
        from_attributes = True
