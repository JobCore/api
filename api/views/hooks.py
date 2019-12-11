import pytz
utc = pytz.UTC
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly

from django.db.models import F, Func, Count, Q

from django.contrib.auth.models import User
from api.models import (Employee, Shift, ShiftInvite, ShiftApplication, Clockin, Employer, AvailabilityBlock, FavoriteList, Venue, JobCoreInvite,
                        Rate, FCMDevice, Notification, PayrollPeriod, PayrollPeriodPayment, Profile, Position)

from api.actions import employee_actions
from api.serializers import clockin_serializer, payment_serializer, shift_serializer

from rest_framework import serializers

from api.utils.loggers import log_debug

class ShiftInviteGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftInvite
        exclude = ()


class DefaultAvailabilityHook(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employees = Employee.objects.all()
        for emp in employees:
            employee_actions.create_default_availablity(emp)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

class ClockOutExpiredShifts(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        NOW = utc.localize(datetime.now())
        # if now > shift.ending_at + delta:
        clockins = Clockin.objects.filter(
            ended_at__isnull=True, 
            shift__maximum_clockout_delay_minutes__isnull=False, 
            shift__ending_at__lte= NOW - (timedelta(minutes=1) * F('shift__maximum_clockout_delay_minutes'))
        ).select_related('shift')
        for clockin in clockins:
            clockin.ended_at = clockin.shift.ending_at + timedelta(minutes=clockin.shift.maximum_clockout_delay_minutes)
            clockin.save()

        # also expire the shift if its still open or filled but it has ended (ended_at + delay)
        Shift.objects.filter(maximum_clockout_delay_minutes__isnull=False, ending_at__lte= NOW - (timedelta(minutes=1) * F('maximum_clockout_delay_minutes')), status__in=['OPEN', 'FILLED']).update(status='EXPIRED')
        # also expire shift if it has passed and no clockouts are pending (delay == null)
        Shift.objects.annotate(
            open_clockins=Count('clockin', filter=Q(clockin__ended_at__isnull=True))
        ).filter(
            maximum_clockout_delay_minutes__isnull=True, 
            ending_at__lte= NOW, 
            status__in=['OPEN', 'FILLED'], 
            open_clockins=0
        ).update(status='EXPIRED')

        # expire pending invites with passed shifts
        ShiftInvite.objects.filter(status= 'PENDING', shift__status='EXPIRED').update(status='EXPIRED')

        # delete applications for expired shifts
        ShiftApplication.objects.filter(shift__status='EXPIRED').delete()

        serializer = clockin_serializer.ClockinGetSerializer(clockins, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class GeneratePeriodsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        qEmployer = request.GET.get('employer')

        log_debug("hooks",'GeneratePeriodsView:get: init....')
        if qEmployer:
            try:
                employer = Employer.objects.get(id=qEmployer)
            except Employer.DoesNotExist:
                return Response(validators.error_object(
                    'Employer found.'), status=status.HTTP_404_NOT_FOUND)
            periods = payment_serializer.generate_periods_and_payments(employer)
            print(periods)
        else:
            log_debug("hooks",'GeneratePeriodsView:get: Looking for all employers periods')
            employers = Employer.objects.filter(payroll_period_starting_time__isnull=False)
            periods = []

            for employer in employers:
                periods = periods + \
                    payment_serializer.generate_periods_and_payments(employer)

        serializer = payment_serializer.PayrollPeriodGetSerializer(
            periods, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class AddTallentsToAllPositions(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        employees = Employee.objects.all().annotate(num_positions=Count('positions')).filter(num_positions=0)
        count = 0
        for emp in employees:
            employee_actions.add_default_positions(emp)
            count = count + 1

        return Response({ "ok" : str(count) + " talents affected" }, status=status.HTTP_200_OK)

class RemoveEmployeesWithoutProfile(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = User.objects.filter(profile__isnull=True)
        total = query.count()
        query.delete()

        return Response({ "ok" : str(total)+" user deleted" }, status=status.HTTP_200_OK)






# (Not being used) Expire invitations that its shifts have already started.
class ExpireOldInvites(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        NOW = utc.localize(datetime.now())
        invites = ShiftInvite.objects.filter(status= 'PENDING', shift__starting_at__lte= NOW + (timedelta(minutes=1) * F('shift__maximum_clockout_delay_minutes'))).select_related('shift')
        for invite in invites:
            invite.status = 'EXPIRED'
            invite.save()

        serializer = shift_serializer.ShiftGetSmallSerializer(invites, many=True)

        #JobCoreInvite.objects.filter(status= 'PENDING', expires_at__lte= NOW).delete()

        return Response(serializer.data, status=status.HTTP_200_OK)
