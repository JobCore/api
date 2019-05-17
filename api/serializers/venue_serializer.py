from rest_framework import serializers
from api.models import Venue


class VenueSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=100, required=True)
    street_address = serializers.CharField(max_length=250, required=True)

    class Meta:
        model = Venue
        exclude = ()


class VenueGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        exclude = ('street_address', 'country', 'updated_at', 'state')
