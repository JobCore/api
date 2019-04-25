import datetime
import json
import sys
from rest_framework import permissions, serializers
from django.core.exceptions import ValidationError
from django.db.models import Q
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import User
from api.serializers import employee_serializer
from api.models import *
from api.actions import employee_actions

# Format Serializers


class ToTimestampField(serializers.Field):
    def to_representation(self, value):
        return value.timestamp() * 1000


class DatetimeFormatField(serializers.Field):
    def to_internal_value(self, value):
        return datetime.datetime.strptime(value, '%Y-%m-%d')

    def to_representation(self, value):
        return "{}-{}-{}T00:00".format(value.year, value.month, value.day)
