import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture()
def client(monkeypatch):
    # Each test run gets a fresh SQLite database.
    from app import config
    from app import database
    from app.main import app
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    test_engine = database.create_engine(
        f"sqlite:///{path}", connect_args={"check_same_thread": False, "timeout": 30}, future=True
    )
    database.Base.metadata.create_all(test_engine)
    TestSession = database.sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    from app.models import User
    with TestSession() as db:
        users = [
            User(user_id="M1", name="Maker One", roles=["Maker"]),
            User(user_id="M2", name="Maker Two", roles=["Maker"]),
            User(user_id="C1", name="Checker One", roles=["Checker"]),
            User(user_id="C2", name="Checker Two", roles=["Checker"]),
            User(user_id="MC1", name="Maker Checker", roles=["Maker", "Checker"]),
            User(user_id="A1", name="Admin", roles=["Admin"]),
        ]
        db.add_all(users)
        db.commit()
    from app.database import get_db
    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    test_engine.dispose()
    os.unlink(path)
