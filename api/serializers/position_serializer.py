from rest_framework import serializers
from api.models import Position


class PositionSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('title', 'id')


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        exclude = ()
