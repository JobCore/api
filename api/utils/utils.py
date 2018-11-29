from math import radians, cos, sin, asin, sqrt

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

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return km