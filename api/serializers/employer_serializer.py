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

    def validate(self, data):

        data = super(EmployerSerializer, self).validate(data)

        if 'title' in data and data['title'] == '':
            raise serializers.ValidationError('Company title cannot by empty')

        if 'bio' in data and data['bio'] == '':
            raise serializers.ValidationError('Company bio cannot by empty')

        return data
