import pytest
from main import main_function

def test_main_function():
    assert main_function(1, 2) == 3
    assert main_function(3, 4) == 7
    assert main_function(5, 0) == 5

def test_main_function_with_negative_numbers():
    assert main_function(-1, -2) == -3
    assert main_function(-3, -4) == -7
    assert main_function(-5, 0) == -5

def test_main_function_with_zero():
    assert main_function(0, 0) == 0
    assert main_function(0, 5) == 5
    assert main_function(5, 0) == 5

def test_main_function_with_large_numbers():
    assert main_function(1000000, 2000000) == 3000000
    assert main_function(1000000000, 2000000000) == 3000000000