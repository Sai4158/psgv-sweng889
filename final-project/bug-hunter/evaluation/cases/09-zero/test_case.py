from candidate import success_rate

def test_empty():
    assert success_rate(0, 0) == 0.0

def test_half():
    assert success_rate(2, 4) == 0.5
