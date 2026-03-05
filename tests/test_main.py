import pytest
from main import main_function

def test_main_function():
    assert main_function(1, 2) == 3
    assert main_function(5, 3) == 8
    assert main_function(-1, 0) == -1

def test_main_function_with_strings():
    with pytest.raises(TypeError):
        main_function("string", "another string")

def test_main_function_with_invalid_types():
    with pytest.raises(TypeError):
        main_function([1, 2], [3, 4])