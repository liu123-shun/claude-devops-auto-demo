"""
登录鉴权单元测试
===============
覆盖：JWT签发/验证、密码加密、登录接口、角色拦截
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.database import get_db
from src.service.auth_service import hash_password, verify_password, create_jwt_token, decode_jwt_token

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
    """每个测试前重建数据库表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """返回 TestClient，注入测试数据库会话"""
    from src.main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestPasswordHashing:
    """密码加密与验证"""

    def test_hash_and_verify(self):
        hashed = hash_password("123456")
        assert hashed != "123456"
        assert verify_password("123456", hashed)
        assert not verify_password("wrong", hashed)


class TestJWT:
    """JWT 签发与解析"""

    def test_create_and_decode(self):
        token = create_jwt_token(1, "admin", "admin")
        payload = decode_jwt_token(token)
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"

    def test_decode_invalid_token(self):
        assert decode_jwt_token("invalid.token.here") is None


class TestAuthAPI:
    """登录 API 接口测试"""

    def test_login_requires_role(self, client):
        """缺少 role 字段应返回 422"""
        resp = client.post("/api/auth/login", json={"username": "admin", "password": "123"})
        assert resp.status_code == 422

    def test_login_invalid_credentials(self, client):
        """错误密码应返回 401"""
        resp = client.post("/api/auth/login", json={
            "username": "admin", "password": "wrong", "role": "admin"
        })
        assert resp.status_code == 401

    def test_me_without_token(self, client):
        """未登录访问 /api/auth/me 应返回 403（无 Bearer token）"""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 403
