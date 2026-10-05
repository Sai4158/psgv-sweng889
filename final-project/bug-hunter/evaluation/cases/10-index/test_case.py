import pytest
from candidate import last_item

def test_last():
    assert last_item([1, 2, 3]) == 3

def test_single():
    assert last_item([9]) == 9

def test_empty():
    with pytest.raises(ValueError):
        last_item([])
