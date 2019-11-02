from math import radians, cos, sin, asin, sqrt
import datetime
from django.utils.timezone import is_aware, make_aware
from django.utils.dateparse import parse_datetime


def custom_index(array, compare_function):
    for i, v in enumerate(array):
        if compare_function(v):
            return i
    return None


def in_choices(choice, CHOICES):
    is_present = False
    for status, description in CHOICES:
        if status == choice:
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
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km


def get_aware_datetime(date_str):
    ret = parse_datetime(date_str)
    if not is_aware(ret):
        ret = make_aware(ret)
    return ret

def nearest_weekday(d, weekday, fallback_direction='forward'):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        if fallback_direction == 'backward':
            days_ahead -= 7
        else:
            days_ahead += 7
    new_date = d + datetime.timedelta(days_ahead)
    return new_date