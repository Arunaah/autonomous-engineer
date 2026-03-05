import pytest
from main import main_function

def test_main_function():
    assert main_function(1, 2) == 3
    assert main_function(5, 3) == 8
    assert main_function(-1, 0) == -1

def test_main_function_with_zero():
    assert main_function(0, 0) == 0

def test_main_function_with_negative_numbers():
    assert main_function(-2, -3) == -5

def test_main_function_with_large_numbers():
    assert main_function(1000000, 2000000) == 3000000