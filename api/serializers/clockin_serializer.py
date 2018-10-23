from api.serializers import shift_serializer, employee_serializer
from rest_framework import serializers
from django.db.models import Q
from api.models import Clockin

class ClockinSerializer(serializers.ModelSerializer):
    employee = employee_serializer.EmployeeGetSmallSerializer()
    shift = shift_serializer.ShiftGetSmallSerializer()

    class Meta:
        model = Clockin
        exclude = ()