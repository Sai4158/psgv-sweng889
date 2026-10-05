from candidate import fahrenheit

def test_freezing():
    assert fahrenheit(0) == 32

def test_boiling():
    assert fahrenheit(100) == 212

def test_negative():
    assert fahrenheit(-40) == -40
