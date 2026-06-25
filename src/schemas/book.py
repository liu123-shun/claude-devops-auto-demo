"""
图书 Pydantic 校验模型
======================
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    """新增图书"""
    book_name: str = Field(..., min_length=1, max_length=128, description="书名")
    author: str = Field(..., min_length=1, max_length=64, description="作者")
    category: Optional[str] = Field(None, max_length=64, description="分类")
    isbn: Optional[str] = Field(None, max_length=32, description="ISBN")
    publisher: Optional[str] = Field(None, max_length=64, description="出版社")
    description: Optional[str] = Field(None, max_length=2000, description="简介")
    cover_url: Optional[str] = Field(None, max_length=512, description="封面URL")
    publish_time: Optional[datetime] = Field(None, description="出版时间")
    stock: int = Field(0, ge=0, description="库存数量")


class BookUpdate(BaseModel):
    """更新图书（部分更新）"""
    book_name: Optional[str] = Field(None, min_length=1, max_length=128)
    author: Optional[str] = Field(None, min_length=1, max_length=64)
    category: Optional[str] = Field(None, max_length=64)
    isbn: Optional[str] = Field(None, max_length=32)
    publisher: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = Field(None, max_length=2000)
    cover_url: Optional[str] = Field(None, max_length=512)
    publish_time: Optional[datetime] = Field(None)
    stock: Optional[int] = Field(None, ge=0)


class BookResponse(BaseModel):
    """图书信息响应"""
    id: int
    book_name: str
    author: str
    category: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    publish_time: Optional[datetime] = None
    stock: int
    total_borrows: int = 0
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True
