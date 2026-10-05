def average(nums):
    if not nums:
        raise ValueError("An average requires at least one value.")
    return sum(nums) / len(nums)
