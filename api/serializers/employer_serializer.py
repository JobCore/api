from rest_framework import serializers
from api.models import Employer, Badge

#
# NESTED
#


class BadgeGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ('title', 'image_url')


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
