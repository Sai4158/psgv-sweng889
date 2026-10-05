def last_item(values):
    if not values:
        raise ValueError("Sequence is empty.")
    return values[-1]
