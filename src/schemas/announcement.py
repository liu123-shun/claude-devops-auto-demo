"""公告校验模型"""
from typing import Optional
from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    content: str = Field(..., min_length=1)
    is_pinned: int = Field(0, ge=0, le=1)


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    content: Optional[str] = Field(None, min_length=1)
    is_pinned: Optional[int] = Field(None, ge=0, le=1)
