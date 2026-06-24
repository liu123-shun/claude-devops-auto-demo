"""
借阅 Pydantic 校验模型
======================
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BorrowCreate(BaseModel):
    """借书请求"""
    book_id: int = Field(..., gt=0, description="图书ID")
    reader_id: int = Field(..., gt=0, description="读者ID")


class BorrowReturn(BaseModel):
    """还书请求"""
    pass  # 仅需借阅记录ID路径参数


class BorrowResponse(BaseModel):
    """借阅记录响应"""
    id: int
    book_id: int
    reader_id: int
    borrow_time: Optional[datetime] = None
    return_time: Optional[datetime] = None
    status: str = "borrowed"
    book_name: Optional[str] = None
    student_name: Optional[str] = None

    class Config:
        from_attributes = True
