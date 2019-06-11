import datetime
import itertools
import decimal
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from api.models import Clockin, Employer, Shift, Position, Employee, PayrollPeriod, PayrollPeriodPayment, User, Badge, Profile
from api.utils.loggers import log_debug
#
# NESTED
#

class ProfileGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('picture',)

class UserGetSmallSerializer(serializers.ModelSerializer):
    profile = ProfileGetSmallSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile')


class PositionGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('title', 'id')


class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('title', 'id')


class ShiftGetSmallSerializer(serializers.ModelSerializer):
    position = PositionGetSmallSerializer(read_only=True)

    class Meta:
        model = Shift
        exclude = (
            'maximum_allowed_employees',
            'minimum_allowed_rating',
            'allowed_from_list',
            'required_badges',
            'candidates',
            'employees',
            'rating',
            'application_restriction',
            'updated_at')

class BadgeGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ('title', 'id')

class EmployeeGetTinySerializer(serializers.ModelSerializer):
    user = UserGetSmallSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = ('user', 'id')

class EmployeeGetSerializer(serializers.ModelSerializer):
    user = UserGetSmallSerializer(read_only=True)
    badges = BadgeGetSmallSerializer(read_only=True, many=True)


    class Meta:
        model = Employee
        fields = ('user', 'id', 'badges')


class ClockinGetSerializer(serializers.ModelSerializer):
    shift = ShiftGetSmallSerializer()
    employee = EmployeeGetTinySerializer()
    #author = serializers.IntegerField()

    class Meta:
        model = Clockin
        exclude = ()

class ClockinGetSmallSerializer(serializers.ModelSerializer):

    class Meta:
        model = Clockin
        exclude = ('shift', 'employee')


class ShiftGetSmallSerializer(serializers.ModelSerializer):
    position = PositionGetSmallSerializer(read_only=True)

    class Meta:
        model = Shift
        fields = ('id', 'position', 'starting_at', 'ending_at')

#
# MAIN
#


class PayrollPeriodPaymentGetSerializer(serializers.ModelSerializer):
    employee = EmployeeGetSerializer(read_only=True)
    employer = EmployerGetSmallSerializer(read_only=True)
    shift = ShiftGetSmallSerializer(read_only=True)
    clockin = ClockinGetSmallSerializer(read_only=True)

    class Meta:
        model = PayrollPeriodPayment
        exclude = ()


class PayrollPeriodGetSerializer(serializers.ModelSerializer):
    payments = PayrollPeriodPaymentGetSerializer(read_only=True, many=True)
    employer = EmployerGetSmallSerializer(read_only=True)

    class Meta:
        model = PayrollPeriod
        fields = (
            'id',
            'employer',
            'length',
            'length_type',
            'status',
            'starting_at',
            'ending_at',
            'created_at',
            'payments')


class PayrollPeriodPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriodPayment
        exclude = ()


class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        exclude = ()


def get_projected_payments(
        employer_id,
        start_date,
        talent_id=None,
        period_length=7,
        period_type='DAYS'):

    if period_type != 'DAYS':
        raise serializers.ValidationError(
            'The only supported period type is DAYS')

    end_date = start_date + timezone.timedelta(days=period_length)
    normal_clockins = Clockin.objects.filter(
        shift__employer__id=employer_id,
        ended_at__lte=end_date,
        started_at__gte=start_date)
    if talent_id is not None:
        normal_clockins = normal_clockins.filter(employee__id=talent_id)
    grouped = itertools.groupby(
        normal_clockins,
        lambda record: record.started_at.strftime("%Y-%m-%d"))
    clockins_by_day = [{"date": day, "clockins": list(
        clockins_this_day)} for day, clockins_this_day in grouped]

    result = {}
    for i in range(period_length):
        result[(start_date + timezone.timedelta(days=i)).strftime("%Y-%m-%d")] = {}

    for date in clockins_by_day:
        result[date['date']] = {"clockins": [ClockinGetSerializer(
            clockin).data for clockin in date['clockins']], "between_periods": []}

    clockins_in_between_periods = Clockin.objects.filter(
        ended_at__gte=end_date, started_at__lte=end_date)
    if talent_id is not None:
        normal_clockins = clockins_in_between_periods.filter(
            employee__id=talent_id)
    for clockin in clockins_in_between_periods:
        date = clockin.started_at.strftime("%Y-%m-%d")
        if date not in result:
            result[date] = {
                "clockins": [],
                "between_periods": []
            }
        result[date]["between_periods"].append(
            ClockinGetSerializer(clockin).data)

    return result


def generate_periods_and_payments(employer, generate_since=None):

    log_debug('hooks','generate_periods_and_payments:Employer: '+employer.title)
    NOW = timezone.now()

    if employer.payroll_period_type != 'DAYS':
        raise serializers.ValidationError(
            'The only supported period type is DAYS (for now)')

    h_hour = employer.payroll_period_starting_time.hour
    m_hour = employer.payroll_period_starting_time.minute
    s_hour = employer.payroll_period_starting_time.second
    last_processed_period = PayrollPeriod.objects.filter(
        employer__id=employer.id).order_by('starting_at').last()

    # if there is a previous period we generate from there, if not we generate
    # since the company joined jobcore
    #
    last_period_ending_date = None
    if last_processed_period is not None:
        last_period_ending_date = last_processed_period.ending_at
    else:
        last_period_ending_date = (employer.created_at.replace(hour=h_hour, minute=m_hour, second=s_hour) - datetime.timedelta(seconds=1))

    log_debug('hooks','generate_periods_and_payments:Employer:'+employer.title+' from '+str(last_period_ending_date))

    # the ending date will be X days later, X = employer.payroll_period_length
    end_date = last_period_ending_date + \
        datetime.timedelta(days=employer.payroll_period_length)

    generated_periods = []
    while end_date < NOW:
        start_date = end_date - \
            datetime.timedelta(
                days=employer.payroll_period_length) + datetime.timedelta(seconds=1)
        period = PayrollPeriod(
            starting_at=start_date,
            ending_at=end_date,
            employer=employer,
            length=employer.payroll_period_length,
            length_type=employer.payroll_period_type
        )
        period.save()

        # move the end_date forward to make sture the loop stops eventually
        end_date = end_date + \
            datetime.timedelta(days=employer.payroll_period_length)

        # no lets start calculating the payaments
        try:
            all_clockins = Clockin.objects.filter(
                Q(started_at__gte=period.starting_at) & Q(started_at__lte=period.ending_at),
                shift__employer__id=employer.id
            )
            log_debug('hooks','Creating a new period for '+employer.title+' from '+str(period.starting_at)+' to '+str(period.ending_at)+ " -> "+str(len(all_clockins))+' clockins')
            for clockin in all_clockins:
                # the payment needs to be inside the payment period
                starting_time = clockin.started_at if clockin.started_at > period.starting_at else period.starting_at
                ending_time = clockin.ended_at if clockin.ended_at < period.ending_at else period.ending_at
                total_hours = (
                    ending_time - starting_time).total_seconds() / 3600

                # the projected payment varies depending on the payment period
                projected_starting_time = clockin.shift.starting_at
                projected_ending_time = clockin.shift.ending_at
                projected_hours = (projected_ending_time - projected_starting_time).total_seconds() / 3600

                log_debug('hooks','Projected hours '+str(projected_hours))
                overtime = 0
                if(total_hours > projected_hours):
                    overtime = total_hours - projected_hours

                payment = PayrollPeriodPayment(
                    payroll_period=period,
                    employee=clockin.employee,
                    employer=employer,
                    shift=clockin.shift,
                    clockin=clockin,
                    regular_hours=total_hours,
                    over_time=overtime,
                    hourly_rate=clockin.shift.minimum_hourly_rate,
                    total_amount=clockin.shift.minimum_hourly_rate *
                    decimal.Decimal(total_hours),
                    splited_payment=False if clockin.started_at == starting_time and ending_time == clockin.ended_at else True
                )
                payment.save()

            generated_periods.append(period)

        except Exception as e:
            PayrollPeriodPayment.objects.filter(payroll_period__id=period.id).delete()
            generated_periods = []
            period.delete()
            raise e

    return generated_periods


def get_employee_payments(
        talent_id=None,
        start_date=None,
        employer_id=None,
        period_length=7,
        period_type='DAYS'):

    if period_type != 'DAYS':
        raise serializers.ValidationError(
            'The only supported period type is DAYS for now')
    if talent_id is None:
        raise serializers.ValidationError('You need to specify the talent id')
    if start_date is None:
        raise serializers.ValidationError(
            'You need to specify the starting date')

    end_date = start_date + timezone.timedelta(days=period_length)
    payments = PayrollPeriodPayment.objects.filter(
        employee=talent_id, payroll_period__started_at__gte=start_date)

    if employer_id is not None:
        payments = payments.filter(payroll_period__employer__id=employer_id)
    elif qShift:
        payments = payments.filter(shift__id=qShift)

    return result
