import pytz
from datetime import datetime, timedelta
from api.models import AvailabilityBlock


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def create_default_availablity(employee):

    today = datetime.now(pytz.utc)

    AvailabilityBlock.objects.filter(employee=employee).delete()
    #   0 = Monday
    AvailabilityBlock.objects.create(
        employee=employee, starting_at=next_weekday(
            today, 0), ending_at=next_weekday(
            today, 0), allday=True, recurrent=True, recurrency_type='WEEKLY')
    AvailabilityBlock.objects.create(
        employee=employee, starting_at=next_weekday(
            today, 1), ending_at=next_weekday(
            today, 1), allday=True, recurrent=True, recurrency_type='WEEKLY')
    AvailabilityBlock.objects.create(
        employee=employee, starting_at=next_weekday(
            today, 2), ending_at=next_weekday(
            today, 2), allday=True, recurrent=True, recurrency_type='WEEKLY')
    AvailabilityBlock.objects.create(
        employee=employee, starting_at=next_weekday(
            today, 3), ending_at=next_weekday(
            today, 3), allday=True, recurrent=True, recurrency_type='WEEKLY')
    AvailabilityBlock.objects.create(
        employee=employee, starting_at=next_weekday(
            today, 4), ending_at=next_weekday(
            today, 4), allday=True, recurrent=True, recurrency_type='WEEKLY')
    AvailabilityBlock.objects.create(
        employee=employee, starting_at=next_weekday(
            today, 5), ending_at=next_weekday(
            today, 5), allday=True, recurrent=True, recurrency_type='WEEKLY')
    AvailabilityBlock.objects.create(
        employee=employee, starting_at=next_weekday(
            today, 6), ending_at=next_weekday(
            today, 6), allday=True, recurrent=True, recurrency_type='WEEKLY')
