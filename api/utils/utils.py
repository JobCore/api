def custom_index(array, compare_function):
    for i, v in enumerate(array):
        if compare_function(v):
            return i
    return None
    
def in_choices(choice, CHOICES):
    is_present = False
    for status, description in CHOICES:
        if status == qStatus:
            is_present = True
    return is_present
