"""
用户服务模块
============
提供用户数据的增删改查（CRUD）操作，使用内存字典存储数据。

核心类:
    UserService — 线程安全的内存用户存储与操作集合

异常:
    UserNotFoundError — 查询或操作不存在的用户时抛出
"""

import threading
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# 自定义异常
# ---------------------------------------------------------------------------


class UserNotFoundError(Exception):
    """目标用户不存在时抛出的异常。

    Attributes:
        user_id: 未能找到的用户ID
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"用户不存在: id={user_id}")


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class User:
    """用户数据对象。

    Attributes:
        id:     用户唯一标识（自动分配）
        name:   用户姓名
        email:  用户邮箱
        age:    用户年龄（可选）
    """

    id: int
    name: str
    email: str
    age: Optional[int] = None


# ---------------------------------------------------------------------------
# 用户数据访问层（内存实现）
# ---------------------------------------------------------------------------


class UserService:
    """用户CRUD服务，基于内存字典实现。

    所有写操作由 _lock 保护，保证线程安全。

    Usage:
        service = UserService()
        user = service.create_user(name="张三", email="zs@example.com", age=28)
        found = service.get_user_by_id(user.id)
    """

    def __init__(self) -> None:
        """初始化空用户存储与自增ID计数器。"""
        self._users: dict[int, User] = {}
        self._next_id: int = 1
        self._lock = threading.Lock()

    # ---- 内部工具方法 -------------------------------------------------------

    def _validate_not_empty(self, value: str, field_name: str) -> None:
        """校验字符串字段非 None 且 strip 后非空，不满足时抛出 ValueError。

        Args:
            value:      待校验字符串
            field_name: 字段中文名（如 "name"、"email"），用于错误提示

        Raises:
            ValueError: value 为 None 或 strip 后为空字符串时抛出
        """
        if value is None or not value.strip():
            raise ValueError(f"{field_name} 不能为空")

    def _get_user_or_raise(self, user_id: int) -> User:
        """按ID从内存字典获取用户，不存在则抛出 UserNotFoundError。

        调用方需在外部持有 _lock 以保证线程安全。

        Args:
            user_id: 目标用户ID

        Returns:
            匹配的 User 对象

        Raises:
            UserNotFoundError: 用户不存在时抛出
        """
        user = self._users.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    # ---- 新增 ---------------------------------------------------------------

    def create_user(
        self, name: str, email: str, age: Optional[int] = None
    ) -> User:
        """新增用户并返回带唯一ID的 User 对象。

        Args:
            name:  用户姓名，不能为空
            email: 用户邮箱，不能为空
            age:   用户年龄（可选）

        Returns:
            创建成功的 User 对象，id 字段已自动分配

        Raises:
            ValueError: name 或 email 为空时抛出
        """
        self._validate_not_empty(name, "name")
        self._validate_not_empty(email, "email")

        with self._lock:
            user = User(
                id=self._next_id,
                name=name.strip(),
                email=email.strip(),
                age=age,
            )
            self._users[self._next_id] = user
            self._next_id += 1
            return user

    # ---- 查询（单个） -------------------------------------------------------

    def get_user_by_id(self, user_id: int) -> User:
        """按ID查询用户。

        Args:
            user_id: 目标用户ID

        Returns:
            匹配的 User 对象

        Raises:
            UserNotFoundError: 用户不存在时抛出
        """
        return self._get_user_or_raise(user_id)

    # ---- 查询（列表） -------------------------------------------------------

    def list_users(self) -> list[User]:
        """返回当前所有用户列表（按ID升序）。

        Returns:
            User 对象列表，无用户时返回空列表
        """
        return sorted(self._users.values(), key=lambda u: u.id)

    # ---- 修改 ---------------------------------------------------------------

    def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        age: Optional[int] = None,
    ) -> User:
        """部分更新用户信息，仅修改传入的非 None 字段。

        Args:
            user_id: 目标用户ID
            name:    新姓名（None 表示不修改）
            email:   新邮箱（None 表示不修改）
            age:     新年龄（None 表示不修改）

        Returns:
            更新后的 User 对象

        Raises:
            UserNotFoundError: 用户不存在时抛出
            ValueError: 传入的 name 或 email 为空字符串时抛出
        """
        if name is not None:
            self._validate_not_empty(name, "name")
        if email is not None:
            self._validate_not_empty(email, "email")

        with self._lock:
            user = self._get_user_or_raise(user_id)
            if name is not None:
                user.name = name.strip()
            if email is not None:
                user.email = email.strip()
            if age is not None:
                user.age = age
            return user

    # ---- 删除 ---------------------------------------------------------------

    def delete_user(self, user_id: int) -> User:
        """删除指定用户并返回被删除的 User 对象。

        Args:
            user_id: 目标用户ID

        Returns:
            被删除的 User 对象

        Raises:
            UserNotFoundError: 用户不存在时抛出
        """
        with self._lock:
            user = self._users.pop(user_id, None)
            if user is None:
                raise UserNotFoundError(user_id)
            return user
