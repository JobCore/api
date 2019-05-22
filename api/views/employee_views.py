from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from api.pagination import CustomPagination
from django.db.models import Q
from django.db.transaction import atomic
from api.models import *
from api.models import SHIFT_INVITE_STATUS_CHOICES
from api.utils.notifier import (
    notify_shift_candidate_update
)
from api.utils import validators
from api.serializers import (
    clockin_serializer, notification_serializer,
    shift_serializer, employee_serializer, other_serializer,
)

from django.db.models import Count


from django.utils import timezone
import datetime


import logging

from api.views.general_views import RateView
from api.mixins import EmployeeView, WithProfileView

logger = logging.getLogger(__name__)
# jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
# jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class EmployeeMeReceivedRatingsView(RateView, EmployeeView):
    def build_lookup(self, request):
        lookup = super().build_lookup(request)
        if 'employee_id' in lookup:
            lookup.pop('employee_id')
        return lookup

    def get_queryset(self):
        return Rate.objects.filter(employee_id=self.employee.id)

    def post(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request)


class EmployeeMeSentRatingsView(EmployeeMeReceivedRatingsView):
    def get_queryset(self):
        return Rate.objects.filter(sender__user_id=self.request.user)


class EmployeeMeApplicationsView(
        EmployeeView, CustomPagination):

    def get_queryset(self):
        return ShiftApplication.objects.filter(
            employee_id=self.employee.id).order_by('shift__starting_at')

    def get_serializer_class(self, many=True):
        if many:
            return shift_serializer.ApplicantGetSmallSerializer
        return shift_serializer.ApplicantGetSerializer

    def get(self, request, application_id=False):
        qs = self.get_queryset()
        many = True
        if application_id:
            try:
                qs = qs.get(id=application_id)
                many = False
            except ShiftApplication.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer_cls = self.get_serializer_class(many=many)

        serializer = serializer_cls(qs, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeMeShiftView(EmployeeView, CustomPagination):
    def get(self, request, id=None):

        if id != None:
            many = False
            shifts = Shift.objects.filter(id=id, employees__in=(self.employee.id,)).first()
            if shifts is None:
                return Response(
                    validators.error_object('The shift was not found'),  # NOQA
                    status=status.HTTP_404_NOT_FOUND)

            serializer = shift_serializer.ShiftGetBigSerializer(shifts, many=False)

        else:

            NOW = datetime.datetime.now(tz=timezone.utc)

            shifts = Shift.objects.all().annotate(clockins=Count('clockin'))
            shifts = shifts.filter(
                employees__in=(self.employee.id,)).order_by('starting_at')

            qStatus = request.GET.get('status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(
                    validators.error_object("Invalid status"),
                    status=status.HTTP_400_BAD_REQUEST)
            elif qStatus:
                shifts = shifts.filter(status__in=qStatus.split(","))

            qStatus = request.GET.get('not_status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(
                    validators.error_object("Invalid Status"),
                    status=status.HTTP_400_BAD_REQUEST)
            elif qStatus:
                shifts = shifts.filter(~Q(status=qStatus))

            qUpcoming = request.GET.get('approved')
            if qUpcoming == 'true':
                shifts = shifts.filter(ending_at__gte=NOW)

            qExpired = request.GET.get('completed')
            if qExpired == 'true':
                shifts = shifts.filter(ending_at__lte=NOW)

            qFailed = request.GET.get('failed')
            if qFailed == 'true':
                shifts = shifts.filter(ending_at__lte=NOW, clockins=0)

            serializer = shift_serializer.ShiftSerializer(shifts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeMeView(EmployeeView, CustomPagination):
    def get(self, request):
        employee = self.employee
        serializer = employee_serializer.EmployeeGetSerializer(
            employee, many=False)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        employee = self.employee

        serializer = employee_serializer.EmployeeSettingsSerializer(
            employee, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeShiftInviteView(EmployeeView):

    def get_queryset(self):
        return ShiftInvite.objects.filter(employee_id=self.employee.id)

    def fetch_one(self, request, id):
        return self.get_queryset().filter(id=id)

    def fetch_list(self, request):
        if 'status' not in self.request.GET:
            return self.get_queryset()

        status = request.GET.get('status')
        available_statuses = dict(SHIFT_INVITE_STATUS_CHOICES)

        if status not in available_statuses:
            valid_choices = '", "'.join(available_statuses.keys())

            raise ValidationError({
                'status': 'Not a valid status, valid choices are: "{}"'.format(valid_choices)  # NOQA
                })

        return self.get_queryset().filter(status=status)

    def get(self, request, id=False):
        data = None
        single = bool(id)
        many = not(single)

        if single:
            try:
                data = self.fetch_one(request, id).get()
            except ShiftInvite.DoesNotExist:
                return Response(
                    validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'),  # NOQA
                    status=status.HTTP_404_NOT_FOUND)
        else:
            data = self.fetch_list(request)

        serializer = shift_serializer.ShiftInviteGetSerializer(
            data, many=many)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @atomic
    def put(self, request, id, action=None):
        if action is None or action not in ['APPLY', 'REJECT']:
            return Response(
                validators.error_object('You need to specify an action=APPLY or REJECT'),  # NOQA
                status=status.HTTP_400_BAD_REQUEST)

        try:
            invite = self.fetch_one(request, id).get()
        except ShiftInvite.DoesNotExist:
            return Response(
                validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'),  # NOQA
                status=status.HTTP_404_NOT_FOUND)

        new_statuses = {
            'APPLY': 'APPLIED',
            'REJECT': 'REJECTED',
        }
        data = {
            "status": new_statuses[action]
        }

        # if the talent is on a preferred_talent list, automatically approve
        # him
        is_preferred_talent = FavoriteList.objects.filter(
            employer_id=invite.shift.employer.id,
            auto_accept_employees_on_this_list=True,
            employees__in=[self.employee]).exists()

        if is_preferred_talent:
            data["status"] = 'APPLIED'

        shiftSerializer = shift_serializer.ShiftInviteSerializer(
                invite,
                data=data,
                many=False,
                context={"request": request}
            )

        if not shiftSerializer.is_valid():
            return Response(shiftSerializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        shiftSerializer.save()

        if is_preferred_talent:
            ShiftEmployee.objects.create(
                employee=self.employee,
                shift=invite.shift
            )

            notify_shift_candidate_update(
                user=self.employee.user,
                shift=invite.shift,
                talents_to_notify=dict(
                    accepted=[self.employee],
                    rejected=[]
                )
            )

            return Response({
                        "details": "Your application was automatically approved because you are one of the vendors preferred talents.",  # NOQA
                    },
                    status=status.HTTP_200_OK)

        appSerializer = shift_serializer.ShiftApplicationSerializer(
            data={
                "shift": invite.shift.id,
                "invite": invite.id,
                "employee": invite.employee.id
            }, many=False)

        if not appSerializer.is_valid():
            return Response(
                appSerializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        appSerializer.save()
        return Response(appSerializer.data,
                        status=status.HTTP_200_OK)


class ClockinsMeView(EmployeeView):
    def get_queryset(self):
        return Clockin.objects.filter(employee_id=self.employee.id)

    def get(self, request):
        clockins = self.get_queryset()

        qShift = request.GET.get('shift')
        if qShift:
            clockins = clockins.filter(shift__id=qShift)

        qOpen = request.GET.get('open')
        if qOpen:
            clockins = clockins.filter(ended_at__isnull=(True if qOpen == 'true' else False))

        serializer = clockin_serializer.ClockinGetSerializer(
            clockins, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # logger.debug(f'ClockinsMeView:post: {request.data}')
        # logger.warning(f'ClockinsMeView:post: {request.data}')
        # logger.error(f'ClockinsMeView:post: {request.data}')
        # logger.info(f'ClockinsMeView:post: {request.data}')

        try:
            request_data = request.data.copy()
        except AttributeError as e:
            # logger.error(f'ClockinsMeView:post: {e}')
            request_data = {}

        request_data['employee'] = self.employee.id
        request_data['author'] = self.employee.id

        # logger.debug(f'ClockinsMeView:post: {request_data}')

        if 'started_at' not in request_data and 'ended_at' not in request_data:
            return Response(
                validators.error_object("You need to specify started_at or ended_at"),  # NOQA
                status=status.HTTP_400_BAD_REQUEST)

        instance = None

        if 'ended_at' in request_data:
            try:
                instance = Clockin.objects.get(
                    shift=request_data["shift"],
                    employee=request_data["employee"],
                    ended_at=None)
            except Clockin.DoesNotExist:
                return Response(
                    validators.error_object(
                        "There is no previous clockin for this shift"),
                    status=status.HTTP_400_BAD_REQUEST)
            except Clockin.MultipleObjectsReturned:
                return Response(
                    validators.error_object(
                        "It seems there is more than one clockin without clockout for this shift"),  # NOQA
                    status=status.HTTP_400_BAD_REQUEST)

        serializer = clockin_serializer.ClockinSerializer(
            instance, data=request_data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeeAvailabilityBlockView(
        EmployeeView, CustomPagination):

    def get_queryset(self):
        return AvailabilityBlock.objects.filter(employee_id=self.employee.id)

    def get(self, request):
        unavailability_blocks = self.get_queryset()

        serializer = other_serializer.AvailabilityBlockSerializer(
            unavailability_blocks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        request_data = request.data.copy()

        request_data['employee'] = self.employee.id
        serializer = other_serializer.AvailabilityBlockSerializer(
            data=request_data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, block_id):
        try:
            block = self.get_queryset().get(
                id=block_id, employee_id=self.employee.id)
        except AvailabilityBlock.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        request_data = request.data.copy()
        request_data['employee'] = self.employee.id

        serializer = other_serializer.AvailabilityBlockSerializer(
            block, data=request_data, context={"request": request},
            partial=True)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # model `EmployeeWeekUnvailability` no existe, lo comentaré
    #
    # def delete(self, request, unavailability_id):
    #     try:
    #         unavailability_block = EmployeeWeekUnvailability.objects.get(
    #             id=unavailability_id)
    #     except EmployeeWeekUnvailability.DoesNotExist:
    #         return Response(validators.error_object(
    #             'Not found.'), status=status.HTTP_404_NOT_FOUND)

    #     unavailability_block.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeDeviceMeView(WithProfileView):
    def get_queryset(self):
        return FCMDevice.objects.filter(user=self.request.user.id)

    def get(self, request, device_id=None):
        qs = self.get_queryset()
        many = True

        if device_id:
            many = False

            try:
                qs = qs.get(registration_id=device_id)
            except FCMDevice.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = notification_serializer.FCMDeviceSerializer(
            qs, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, device_id):

        try:
            device = self.get_queryset().filter(
                registration_id=device_id).get()
        except FCMDevice.DoesNotExist:
            return Response(validators.error_object(
                'Device not found'), status=status.HTTP_404_NOT_FOUND)

        serializer = notification_serializer.FCMDeviceSerializer(
            device, data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, device_id=None):
        qs = self.get_queryset()

        if device_id:
            try:
                qs = qs.get(registration_id=device_id)
            except FCMDevice.DoesNotExist:
                return Response(validators.error_object(
                    'Device not found'), status=status.HTTP_404_NOT_FOUND)

        qs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
