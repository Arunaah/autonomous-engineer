import pytest
from main import main_function

def test_main_function():
    assert main_function(3, 4) == 7
    assert main_function(5, 2) == 7
    assert main_function(0, 0) == 0
    assert main_function(-1, 1) == 0
    with pytest.raises(ValueError):
        main_function('a', 1)
        main_function(1, 'b')
        main_function('a', 'b')