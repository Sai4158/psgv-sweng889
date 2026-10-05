import pytest
from candidate import parse_quantity

def test_valid():
    assert parse_quantity("12") == 12

def test_invalid():
    with pytest.raises(ValueError):
        parse_quantity("twelve")
