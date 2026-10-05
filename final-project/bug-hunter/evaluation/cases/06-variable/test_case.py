from candidate import full_name

def test_distinct_names():
    assert full_name("Sai", "Rangineeni") == "Sai Rangineeni"

def test_first_only():
    assert full_name("Avery", "") == "Avery"
