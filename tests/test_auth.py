import pytest
from app.models.user import User
from app.database import db

def test_user_password_hashing(app):
    user = User(username="prof_smith", email="smith@school.edu", full_name="Prof Smith", role="teacher")
    user.set_password("Secret123!")
    assert user.password_hash != "Secret123!"
    assert user.check_password("Secret123!") is True
    assert user.check_password("WrongPassword") is False
    assert user.is_teacher is True
    assert user.is_student is False

def test_auth_registration_and_login(client, app):
    # Register teacher
    res = client.post("/auth/register", data={
        "username": "teacher1",
        "email": "teacher1@example.com",
        "password": "Password123!",
        "full_name": "Teacher One",
        "role": "teacher"
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="teacher1").first()
        assert user is not None
        assert user.role == "teacher"

    # Login
    res = client.post("/auth/login", data={
        "username_or_email": "teacher1",
        "password": "Password123!"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Teacher One" in res.data or b"Dashboard" in res.data
