import pytest
from main import Calculator

def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_subtract():
    calc = Calculator()
    assert calc.subtract(5, 3) == 2

def test_multiply():
    calc = Calculator()
    assert calc.multiply(2, 3) == 6

def test_divide():
    calc = Calculator()
    with pytest.raises(ZeroDivisionError):
        calc.divide(4, 0)

def test_divide_result():
    calc = Calculator()
    assert calc.divide(8, 2) == 4

def test_power():
    calc = Calculator()
    assert calc.power(2, 3) == 8

def test_square_root():
    calc = Calculator()
    assert calc.square_root(16) == 4

def test_square_root_negative():
    calc = Calculator()
    with pytest.raises(ValueError):
        calc.square_root(-1)