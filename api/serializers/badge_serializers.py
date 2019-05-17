from rest_framework import serializers
from api.models import Badge


class BadgeGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ('title', 'image_url')
