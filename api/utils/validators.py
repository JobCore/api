def in_choices(choice, CHOICES):
    is_present = False
    for status, description in CHOICES:
        if description == choice:
            is_present = True
    return is_present