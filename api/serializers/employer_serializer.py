from rest_framework import serializers
from api.models import Employer, Shift
from datetime import datetime
from django.utils import timezone
from api.serializers.badge_serializers import BadgeGetSmallSerializer
from api.serializers.other_serializer import SubscriptionSerializer

#
# MAIN
#


class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        exclude = ()


class EmployerGetSerializer(serializers.ModelSerializer):
    badges = BadgeGetSmallSerializer(many=True)
    active_subscription = serializers.SerializerMethodField()

    class Meta:
        model = Employer
        fields = ('title', 'picture', 'bio', 'website', 'bio', 'response_time', 'rating',
            'total_ratings', 'badges', 'status', 'automatically_accept_from_favlists',
            'payroll_period_starting_time', 'payroll_period_length', 'payroll_period_type',
            'last_payment_period', 'maximum_clockin_delta_minutes', 
            'maximum_clockout_delay_minutes', 'created_at', 'updated_at','active_subscription')

    def get_active_subscription(self, employer):
        _sub = employer.employersubscription_set.filter(status='ACTIVE').first()
        if _sub is not None:
            serializer = SubscriptionSerializer(_sub.subscription, many=False)
            return serializer.data
        else:
            return None


class EmployerSerializer(serializers.ModelSerializer):
    retroactive = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Employer
        exclude = (
            'rating', 'total_ratings'
            )

    def validate(self, data):

        data = super(EmployerSerializer, self).validate(data)

        if 'title' in data and data['title'] == '':
            raise serializers.ValidationError('Company title cannot by empty')

        if 'bio' in data and data['bio'] == '':
            raise serializers.ValidationError('Company bio cannot by empty')

        return data

    def update(self, employer, validated_data):

        employer = super(EmployerSerializer, self).update(employer, validated_data)

        # update shifts settings retroactively
        if 'retroactive' in validated_data and validated_data['retroactive'] == True:
            NOW = datetime.now(tz=timezone.utc)
            Shift.objects.filter(ending_at__gte=NOW, employer__id=employer.id).update(
                maximum_clockin_delta_minutes=validated_data['maximum_clockin_delta_minutes'], 
                maximum_clockout_delay_minutes=validated_data['maximum_clockout_delay_minutes']
            )

        return employer
