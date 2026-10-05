from candidate import is_weekend

def test_saturday():
    assert is_weekend("Saturday") is True

def test_sunday():
    assert is_weekend("Sunday") is True

def test_weekday():
    assert is_weekend("Monday") is False
