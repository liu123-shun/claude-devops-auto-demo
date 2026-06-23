"""
FastAPI 应用入口
================
提供用户管理的 RESTful API，基于内存 UserService。

启动方式:
    uvicorn src.main:app --reload

接口:
    POST   /users         新增用户
    GET    
    /users         查询全部用户
    GET    /users/{id}    按ID查询
    PUT    /users/{id}    更新用户
    DELETE /users/{id}    删除用户
"""

from http import HTTPStatus
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .user_service import UserNotFoundError, UserService

# ---------------------------------------------------------------------------
# FastAPI 实例 & 服务层
# ---------------------------------------------------------------------------

app = FastAPI(
    title="用户管理后端",
    version="1.0.0",
    description="简易用户CRUD服务，内存存储",
)
service = UserService()


# ---------------------------------------------------------------------------
# Pydantic 请求/响应模型
# ---------------------------------------------------------------------------


class UserCreateRequest(BaseModel):
    """新增用户请求体。

    Attributes:
        name:  用户姓名（必填，1-64字符）
        email: 用户邮箱（必填，需含@）
        age:   用户年龄（可选，0-150）
    """

    name: str = Field(..., min_length=1, max_length=64, description="用户姓名")
    email: str = Field(
        ..., min_length=1, max_length=128, pattern=r"^[^@]+@[^@]+$", description="用户邮箱"
    )
    age: Optional[int] = Field(None, ge=0, le=150, description="用户年龄")


class UserUpdateRequest(BaseModel):
    """更新用户请求体，所有字段均为可选。

    Attributes:
        name:  新姓名
        email: 新邮箱
        age:   新年龄
    """

    name: Optional[str] = Field(None, min_length=1, max_length=64, description="用户姓名")
    email: Optional[str] = Field(
        None, min_length=1, max_length=128, pattern=r"^[^@]+@[^@]+$", description="用户邮箱"
    )
    age: Optional[int] = Field(None, ge=0, le=150, description="用户年龄")


class UserResponse(BaseModel):
    """用户信息响应体。

    Attributes:
        id:    用户ID
        name:  用户姓名
        email: 用户邮箱
        age:   用户年龄
    """

    id: int
    name: str
    email: str
    age: Optional[int] = None


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _build_response(user) -> UserResponse:
    """将内部 User 对象转换为 API 响应模型。"""
    return UserResponse(id=user.id, name=user.name, email=user.email, age=user.age)


def _handle_not_found(exc: UserNotFoundError) -> None:
    """将 UserNotFoundError 统一转为 404 HTTPException。"""
    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# API 路由
# ---------------------------------------------------------------------------


@app.post("/users", response_model=UserResponse, status_code=HTTPStatus.CREATED)
def create_user(body: UserCreateRequest) -> UserResponse:
    """新增用户。

    - 201: 创建成功，返回用户信息
    - 400: 参数校验失败
    """
    try:
        user = service.create_user(name=body.name, email=body.email, age=body.age)
        return _build_response(user)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(exc))


@app.get("/users", response_model=list[UserResponse])
def list_users() -> list[UserResponse]:
    """查询全部用户。

    - 200: 返回用户列表（无用户时为空列表）
    """
    return [_build_response(u) for u in service.list_users()]


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int) -> UserResponse:
    """按ID查询用户。

    - 200: 返回用户信息
    - 404: 用户不存在
    """
    try:
        return _build_response(service.get_user_by_id(user_id))
    except UserNotFoundError as exc:
        _handle_not_found(exc)


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, body: UserUpdateRequest) -> UserResponse:
    """更新用户信息（部分更新）。

    - 200: 更新成功，返回最新用户信息
    - 404: 用户不存在
    - 400: 参数校验失败
    """
    try:
        user = service.update_user(
            user_id=user_id, name=body.name, email=body.email, age=body.age
        )
        return _build_response(user)
    except UserNotFoundError as exc:
        _handle_not_found(exc)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(exc))


@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int) -> UserResponse:
    """删除用户。

    - 200: 删除成功，返回被删除的用户信息
    - 404: 用户不存在
    """
    try:
        return _build_response(service.delete_user(user_id))
    except UserNotFoundError as exc:
        _handle_not_found(exc)
