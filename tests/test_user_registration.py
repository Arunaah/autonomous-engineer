import pytest
from user_registration import UserRegistration

def test_is_valid_email():
    reg = UserRegistration()
    assert reg.is_valid_email("test@example.com") == True
    assert reg.is_valid_email("test.example.com") == False
    assert reg.is_valid_email("test@example.co.uk") == True

def test_is_valid_username():
    reg = UserRegistration()
    assert reg.is_valid_username("user123") == True
    assert reg.is_valid_username("u") == False
    assert reg.is_valid_username("user1234567890123456") == False

def test_is_valid_password():
    reg = UserRegistration()
    assert reg.is_valid_password("Password123") == True
    assert reg.is_valid_password("pass") == False
    assert reg.is_valid_password("Password1234") == False

def test_register_user():
    reg = UserRegistration()
    assert reg.register_user("user1", "test@example.com", "Password123") == "User registered successfully"
    assert reg.register_user("user1", "test@example.com", "Password123") == "Username already exists"
    assert reg.register_user("user2", "test@example.com", "Password123") == "Email already in use"

def test_get_user_email():
    reg = UserRegistration()
    reg.register_user("user1", "test@example.com", "Password123")
    assert reg.get_user_email("user1") == "test@example.com"
    assert reg.get_user_email("user2") == "User not found"

def test_unregister_user():
    reg = UserRegistration()
    reg.register_user("user1", "test@example.com", "Password123")
    assert reg.unregister_user("user1") == "User unregistered successfully"
    assert reg.unregister_user("user1") == "User not found"