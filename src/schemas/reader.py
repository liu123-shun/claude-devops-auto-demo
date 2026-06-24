"""
读者 Pydantic 校验模型
======================
"""

from typing import Optional
from pydantic import BaseModel, Field


class ReaderCreate(BaseModel):
    """新增读者"""
    student_name: str = Field(..., min_length=1, max_length=64, description="学生姓名")
    class_: Optional[str] = Field(None, max_length=64, alias="class_name", description="班级")
    phone: Optional[str] = Field(None, max_length=32, description="手机号")
    bind_user_id: Optional[int] = Field(None, description="关联系统账号ID")


class ReaderUpdate(BaseModel):
    """更新读者信息"""
    student_name: Optional[str] = Field(None, min_length=1, max_length=64, description="学生姓名")
    class_: Optional[str] = Field(None, max_length=64, alias="class_name", description="班级")
    phone: Optional[str] = Field(None, max_length=32, description="手机号")
    bind_user_id: Optional[int] = Field(None, description="关联系统账号ID")


class ReaderResponse(BaseModel):
    """读者信息响应"""
    id: int
    student_name: str
    class_: Optional[str] = None
    phone: Optional[str] = None
    bind_user_id: Optional[int] = None

    class Config:
        from_attributes = True
