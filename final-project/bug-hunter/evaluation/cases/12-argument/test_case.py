from candidate import round_money

def test_two_decimal_places():
    assert round_money(12.346) == 12.35

def test_zero():
    assert round_money(0) == 0
