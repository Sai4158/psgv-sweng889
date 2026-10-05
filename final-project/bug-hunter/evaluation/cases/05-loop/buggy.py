def count_evens(values):
    count = 0
    for index in range(1, len(values)):
        if values[index] % 2 == 0:
            count += 1
    return count
