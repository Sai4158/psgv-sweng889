from candidate import rectangle_area

def test_area():
    assert rectangle_area(3, 4) == 12

def test_zero():
    assert rectangle_area(0, 4) == 0
