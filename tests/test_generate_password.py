import pytest
from main import generate_password

def test_generate_password_length():
    password = generate_password(10, False)
    assert len(password) == 10

def test_generate_password_with_special_chars():
    password = generate_password(10, True)
    assert any(char in string.punctuation for char in password)

def test_generate_password_no_special_chars():
    password = generate_password(10, False)
    assert not any(char in string.punctuation for char in password)

def test_generate_password_min_length():
    with pytest.raises(ValueError):
        generate_password(0, False)

def test_generate_password_max_length():
    password = generate_password(100, True)
    assert len(password) == 100