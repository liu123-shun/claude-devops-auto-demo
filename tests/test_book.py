"""
图书管理单元测试
===============
覆盖：图书 CRUD 接口、管理员权限校验
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.database import get_db

# ---- 使用 SQLite 内存数据库进行测试 ----
SQLITE_URL = "sqlite:///./test_library.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    # 创建管理员账号用于测试
    from src.service.auth_service import hash_password, create_jwt_token
    from src.db.models import SysUser
    db = TestingSessionLocal()
    admin = SysUser(username="admin", password=hash_password("123456"), role="admin", name="管理员")
    db.add(admin)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_token():
    """生成管理员 JWT Token"""
    from src.service.auth_service import create_jwt_token
    return create_jwt_token(1, "admin", "admin")


@pytest.fixture
def client():
    from src.main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestBookCRUD:
    """图书增删改查"""

    def test_create_book(self, client, admin_token):
        resp = client.post(
            "/api/admin/books",
            json={"book_name": "测试图书", "author": "测试作者", "stock": 5},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["book_name"] == "测试图书"
        assert data["stock"] == 5

    def test_list_books(self, client, admin_token):
        # 先创建一本
        client.post(
            "/api/admin/books",
            json={"book_name": "Python入门", "author": "张三", "stock": 3},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get(
            "/api/admin/books",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_update_book(self, client, admin_token):
        # 创建
        r = client.post(
            "/api/admin/books",
            json={"book_name": "旧书名", "author": "旧作者", "stock": 2},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        book_id = r.json()["id"]
        # 更新
        resp = client.put(
            f"/api/admin/books/{book_id}",
            json={"book_name": "新书名"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["book_name"] == "新书名"

    def test_delete_book(self, client, admin_token):
        r = client.post(
            "/api/admin/books",
            json={"book_name": "待删除", "author": "某人", "stock": 1},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        book_id = r.json()["id"]
        resp = client.delete(
            f"/api/admin/books/{book_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    def test_unauthorized_access(self, client):
        """无 Token 访问管理接口应返回 403"""
        resp = client.get("/api/admin/books")
        assert resp.status_code == 403
