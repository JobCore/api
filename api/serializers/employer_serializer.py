from rest_framework import serializers
from api.models import Employer
from api.serializers.badge_serializers import BadgeGetSmallSerializer

#
# MAIN
#


class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        exclude = ()


class EmployerGetSerializer(serializers.ModelSerializer):
    badges = BadgeGetSmallSerializer(many=True)

    class Meta:
        model = Employer
        exclude = ()


class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        exclude = (
            'rating', 'total_ratings'
            )
