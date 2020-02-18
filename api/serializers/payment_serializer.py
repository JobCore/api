import datetime
import decimal
import itertools

from django.db.models import Q, Sum
from django.utils import timezone

from rest_framework import serializers

from api.models import (Badge, BankAccount, Clockin, Employee, EmployeePayment, Employer, EmployerDeduction,
                        PaymentTransaction, PayrollPeriod, PayrollPeriodPayment, Position, PreDefinedDeduction, Profile,
                        Shift, User, Venue, APPROVED, PENDING)
from api.utils.loggers import log_debug
from api.utils.utils import nearest_weekday

DATE_FORMAT = '%Y-%m-%d'

#
# NESTED
#


class ProfileGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('picture','id')


class UserGetSmallSerializer(serializers.ModelSerializer):
    profile = ProfileGetSmallSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile')


class PositionGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('title', 'id')


class VenueGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ('title', 'id')


class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ('title', 'id', 'picture', 'rating', 'total_ratings')


class ShiftGetSmallSerializer(serializers.ModelSerializer):
    position = PositionGetSmallSerializer(read_only=True)
    venue = VenueGetSmallSerializer(read_only=True)

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


class PayrollPeriodGetTinySerializer(serializers.ModelSerializer):
    #payments = PayrollPeriodPaymentGetSerializer(read_only=True, many=True)
    class Meta:
        model = PayrollPeriod
        fields = (
            'id',
            'status',
            'starting_at',
            'ending_at',
            'total_payments'
        )

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
    #payments = PayrollPeriodPaymentGetSerializer(read_only=True, many=True)
    payments = serializers.SerializerMethodField()
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
            'total_payments',
            'payments')

    def get_payments(self, instance):
        _payments = instance.payments.all().order_by('shift__starting_at')
        return PayrollPeriodPaymentGetSerializer(_payments, many=True).data


class RoundingDecimalField(serializers.DecimalField):
    def validate_precision(self, value):
        return value


class PayrollPeriodPaymentPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = PayrollPeriodPayment
        exclude = ()

    def validate(self, data):

        data = super(PayrollPeriodPaymentPostSerializer, self).validate(data)

        if 'shift' not in data:
            raise serializers.ValidationError('Missing shift on the Payment')

        if 'regular_hours' not in data:
            raise serializers.ValidationError('You need to specify how many regular_hours were worked')

        if 'over_time' not in data:
            raise serializers.ValidationError('You need to specify how many over_time was worked')

        if 'breaktime_minutes' not in data:
            raise serializers.ValidationError('You need to specify how many breaktime_minutes was worked')

        # previous_payment = PayrollPeriodPayment.objects.filter(employee__id=data['employee'].id, shift__id=data['shift'].id).first()
        # if previous_payment is not None:
        #     raise serializers.ValidationError('There is already a payment for this talent and shift')

        return data

    def create(self, validated_data):

        params = validated_data.copy()
        params['hourly_rate'] = validated_data['shift'].minimum_hourly_rate
        params['total_amount'] = params['hourly_rate'] * (decimal.Decimal(params['regular_hours']) + decimal.Decimal(params['over_time']) - decimal.Decimal(params['breaktime_minutes'] / 60))
        payment = super(PayrollPeriodPaymentPostSerializer, self).create(params)

        return payment


class PayrollPeriodPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = PayrollPeriodPayment
        exclude = ()

    def validate(self, data):

        data = super(PayrollPeriodPaymentSerializer, self).validate(data)

        if self.instance.payroll_period.status != 'OPEN':
            raise serializers.ValidationError('This payroll period is not open for changes anymore')

        if 'status' not in data:
            raise serializers.ValidationError('You need to specify the status')

        return data

    def update(self, payment, validated_data):

        params = validated_data.copy()

        if 'regular_hours' in params:
            print("Summing: "+str(params['regular_hours'])+" + "+str(params['breaktime_minutes'] / 60))
            params['total_amount'] = payment.hourly_rate * (decimal.Decimal(params['regular_hours']) - decimal.Decimal(params['breaktime_minutes'] / 60))

        return super().update(payment, params)


class PayrollPeriodSerializer(serializers.ModelSerializer):

    class Meta:
        model = PayrollPeriod
        exclude = ()
        extra_kwargs = {
            'ending_at': {'read_only': True},
            'starting_at': {'read_only': True}
        }

    def update(self, instance, validated_data):
        employer_id = instance.employer_id
        for item in PayrollPeriodPayment.objects.filter(payroll_period_id=instance.id, employer_id=employer_id,
                                                        status=APPROVED).values('employee_id')\
                .annotate(total_regular_hours=Sum('regular_hours'),
                          total_over_time=Sum('over_time'),
                          gross_amount=Sum('total_amount'),
                          total_breaktime_minutes=Sum('breaktime_minutes'),
                          total_payment=Sum('total_amount')):
            # get_or_create is used to maintain idempotence
            EmployeePayment.objects.get_or_create(payroll_period=instance,
                                                  employee_id=item['employee_id'],
                                                  employer_id=employer_id,
                                                  regular_hours=item['total_regular_hours'],
                                                  over_time=item['total_over_time'],
                                                  breaktime_minutes=item['total_breaktime_minutes'],
                                                  earnings=item['total_payment'],
                                                  )
        return super().update(instance, validated_data)

    def validate(self, data):
        # don't allow to set period as FINALIZED if there is a payrollpayment with status PENDING
        if self.context['request'].method == 'PUT':
            if PayrollPeriodPayment.objects.filter(payroll_period_id=self.instance.id,
                                                   employer_id=self.instance.employer_id,
                                                   status=PENDING).exists():
                raise serializers.ValidationError('There is a Payroll Payment with status PENDING in current period')
        return super().validate(data)


class BankAccountSmallSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ('id', 'name', 'institution_name', 'account', 'account_id')


class EmployerInfoPaymentSerializer(serializers.ModelSerializer):
    """Serializer to get basic information of employer, including bank accounts"""
    bank_accounts = BankAccountSmallSerializer(source='profile_set.last.bank_accounts', many=True)

    class Meta:
        model = Employer
        fields = ('id', 'title', 'status', 'bank_accounts')


class EmployeeInfoPaymentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=30, source='user.first_name')
    last_name = serializers.CharField(max_length=150, source='user.last_name')
    bank_accounts = BankAccountSmallSerializer(source='profile_set.last.bank_accounts', many=True)

    class Meta:
        model = Employee
        fields = ('first_name', 'last_name', 'bank_accounts')


class EmployeePaymentSerializer(serializers.ModelSerializer):
    employee = EmployeeInfoPaymentSerializer()
    deduction_list = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePayment
        fields = ('id', 'employee', 'regular_hours', 'over_time', 'earnings',
                  'paid', 'payroll_period_id', 'deductions', 'deduction_list', 'amount')

    def get_deduction_list(self, instance):
        self.context['total_deductions'] = 0
        res_list = []
        for deduction in itertools.chain(PreDefinedDeduction.objects.order_by('id'),
                                         EmployerDeduction.objects.order_by('id')):
            if deduction.type == PreDefinedDeduction.PERCENTAGE_TYPE:
                amount = instance.earnings * decimal.Decimal('{:.2f}'.format(deduction.value)) / 100
            else:
                amount = decimal.Decimal('{:.2f}'.format(deduction.value))
            self.context['total_deductions'] += amount
            res_list.append({'name': deduction.name, 'amount': amount})
        return res_list

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['deductions'] = self.context['total_deductions']
        data['amount'] = instance.earnings - data['deductions']
        return data


class EmployeePaymentDataSerializer(serializers.Serializer):
    """Serializer to check received data in order to paid"""
    payment_type = serializers.ChoiceField(choices=PaymentTransaction.PAYMENT_TYPES)
    payment_data = serializers.JSONField()

    def validate_payment_data(self, dict_value):
        if self.initial_data.get('payment_type') in [PaymentTransaction.ELECT_TRANSF, PaymentTransaction.FAKE]:
            try:
                BankAccount.objects.get(id=dict_value.get('employer_bank_account_id'),
                                        user=self.context['employer_user'].profile)
            except BankAccount.DoesNotExist:
                raise serializers.ValidationError('Wrong employer bank account')
            try:
                BankAccount.objects.get(id=dict_value.get('employee_bank_account_id'),
                                        user=self.context['employee_user'].profile)
            except BankAccount.DoesNotExist:
                raise serializers.ValidationError('Wrong employee bank account')
            return dict_value
        else:
            return dict_value


class EmployeePaymentDatesSerializer(serializers.Serializer):
    """To verify parameters for searching"""
    start_date = serializers.DateField(format=DATE_FORMAT, required=False)
    end_date = serializers.DateField(format=DATE_FORMAT, required=False)
    period_id = serializers.IntegerField(required=False)

    def to_internal_value(self, data):
        new_data = data.copy()
        for key in data.keys():
            if new_data[key] == 'null':
                new_data.pop(key)
        return super().to_internal_value(new_data)

    def validate_period_id(self, value):
        try:
            period = PayrollPeriod.objects.get(id=value, employer_id=self.context['employer_id'])
        except PayrollPeriod.DoesNotExist:
            raise serializers.ValidationError('There is not PayrollPeriod')
        else:
            return value


class EmployeePaymentReportSerializer(serializers.ModelSerializer):
    class CustomPayrollPeriodSerializer(PayrollPeriodSerializer):
        class Meta:
            model = PayrollPeriod
            fields = ('id', 'starting_at', 'ending_at')

    employee = serializers.SerializerMethodField()
    payment_date = serializers.DateTimeField(format=DATE_FORMAT, source='payment_transaction.created_at')
    payment_source = serializers.SerializerMethodField()
    payroll_period = CustomPayrollPeriodSerializer()

    class Meta:
        model = EmployeePayment
        fields = ('employee', 'earnings', 'deductions', 'amount', 'payment_date', 'payment_source', 'payroll_period')

    def get_employee(self, instance):
        user = instance.employee.user
        return '{}, {}'.format(user.last_name, user.first_name)

    def get_payment_source(self, instance):
        data = instance.payment_transaction.payment_data
        try:
            bank_account = BankAccount.objects.get(stripe_bankaccount_id=data.get('sender_stripe_token'))
        except BankAccount.DoesNotExist:
            return instance.payment_transaction.payment_type
        else:
            if bank_account.institution_name:
                return bank_account.institution_name
            else:
                return instance.payment_transaction.payment_type


class EmployeePaymentDeductionReportSerializer(EmployeePaymentReportSerializer):
    deduction_amount = serializers.DecimalField(max_digits=10, decimal_places=2, source='deductions')

    class Meta:
        model = EmployeePayment
        fields = ('employee', 'deduction_amount', 'deduction_list', 'payment_date', 'payroll_period')


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

    log_debug('hooks','generate_periods -> Employer: '+employer.title)
    NOW = timezone.now()

    if employer.payroll_period_type != 'DAYS':
        raise serializers.ValidationError('The only supported period type is DAYS (for now)')

    if employer.payroll_period_starting_time is None:
        raise serializers.ValidationError('You have to setup your payroll configuration')

    weekday = employer.payroll_period_starting_time.weekday()
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
        log_debug('hooks','Last period generated until '+str(last_processed_period))
        last_period_ending_date = nearest_weekday(last_processed_period.ending_at - datetime.timedelta(days=1), weekday, fallback_direction='forward')
        last_period_ending_date = last_period_ending_date.replace(hour=h_hour, minute=m_hour, second=s_hour)
        log_debug('hooks','Will start generating from '+str(last_period_ending_date))
    else:
        last_period_ending_date = nearest_weekday(employer.created_at, weekday, fallback_direction='backward')
        log_debug('hooks','generate_periods:Employer: This is the first payroll, and the company started existing on '+str(employer.created_at))
        last_period_ending_date = (last_period_ending_date.replace(hour=h_hour, minute=m_hour, second=s_hour) - datetime.timedelta(seconds=1))
    
    #log_debug('hooks','Last period generated until '+str(last_period_ending_date))

    # the ending date will be X days later, X = employer.payroll_period_length
    end_date = last_period_ending_date + datetime.timedelta(days=employer.payroll_period_length)

    generated_periods = []
    if end_date >= NOW:
        log_debug('hooks','No new periods to generate, now is '+ str(NOW) +' we have to wait until '+str(end_date))
        return []

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
        end_date = end_date + datetime.timedelta(days=employer.payroll_period_length)

        # no lets start calculating the payaments
        try:
            all_clockins = Clockin.objects.filter(
                Q(started_at__gte=period.starting_at) & Q(started_at__lte=period.ending_at),
                shift__employer__id=employer.id
            )
            log_debug('hooks','Creating a new period for '+employer.title+' from '+str(period.starting_at)+' to '+str(period.ending_at)+ " -> "+str(len(all_clockins))+' clockins')
            total_payments = 0
            for clockin in all_clockins:
                # the payment needs to be inside the payment period
                starting_time = clockin.started_at if clockin.started_at > period.starting_at else period.starting_at
                
                ending_time = clockin.ended_at if clockin.ended_at is not None and clockin.ended_at < period.ending_at else period.ending_at
                clocked_hours = (ending_time - starting_time).total_seconds() / 3600 if clockin.ended_at is not None else None

                # the projected payment varies depending on the payment period
                projected_starting_time = clockin.shift.starting_at
                projected_ending_time = clockin.shift.ending_at
                projected_hours = (projected_ending_time - projected_starting_time).total_seconds() / 3600

                log_debug('hooks','Projected hours '+str(projected_hours))
                overtime = 0
                regular_hours = 0
                if clocked_hours is not None and (clocked_hours > 40):
                    overtime = clocked_hours - 40
                    regular_hours = 40
                else:
                    regular_hours = clocked_hours
                    overtime = 0


                payment = PayrollPeriodPayment(
                    payroll_period=period,
                    employee=clockin.employee,
                    employer=employer,
                    shift=clockin.shift,
                    clockin=clockin,
                    regular_hours= regular_hours,
                    over_time=overtime,
                    hourly_rate=clockin.shift.minimum_hourly_rate,
                    total_amount= (decimal.Decimal(regular_hours) * decimal.Decimal(clockin.shift.minimum_hourly_rate)) + (decimal.Decimal(overtime) * decimal.Decimal(1.5) * decimal.Decimal(clockin.shift.minimum_hourly_rate)),
                    splited_payment=False if clockin.ended_at is None or (clockin.started_at == starting_time and ending_time == clockin.ended_at) else True
                )
                payment.save()
                total_payments = total_payments + 1

            period.total_payments = total_payments
            period.save()
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
