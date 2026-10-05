import pytest
from candidate import average

def test_all_values():
    assert average([2, 4, 6]) == pytest.approx(4)

def test_single_value():
    assert average([7]) == 7

def test_empty_input():
    with pytest.raises(ValueError):
        average([])
