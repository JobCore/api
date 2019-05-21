import pytz
utc = pytz.UTC
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly

from django.db.models import F, Func

from api.models import Employee, Shift, ShiftInvite, ShiftApplication, Clockin
from api.actions import employee_actions
from api.serializers import clockin_serializer


class DefaultAvailabilityHook(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employees = Employee.objects.all()
        for emp in employees:
            employee_actions.create_default_availablity(emp)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class DeleteAllShifts(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        ShiftInvite.objects.all().delete()
        ShiftApplication.objects.all().delete()
        Shift.objects.all().delete()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

class ClockOutExpiredShifts(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        NOW = utc.localize(datetime.now())
        # if now > shift.ending_at + delta:
        #clockins = Clockin.objects.all()
        #clockins = Clockin.objects.filter(ended_at__isnull=True)
        clockins = Clockin.objects.filter(ended_at__isnull=True, shift__ending_at__lte= NOW + (timedelta(minutes=1) * F('shift__maximum_clockout_delay_minutes'))).select_related('shift')
        for clockin in clockins:
            clockin.ended_at = clockin.shift.ending_at + timedelta(minutes=clockin.shift.maximum_clockout_delay_minutes)
            clockin.save()
            
        serializer = clockin_serializer.ClockinGetSerializer(clockins, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
