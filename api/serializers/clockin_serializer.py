import logging
from api.serializers import shift_serializer, employee_serializer
from rest_framework import serializers
from api.models import Clockin
from api.utils.utils import haversine
from django.utils import timezone
import datetime

NOW = timezone.now()

logger = logging.getLogger('jobcore:clockin_serializer:')


class ClockinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clockin
        exclude = ()

    def _ensure_distance_threshold(self, currentPos, shift, threshold=0.1):
        venue = shift.venue
        talent_lat, talent_lon = currentPos
        shift_lat, shift_lon = [venue.latitude, venue.longitude]

        distance = haversine(
            talent_lat, talent_lon,
            shift_lat, shift_lon
        )

        if distance > threshold:
            raise serializers.ValidationError(
                "You need to be {} miles near {} to clock in/out. Right now you"
                "are at {} miles".format(threshold, venue.title, distance)
            )

    def _ensure_time_threshold(self, currentTime, start, threshold=0):
        '''
        @deprecated
        '''
        delta = datetime.timedelta(minutes=threshold)

        minTime, maxTime = start - delta, start + delta

        if currentTime < minTime:
            raise serializers.ValidationError('You cannot clock in/out before shift starting time')  # NOQA

        if currentTime > maxTime:
            raise serializers.ValidationError('You cannot clock in/out after shift starting time')  # NOQA

    def _validate_clockin(self, data):
        shift = data['shift']

        if 'latitude_in' not in data or 'longitude_in' not in data:
            raise serializers.ValidationError(
                "You need to specify latitude_in, longitude_in")

        currentPos = (data['latitude_in'], data['longitude_in'])
        self._ensure_distance_threshold(currentPos, shift)

        # if trying to clock in after the Shift ended
        if data['started_at'] > shift.ending_at:
            raise serializers.ValidationError("You can't Clock in after the Shift ending time")  # NOQA

        last_clockin_for_shift = Clockin.objects.filter(shift__id=shift.id).last()

        # The employee first clockin for this Shift
        if last_clockin_for_shift is None:
            delta = datetime.timedelta(minutes=shift.employer.maximum_clockin_delta_minutes)
            logger.debug('started at: %s' % data["started_at"])
            logger.debug('shift.starting_at: %s' % shift.starting_at)
            logger.debug('delta: %s' % delta)

            if data['started_at'] > shift.starting_at + delta:
                raise serializers.ValidationError("You can't Clock in %s minutes after the Shift has started" % delta)

            if data['started_at'] < shift.starting_at - delta:
                raise serializers.ValidationError("You can't Clock %s minutes before the Shift has started" % delta)

        elif last_clockin_for_shift.ended_at is None:
            raise serializers.ValidationError("You can't Clock in with a pending Clock out")

    def _validate_clockout(self, data):
        shift = data['shift']
        delta = datetime.timedelta(minutes=shift.employer.maximum_clockout_delay_minutes)
        now = timezone.now()

        if 'latitude_out' not in data or 'longitude_out' not in data:
            raise serializers.ValidationError(
                "You need to specify latitude_out, longitude_out")

        currentPos = (data['latitude_out'], data['longitude_out'])
        self._ensure_distance_threshold(currentPos, shift)

        # the Shift already ended
        if now > shift.ending_at + delta:
            raise serializers.ValidationError(
                "You can't Clock out after the Shift has ended. The System clock you out automatically")

        some_lockin_for_shift = Clockin.objects.filter(shift__id=shift.id, ended_at=None).first()
        # There is no Clock in record with out a Clock out
        if some_lockin_for_shift is None:
            raise serializers.ValidationError("You can't Clock out if you haven't Clocked in")

    def validate(self, data):

        if 'started_at' in data and 'ended_at' in data:
            raise serializers.ValidationError(
                "You cannot clock in and out at the same time, you need to specify only the started or ended time, but not both at the same time")  # NOQA

        if 'started_at' not in data and 'ended_at' not in data:
            raise serializers.ValidationError(
                "You need to specify the started or ended time")

        shift = data['shift']
        employee = data['employee']

        if not shift.employees.filter(id=employee.id).exists():
            raise serializers.ValidationError(
                "You cannot clock in/out to a shift that you haven't applied.")

        if 'started_at' in data:
            self._validate_clockin(data)
        elif 'ended_at' in data:
            self._validate_clockout(data)

        return data


class ClockinGetSerializer(serializers.ModelSerializer):
    shift = shift_serializer.ShiftGetSmallSerializer()
    employee = employee_serializer.EmployeeGetSmallSerializer()

    class Meta:
        model = Clockin
        exclude = ()


class ClockinPayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clockin
        exclude = ()

    def validate(self, data):
        if 'started_at' not in data and 'ended_at' not in data:
            raise serializers.ValidationError(
                "You need to specify the started or ended time")

        return data


def validate_clock_in(
        now,
        started_at,
        ended_at,
        maximum_clockin_delta_minutes=None,
        is_first_clockin=True):
    if now > ended_at:
        raise ValueError("You can't Clock In after the Shift ending time")

    if maximum_clockin_delta_minutes is None:
        if now < started_at:
            raise ValueError(
                "You can't Clock In before the Shift starting time")
        return

    # Delta exists
    if is_first_clockin:
        delta = datetime.timedelta(minutes=maximum_clockin_delta_minutes)
        if now < started_at - delta:
            raise ValueError(
                "You can only clock in " +
                str(maximum_clockin_delta_minutes) +
                " min before the Shift starting time")

        if now > started_at + delta:
            raise ValueError(
                "You can only clock in " +
                str(maximum_clockin_delta_minutes) +
                " min after the Shift starting time")
