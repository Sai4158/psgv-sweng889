def parse_quantity(text):
    try:
        return int(text)
    except Exception:
        return 0
