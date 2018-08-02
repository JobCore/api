def custom_index(array, compare_function):
    for i, v in enumerate(array):
        if compare_function(v):
            return i
    return None