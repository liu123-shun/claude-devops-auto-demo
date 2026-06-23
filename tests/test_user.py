"""
用户管理接口单元测试
====================
覆盖 FastAPI 全部 4 个 CRUD 接口的正常与异常场景。

运行方式:
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from http import HTTPStatus

from src.main import app
from src.user_service import UserNotFoundError, UserService


# ---------------------------------------------------------------------------
# 测试夹具
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """返回 FastAPI TestClient 实例，每次测试使用独立 app。"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_service() -> None:
    """每个测试用例执行前重置 UserService 到初始状态，保证用例隔离。"""
    from src import main

    main.service = UserService()


# ---------------------------------------------------------------------------
# 单元测试 — UserService 层
# ---------------------------------------------------------------------------


class TestUserService:
    """UserService 内存存储层的单元测试。"""

    # ---- 新增 ---------------------------------------------------------------

    def test_create_user_success(self):
        """新增用户成功应返回带ID的 User 对象。"""
        svc = UserService()
        user = svc.create_user(name="张三", email="zs@example.com", age=25)
        assert user.id == 1
        assert user.name == "张三"
        assert user.email == "zs@example.com"
        assert user.age == 25

    def test_create_user_empty_name_raises(self):
        """name 为空时应抛出 ValueError。"""
        svc = UserService()
        with pytest.raises(ValueError, match="name 不能为空"):
            svc.create_user(name="", email="a@b.com")

    def test_create_user_empty_email_raises(self):
        """email 为空时应抛出 ValueError。"""
        svc = UserService()
        with pytest.raises(ValueError, match="email 不能为空"):
            svc.create_user(name="张三", email="")

    def test_create_user_auto_increment_id(self):
        """连续新增用户，ID 应自增不重复。"""
        svc = UserService()
        u1 = svc.create_user(name="A", email="a@x.com")
        u2 = svc.create_user(name="B", email="b@x.com")
        assert u1.id == 1
        assert u2.id == 2

    # ---- 查询（单个） -------------------------------------------------------

    def test_get_user_by_id_found(self):
        """按已有ID查询应返回对应用户。"""
        svc = UserService()
        svc.create_user(name="李四", email="ls@example.com")
        user = svc.get_user_by_id(1)
        assert user.name == "李四"

    def test_get_user_by_id_not_found(self):
        """查询不存在的ID应抛出 UserNotFoundError。"""
        svc = UserService()
        with pytest.raises(UserNotFoundError, match="用户不存在: id=999"):
            svc.get_user_by_id(999)

    # ---- 查询（列表） -------------------------------------------------------

    def test_list_users_returns_all(self):
        """list_users 应返回所有用户按ID升序排列。"""
        svc = UserService()
        svc.create_user(name="A", email="a@x.com")
        svc.create_user(name="B", email="b@x.com")
        result = svc.list_users()
        assert len(result) == 2
        assert [u.id for u in result] == [1, 2]

    def test_list_users_empty(self):
        """无用户时应返回空列表。"""
        svc = UserService()
        assert svc.list_users() == []

    # ---- 修改 ---------------------------------------------------------------

    def test_update_user_partial(self):
        """部分更新应仅修改传入的字段。"""
        svc = UserService()
        svc.create_user(name="王五", email="ww@example.com", age=30)
        updated = svc.update_user(user_id=1, name="王五改")
        assert updated.name == "王五改"
        # email 不应被覆盖
        assert updated.email == "ww@example.com"
        assert updated.age == 30

    def test_update_user_not_found(self):
        """更新不存在的用户应抛出 UserNotFoundError。"""
        svc = UserService()
        with pytest.raises(UserNotFoundError):
            svc.update_user(user_id=999, name="不存在")

    # ---- 删除 ---------------------------------------------------------------

    def test_delete_user_success(self):
        """删除已有用户应返回被删除对象，且后续查询失败。"""
        svc = UserService()
        svc.create_user(name="赵六", email="zl@example.com")
        deleted = svc.delete_user(1)
        assert deleted.name == "赵六"
        with pytest.raises(UserNotFoundError):
            svc.get_user_by_id(1)

    def test_delete_user_not_found(self):
        """删除不存在的用户应抛出 UserNotFoundError。"""
        svc = UserService()
        with pytest.raises(UserNotFoundError):
            svc.delete_user(999)


# ---------------------------------------------------------------------------
# 集成测试 — FastAPI 接口层
# ---------------------------------------------------------------------------


class TestUserAPI:
    """通过 TestClient 测试完整的 HTTP 请求/响应链路。"""

    # ---- POST /users --------------------------------------------------------

    def test_create_user_201(self, client: TestClient):
        """正常创建应返回 201 与用户数据。"""
        resp = client.post(
            "/users", json={"name": "张三", "email": "zs@example.com", "age": 25}
        )
        assert resp.status_code == HTTPStatus.CREATED
        body = resp.json()
        assert body["id"] == 1
        assert body["name"] == "张三"

    def test_create_user_422_empty_name(self, client: TestClient):
        """name 为空字符串由 Pydantic min_length 校验拦截，返回 422。"""
        resp = client.post("/users", json={"name": "", "email": "a@b.com"})
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_create_user_400_invalid_email(self, client: TestClient):
        """email 格式不合法应返回 422（Pydantic 校验）。"""
        resp = client.post("/users", json={"name": "张三", "email": "not-an-email"})
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # ---- GET /users ---------------------------------------------------------

    def test_list_users_200(self, client: TestClient):
        """查询列表应返回 200 与用户数组。"""
        client.post("/users", json={"name": "A", "email": "a@x.com"})
        client.post("/users", json={"name": "B", "email": "b@x.com"})
        resp = client.get("/users")
        assert resp.status_code == HTTPStatus.OK
        assert len(resp.json()) == 2

    def test_list_users_empty(self, client: TestClient):
        """无用户时返回空数组。"""
        resp = client.get("/users")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json() == []

    # ---- GET /users/{id} ----------------------------------------------------

    def test_get_user_200(self, client: TestClient):
        """查询已有用户返回 200。"""
        client.post("/users", json={"name": "李四", "email": "ls@example.com"})
        resp = client.get("/users/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json()["name"] == "李四"

    def test_get_user_404(self, client: TestClient):
        """查询不存在的用户返回 404。"""
        resp = client.get("/users/999")
        assert resp.status_code == HTTPStatus.NOT_FOUND

    # ---- PUT /users/{id} ----------------------------------------------------

    def test_update_user_200(self, client: TestClient):
        """部分更新成功返回 200。"""
        client.post("/users", json={"name": "王五", "email": "ww@example.com"})
        resp = client.put("/users/1", json={"name": "王五改"})
        assert resp.status_code == HTTPStatus.OK
        assert resp.json()["name"] == "王五改"
        # email 不变
        assert resp.json()["email"] == "ww@example.com"

    def test_update_user_404(self, client: TestClient):
        """更新不存在的用户返回 404。"""
        resp = client.put("/users/999", json={"name": "不存在"})
        assert resp.status_code == HTTPStatus.NOT_FOUND

    # ---- DELETE /users/{id} -------------------------------------------------

    def test_delete_user_200(self, client: TestClient):
        """删除成功返回 200 与被删除用户。"""
        client.post("/users", json={"name": "赵六", "email": "zl@example.com"})
        resp = client.delete("/users/1")
        assert resp.status_code == HTTPStatus.OK
        assert resp.json()["name"] == "赵六"
        # 确认已删除
        assert client.get("/users/1").status_code == HTTPStatus.NOT_FOUND

    def test_delete_user_404(self, client: TestClient):
        """删除不存在的用户返回 404。"""
        resp = client.delete("/users/999")
        assert resp.status_code == HTTPStatus.NOT_FOUND
