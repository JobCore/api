from api.serializers import other_serializer
from rest_framework import serializers
from api.models import Employer

class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        exclude = ()
        
class EmployerGetSerializer(serializers.ModelSerializer):
    badges = other_serializer.BadgeSerializer(many=True)

    class Meta:
        model = Employer
        exclude = ()

class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        exclude = ()