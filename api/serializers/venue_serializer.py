from rest_framework import serializers
from api.models import Venue

class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        exclude = ()

class VenueGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        exclude = ('street_address','country','updated_at','state')