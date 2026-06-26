"""评分评论校验模型"""
from typing import Optional
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    comment: Optional[str] = Field(None, max_length=1000, description="评论内容")
