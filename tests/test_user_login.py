import pytest
from user_login import User, LoginSystem

def test_user_registration():
    login_system = LoginSystem()
    login_system.register("testuser", "testpassword")
    assert "testuser" in login_system.users

def test_user_login_success():
    login_system = LoginSystem()
    login_system.register("testuser", "testpassword")
    assert login_system.login("testuser", "testpassword") is True

def test_user_login_failure():
    login_system = LoginSystem()
    login_system.register("testuser", "testpassword")
    assert login_system.login("testuser", "wrongpassword") is False

def test_user_not_registered():
    login_system = LoginSystem()
    with pytest.raises(ValueError):
        login_system.login("nonexistentuser", "testpassword")