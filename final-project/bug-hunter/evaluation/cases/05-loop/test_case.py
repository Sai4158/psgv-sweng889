from candidate import count_evens

def test_first_even():
    assert count_evens([2, 3, 4]) == 2

def test_single_even():
    assert count_evens([2]) == 1

def test_empty():
    assert count_evens([]) == 0
