"""
日志相关单元测试
===============
覆盖：登录日志查询、借阅操作日志查询
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.database import get_db

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
    db = TestingSessionLocal()
    from src.service.auth_service import hash_password
    from src.db.models import SysUser
    admin = SysUser(username="admin", password=hash_password("123456"), role="admin", name="管理员")
    student = SysUser(username="stu001", password=hash_password("123456"), role="student", name="学生")
    db.add_all([admin, student])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_token():
    from src.service.auth_service import create_jwt_token
    return create_jwt_token(1, "admin", "admin")


@pytest.fixture
def student_token():
    from src.service.auth_service import create_jwt_token
    return create_jwt_token(2, "stu001", "student")


@pytest.fixture
def client():
    from src.main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestLoginLogs:
    """登录日志查询"""

    def test_admin_can_view_all_logs(self, client, admin_token):
        resp = client.get(
            "/api/admin/login-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    def test_student_can_view_own_logs(self, client, student_token):
        resp = client.get(
            "/api/student/login-logs",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200


class TestBorrowLogs:
    """借阅操作日志查询"""

    def test_admin_can_view_borrow_logs(self, client, admin_token):
        resp = client.get(
            "/api/admin/borrow-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200


class TestDashboard:
    """看板统计"""

    def test_admin_dashboard(self, client, admin_token):
        resp = client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_books" in data
        assert "active_borrows" in data
        assert "overdue_count" in data

    def test_student_dashboard(self, client, student_token):
        resp = client.get(
            "/api/student/dashboard",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert resp.status_code == 200
