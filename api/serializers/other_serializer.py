from rest_framework import serializers
from api.serializers import profile_serializer
from api.utils import notifier
from api.models import (
    Badge, JobCoreInvite, Rate, Employer, Profile,
    Shift, Employee, User, AvailabilityBlock,
)

from api.serializers.position_serializer import PositionSmallSerializer


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


# reset the employee badges


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

    def validate(self, data):
        if not data.get('email'):
            raise serializers.ValidationError('invalid payload')

        user = User.objects.filter(email=data["email"]).first()
        if user is not None:
            profile = Profile.objects.filter(user=user).first()
            if profile is not None:
                raise serializers.ValidationError(
                    "The user is already registered in jobcore")

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
        invite = JobCoreInvite(**validated_data)
        invite.save()

        notifier.notify_jobcore_invite(invite)

        return invite

    def update(self, invite, validated_data):

        invite = super(JobCoreInvitePostSerializer, self).update(invite, validated_data)
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

        if 'allday' in data:
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
            raise serializers.ValidationError('Invalid availability rarge')

        if 'recurrent' in data and data['recurrent']:
            self.force_recurrency(data)

        # Resulta que datetime.isoweekday() retorna el dia de la semana
        # siendo lunes = 1 y domingo = 7
        #
        # pero el lookup de django __week_day interpreta la semana como
        # domingo = 1 y sabado = 7
        # con un poquito de juego matematico, resolvemos el problema

        if data['recurrency_type'] == 'WEEKLY' and data['allday'] == True:
            days = {
                "1": "Sunday",
                "2": "Monday",
                "3": "Tuesday",
                "4": "Wednesday",
                "5": "Thursday",
                "6": "Friday",
                "7": "Saturday"
            }

            django_week_day = (start.isoweekday() % 7) + 1

            previous_ablock_in_week = AvailabilityBlock.objects.filter(
                starting_at__week_day=django_week_day, recurrency_type='WEEKLY', employee_id=self.context['request'].user.profile.id
            )

            if self.instance:
                previous_ablock_in_week = previous_ablock_in_week.exclude(
                    id=self.instance.id)

            previous_ablock_in_week = previous_ablock_in_week.count()

            if previous_ablock_in_week > 0:
                raise serializers.ValidationError('This employee has '+str(previous_ablock_in_week)+' all day blocks for '+days[str(django_week_day)]+' already')  # NOQA

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

        if (end-start).days > 0:
            raise serializers.ValidationError('Invalid availability rarge')

        if 'recurrent' in data and data['recurrent']:
            self.force_recurrency(data)

        return data
