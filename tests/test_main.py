import pytest
from main import main_function

def test_main_function():
    assert main_function(1, 2) == 3
    assert main_function(5, 3) == 8
    assert main_function(0, 0) == 0

def test_main_function_with_negative_numbers():
    assert main_function(-1, -2) == -3
    assert main_function(-5, -3) == -8

def test_main_function_with_zero():
    assert main_function(0, 5) == 5
    assert main_function(5, 0) == 5

def test_main_function_with_large_numbers():
    assert main_function(123456789, 987654321) == 1111111110

def test_main_function_with_zero_and_negative():
    assert main_function(0, -5) == -5
    assert main_function(-5, 0) == -5

def test_main_function_with_same_numbers():
    assert main_function(10, 10) == 20