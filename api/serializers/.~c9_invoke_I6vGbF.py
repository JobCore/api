
from api.serializers import profile_serializer, employer_serializer
from api.models import User, Notification, FCMDevice
from rest_framework import serializers

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ()

class DeviceNotification(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ()
