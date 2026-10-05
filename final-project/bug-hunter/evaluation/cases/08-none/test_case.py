from candidate import display_name

def test_none():
    assert display_name(None) == "Guest"

def test_blank():
    assert display_name(" ") == "Guest"

def test_name():
    assert display_name(" Avery ") == "Avery"
