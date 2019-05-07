from rest_framework import serializers
from api.serializers import profile_serializer
from api.utils import notifier
from api.models import Badge, Position, JobCoreInvite, Rate, AvailabilityBlock, Employer, Shift, Employee, Clockin, User


class PositionSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('title', 'id')


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


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        exclude = ()


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        exclude = ()

# reset the employee badges


class EmployeeBadgeSerializer(serializers.Serializer):
    badges = serializers.ListField(child=serializers.IntegerField())
    employee = serializers.IntegerField()

    def validate(self, data):

        if 'badges' not in data:
            raise serializers.ValidationError('You need to specify the badges')

        if 'employee' not in data:
            raise serializers.ValidationError(
                'You need to specify the employee')

        try:
            employee = Employee.objects.get(id=data['employee'])
        except Employee.DoesNotExist:
            return Response(validators.error_object(
                'Employee not found.'), status=status.HTTP_404_NOT_FOUND)

        for badge in data['badges']:
            try:
                badge = Badge.objects.get(id=badge)
            except Badge.DoesNotExist:
                raise serializers.ValidationError('Badge not found')

        return data

    def create(self, validated_data):

        Employee.badges.through.objects.filter(
            employee_id=validated_data['employee']).delete()

        employee = Employee.objects.get(id=validated_data['employee'])
        for badge_id in validated_data['badges']:
            badge = Badge.objects.get(id=badge_id)
            employee.badges.add(badge)

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

        try:
            User.objects.get(email=data["email"])
            raise serializers.ValidationError(
                "The user is already registered in jobcore")
        except User.DoesNotExist:
            pass

        try:
            sender = self.context['request'].user.profile.id
            JobCoreInvite.objects.get(
                sender=sender,
                email=data["email"]
            )

            raise serializers.ValidationError(
                "User with this email has already been invited")
        except JobCoreInvite.DoesNotExist:
            pass

        return data

    def create(self, validated_data):
        # TODO: send email message not working
        invite = JobCoreInvite(**validated_data)
        invite.save()

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
        start = data['starting_at']
        end = data['ending_at']

        if start > end:
            raise serializers.ValidationError('Invalid availability range')

        if (end-start).days > 0:
            raise serializers.ValidationError('Invalid availability rarge')

        if 'recurrent' in data and data['recurrent']:
            self.force_recurrency(data)

        # Resulta que datetime.isoweekday() retorna el dia de la semana
        # siendo lunes = 1 y domingo = 7
        #
        # pero el lookup de django __week_day interpreta la semana como
        # domingo = 1 y sabado = 7
        # con un poquito de juego matematico, resolvemos el problema

        django_week_day = (start.isoweekday() % 7) + 1

        previous_ablock_in_week = AvailabilityBlock.objects.filter(
            starting_at__week_day=django_week_day, recurrency_type='WEEKLY'
            )

        if self.instance:
            previous_ablock_in_week = previous_ablock_in_week.exclude(
                id=self.instance.id)

        previous_ablock_in_week = previous_ablock_in_week.count()

        if previous_ablock_in_week > 0:
            raise serializers.ValidationError('There is a block covering this day of the week already')  # NOQA

        return data
