from rest_framework import serializers
import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from api.serializers import profile_serializer
from api.utils import notifier
from api.models import (
    Badge, JobCoreInvite, Rate, Employer, Profile,
    Shift, Employee, User, AvailabilityBlock, City,
    AppVersion, SubscriptionPlan, EmployerSubscription
)

from api.serializers.position_serializer import PositionSmallSerializer


class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        exclude = ()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        exclude = ()

class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ('title', 'id')


class ShiftGetSmallSerializer(serializers.ModelSerializer):
    position = PositionSmallSerializer(read_only=True)
    employer = EmployerGetSmallSerializer(read_only=True)

    class Meta:
        model = Shift
        fields = (
            'id',
            'position',
            'employer',
            'minimum_hourly_rate',
            'starting_at',
            'ending_at')


class RatingGetSerializer(serializers.ModelSerializer):
    shift = ShiftGetSmallSerializer(read_only=True)

    class Meta:
        model = Rate
        exclude = ()


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        exclude = ()


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        exclude = ()


# reset the employee badges

        
class EmployerSubscriptionPost(serializers.ModelSerializer):
    due_at = serializers.DateTimeField(required=False)

    class Meta:
        model = EmployerSubscription
        exclude = ()

    def validate(self, data):

        if 'employer' not in data or data['employer'] is None or data['employer'].id == 0:
            raise serializers.ValidationError('Invalid employer')

        validated_data = super().validate(data)

        current = EmployerSubscription.objects.filter(status='ACTIVE', employer=data['employer'].id).first()
        if current is not None and current.subscription.id == data['subscription'].id:
            raise serializers.ValidationError('That subscription is already active')

        return validated_data

    def create(self, validated_data):

        NOW = timezone.now()
        EmployerSubscription.objects.filter(status='ACTIVE', employer=validated_data['employer'].id).update(status='CANCELLED', updated_at=NOW)

        params = validated_data.copy()
        if 'payment_mode' not in validated_data:
            params['payment_mode'] = 'MONTHLY'

        if params['payment_mode'] == 'YEARLY':
            params['due_at'] = NOW +  + datetime.timedelta(years=1)
        else:
            params['due_at'] = NOW + relativedelta(months=1)

        subs = super().create(params)

        return subs

class EmployeeBadgeSerializer(serializers.Serializer):
    badges = serializers.PrimaryKeyRelatedField(
        queryset=Badge.objects.all(),
        many=True,
        required=True)
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        required=True
    )

    def validate_badges(self, value):
        if len(value) == 0:
            raise serializers.ValidationError('You need to specify the badges')
        return value

    def create(self, validated_data):
        employee = validated_data['employee']
        employee.badges.all().delete()
        employee.badges.add(*validated_data['badges'])
        return validated_data


class JobCoreInviteGetSerializer(serializers.ModelSerializer):
    sender = profile_serializer.ProfileGetSerializer()

    class Meta:
        model = JobCoreInvite
        exclude = ()


class JobCoreInvitePostSerializer(serializers.ModelSerializer):
    include_sms = serializers.BooleanField(default=False, write_only=True)
    employer_role = serializers.CharField(default='', write_only=True)

    def validate(self, data):
        print(data)
        if not data.get('email'):
            raise serializers.ValidationError('invalid payload')
   
        user = User.objects.filter(email=data["email"]).first()

        if 'status' in data and data['status'] == "COMPANY":
            data["user"] = user
        else:
            if user is not None:
                profile = Profile.objects.filter(user=user).first()
                if profile is not None:
                    print(profile.employer)
                    # if profile.employer is None:
                    raise serializers.ValidationError("The user is already registered in jobcore")
        
         
       

        try:
            sender = self.context['request'].user.profile.id
            JobCoreInvite.objects.get(
                sender=sender,
                status='ACCEPTED',
                email=data["email"]
            )

            raise serializers.ValidationError(
                "User with this email has already accepted an invite")
        except JobCoreInvite.DoesNotExist:
            pass

        return data

    def create(self, validated_data):
        # TODO: send email message not working
        # is_jobcore_employer = validated_data.pop('is_jobcore_employer', True)
        # user = User.objects.filter(email=validated_data["email"]).first()
        # if user is not None:
        #     profile = Profile.objects.filter(user=user).first()
        #     if profile is not None:
        #         if profile.employer is not None:
        #             is_jobcore_employer = True

        employer_role = validated_data.pop('employer_role', '')
        include_sms = validated_data.pop('include_sms', False)

        invite = JobCoreInvite(**validated_data)
        invite.save()
        # notifier.notify_jobcore_invite(invite, include_sms=include_sms, is_jobcore_employer=is_jobcore_employer)
        notifier.notify_jobcore_invite(invite, include_sms=include_sms, employer_role=employer_role)

        return invite

    def update(self, invite, validated_data):
        invite = super(JobCoreInvitePostSerializer, self).update(invite, validated_data)
        if invite.status == "COMPANY":
            notifier.notify_company_invite_confirmation( user=validated_data["user"], employer=invite.employer, employer_role=invite.employer_role)
        else:
            notifier.notify_jobcore_invite(invite)

        return invite

    class Meta:
        model = JobCoreInvite
        exclude = ()


class AvailabilityBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBlock
        exclude = ()

    def force_recurrency(self, data):
        if not data.get('recurrency_type'):
            raise serializers.ValidationError('Missing recurrency type')

    def validate(self, data):
        if AvailabilityBlock.objects.filter(employee_id=self.context['request'].user.profile.employee.id).count() == 7:
            raise serializers.ValidationError('Max 7 blocks are valid')

        if 'allday' in data and data.get('allday'):
            return data

        if 'starting_at' not in data:
            raise serializers.ValidationError('No initial date/time specified on the availability block')
        if 'ending_at' not in data:
            raise serializers.ValidationError('No final date/time specified on the availability block')

        start = data['starting_at']
        end = data['ending_at']

        if start > end:
            raise serializers.ValidationError('Invalid availability range')

        if (end - start).days > 0:
            raise serializers.ValidationError('Invalid availability rage')

        if AvailabilityBlock.objects.filter(
                employee_id=self.context['request'].user.profile.employee.id,
                starting_at__day=start.day,
                starting_at__month=start.month,
                starting_at__year=start.year,
                starting_at__hour=start.hour,
                starting_at__minute=start.minute,
                ending_at__day=end.day,
                ending_at__month=end.month,
                ending_at__year=end.year,
                ending_at__hour=end.hour,
                ending_at__minute=end.minute).exists():
            raise serializers.ValidationError('Duplicated block')

        if 'recurrency_type' not in data or 'recurrent' not in data:
            raise serializers.ValidationError('Missing recurrent or recurrency_type')
        else:
            self.force_recurrency(data)

        # Resulta que datetime.isoweekday() retorna el dia de la semana
        # siendo lunes = 1 y domingo = 7
        #
        # pero el lookup de django __week_day interpreta la semana como
        # domingo = 1 y sabado = 7
        # con un poquito de juego matematico, resolvemos el problema

        days = {
            "1": "Sunday",
            "2": "Monday",
            "3": "Tuesday",
            "4": "Wednesday",
            "5": "Thursday",
            "6": "Friday",
            "7": "Saturday"
        }
        django_start_week_day = (start.isoweekday() % 7) + 1
        # django_end_week_day = (start.isoweekday() % 7) + 1

        if data['recurrency_type'] == 'WEEKLY':
            # TODO: Duplicated code with line 273
            previous_ablock_in_week = AvailabilityBlock.objects.filter(
                starting_at__week_day=django_start_week_day, recurrency_type='WEEKLY',
                employee_id=self.context['request'].user.profile.id
            )

            # if updating
            if self.instance:
                previous_ablock_in_week = previous_ablock_in_week.exclude(
                    id=self.instance.id)

            previous_ablock_in_week = previous_ablock_in_week.count()
            if previous_ablock_in_week > 0:
                raise serializers.ValidationError(
                    'This employee has ' + str(previous_ablock_in_week) + ' day block(s) for ' + days[
                        str(django_start_week_day)] + ' already')  # NOQA

        return data


class AvailabilityPutBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBlock
        exclude = ()

    def force_recurrency(self, data):
        if not data.get('recurrency_type'):
            raise serializers.ValidationError('Missing recurrency type')

    def validate(self, data):

        if 'starting_at' not in data:
            raise serializers.ValidationError('No initial date/time specified on the availability block')
        if 'ending_at' not in data:
            raise serializers.ValidationError('No final date/time specified on the availability block')

        start = data['starting_at']
        end = data['ending_at']

        if start > end:
            raise serializers.ValidationError('Invalid availability range')

        if (end - start).days > 0:
            raise serializers.ValidationError('Invalid availability rarge')

        if 'recurrent' in data and data['recurrent']:
            self.force_recurrency(data)

        # Resulta que datetime.isoweekday() retorna el dia de la semana
        # siendo lunes = 1 y domingo = 7
        #
        # pero el lookup de django __week_day interpreta la semana como
        # domingo = 1 y sabado = 7
        # con un poquito de juego matematico, resolvemos el problema

        days = {
            "1": "Sunday",
            "2": "Monday",
            "3": "Tuesday",
            "4": "Wednesday",
            "5": "Thursday",
            "6": "Friday",
            "7": "Saturday"
        }
        django_start_week_day = (start.isoweekday() % 7) + 1
        # django_end_week_day = (start.isoweekday() % 7) + 1

        if data['recurrency_type'] == 'WEEKLY':
            # TODO: Duplicated code with line 207
            previous_ablock_in_week = AvailabilityBlock.objects.filter(
                starting_at__week_day=django_start_week_day, recurrency_type='WEEKLY',
                employee_id=self.context['request'].user.profile.id
            )
            # if updating
            if self.instance:
                previous_ablock_in_week = previous_ablock_in_week.exclude(
                    id=self.instance.id)

            previous_ablock_in_week = previous_ablock_in_week.count()
            if previous_ablock_in_week > 0:
                raise serializers.ValidationError(
                    'This employee has ' + str(previous_ablock_in_week) + ' all day blocks for ' + days[
                        str(django_start_week_day)] + ' already')  # NOQA

        return data
