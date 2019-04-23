import json
import os
import functools
import decimal
import operator
from django.utils.dateparse import parse_datetime
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly)
from api.pagination import CustomPagination
from django.db.models import Q

from api.utils.email import send_fcm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken
from api.models import *
from api.utils.notifier import (
    notify_password_reset_code, notify_shift_candidate_update
    )
from api.utils import validators
from api.utils.utils import get_aware_datetime
from api.serializers import (
    user_serializer, profile_serializer,
    shift_serializer, employee_serializer, other_serializer,
    payment_serializer, favlist_serializer, venue_serializer,
    employer_serializer, auth_serializer, notification_serializer,
    rating_serializer)

from rest_framework_jwt.settings import api_settings
from django.db.models import Count

import api.utils.jwt

from django.utils import timezone
import datetime

# from .utils import GeneralException
import logging
from api.utils.email import get_template_content

import cloudinary
import cloudinary.uploader
import cloudinary.api
logger = logging.getLogger(__name__)
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class EmployeeView(APIView):
    def validate_employee(self, request):
        if request.user.profile.employee_id is None:
            raise PermissionDenied("You don't seem to be a talent")
        self.employee = self.request.user.profile.employee


class EmployeeMeReceivedRatingsView(EmployeeView):
    def get(self, request):
        self.validate_employee(request)

        ratings = Rate.objects.filter(employee__id=self.employee.id)

        qShift = request.GET.get('shift')
        if qShift is not None:
            ratings = ratings.filter(shift__id=qShift)

        qEmployer = request.GET.get('employer')
        if qEmployer is not None:
            ratings = ratings.filter(shift__employer=qEmployer)

        serializer = other_serializer.RatingGetSerializer(ratings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeMeSentRatingsView(EmployeeView):
    def get(self, request):
        self.validate_employee(request)

        ratings = Rate.objects.filter(sender__user__id=self.employee.user.id)

        qShift = request.GET.get('shift')
        if qShift is not None:
            ratings = ratings.filter(shift__id=qShift)

        qEmployer = request.GET.get('employer')
        if qEmployer is not None:
            ratings = ratings.filter(shift__employer=qEmployer)

        serializer = other_serializer.RatingGetSerializer(ratings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeMeApplicationsView(EmployeeView, CustomPagination):
    def get(self, request, application_id=False):
        self.validate_employee(request)

        if(application_id):
            try:
                application = ShiftApplication.objects.get(id=application_id)
            except ShiftApplication.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)
            serializer = shift_serializer.ApplicantGetSmallSerializer(application, many=False)
        else:
            applications = ShiftApplication.objects.all().filter(employee__id=self.employee.id).order_by('shift__starting_at')
            serializer = shift_serializer.ApplicantGetSerializer(applications, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeMeShiftView(EmployeeView, CustomPagination):
    def get(self, request):
        self.validate_employee(request)

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

        qUpcoming = request.GET.get('upcoming')
        if qUpcoming == 'true':
            shifts = shifts.filter(starting_at__gte=NOW)

        qExpired = request.GET.get('expired')
        if qExpired == 'true':
            shifts = shifts.filter(ending_at__lte=NOW)

        qFailed = request.GET.get('failed')
        if qFailed == 'true':
            shifts = shifts.filter(ending_at__lte=NOW, clockins=0)

        serializer = shift_serializer.ShiftSerializer(shifts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeMeView(EmployeeView, CustomPagination):
    def get(self, request):
        self.validate_employee(request)

        try:
            employee = Employee.objects.get(id=self.employee.id)
        except Employee.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = employee_serializer.EmployeeGetSerializer(employee, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        self.validate_employee(request)

        try:
            employee = Employee.objects.get(id=self.employee.id)
        except Employee.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = employee_serializer.EmployeeSettingsSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeShiftInviteView(EmployeeView):
    def get(self, request, id=False):
        self.validate_employee(request)

        if (id):
            try:
                invite = ShiftInvite.objects.get(id=id, employee__id=self.employee.id)
            except ShiftInvite.DoesNotExist:
                return Response(validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'), status=status.HTTP_404_NOT_FOUND)

            serializer = shift_serializer.ShiftInviteGetSerializer(invite, many=False)
        else:
            invites = ShiftInvite.objects.filter(employee__id=self.employee.id)

            qStatus = request.GET.get('status')
            if qStatus:
                invites = invites.filter(status=qStatus)

            serializer = shift_serializer.ShiftInviteGetSerializer(invites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id, action=None):
        self.validate_employee(request)
        
        if request.user is None:
            return Response(validators.error_object('You need to specify an action=APPLY or REJECT'), status=status.HTTP_400_BAD_REQUEST)
        
        try:
            invite = ShiftInvite.objects.get(id=id, employee__id=self.employee.id)
        except ShiftInvite.DoesNotExist:
            return Response(validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'), status=status.HTTP_404_NOT_FOUND)

        data = {}
        if action.lower() == 'apply':
            data["status"] = 'APPLIED'
        elif action.lower() == 'reject':
            data["status"] = 'REJECTED'
        else:
            return Response(validators.error_object("You can either apply or reject an invite"), status=status.HTTP_400_BAD_REQUEST)

        #if the talent is on a preferred_talent list, automatically approve him
        preferred_talent = FavoriteList.objects.filter(employer__id=invite.shift.employer.id, auto_accept_employees_on_this_list=True, employees__in=[self.employee])
        if(len(preferred_talent) > 0):
            shiftSerializer = shift_serializer.ShiftInviteSerializer(invite, data={ "status": "APPLIED" }, many=False, context={"request": request })
            if shiftSerializer.is_valid():
                shiftSerializer.save()
                ShiftEmployee.objects.create(employee=self.employee, shift=invite.shift)
                notify_shift_candidate_update(user=self.employee.user, shift=invite.shift, talents_to_notify={
                    "accepted": [self.employee],
                    "rejected": []
                })
                return Response({ "details": "Your application was automatically approved because you are one of the vendors preferred talents." }, status=status.HTTP_200_OK)
            else:
                return Response(shiftSerializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            #else, create the application
            shiftSerializer = shift_serializer.ShiftInviteSerializer(invite, data=data, many=False, context={"request": request })
            appSerializer = shift_serializer.ShiftApplicationSerializer(data={
                "shift": invite.shift.id,
                "invite": invite.id,
                "employee": invite.employee.id
            }, many=False)
            if shiftSerializer.is_valid():
                if appSerializer.is_valid():
                    shiftSerializer.save()
                    appSerializer.save()

                    return Response(appSerializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(appSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(shiftSerializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @TODO: DELETE ShiftMeInviteView
#


class ShiftMeInviteView(EmployeeView):
#     def get(self, request, id=False):
#         self.validate_employee(request)

#         invites = ShiftInvite.objects.filter(employee__id=self.employee.id)

#         qStatus = request.GET.get('status')
#         if qStatus:
#             invites = invites.filter(status=qStatus)

#         serializer = shift_serializer.ShiftInviteGetSerializer(invites, many=True)

#         return Response(serializer.data, status=status.HTTP_200_OK)
    pass


class ClockinsMeView(EmployeeView):
    def get(self, request):
        self.validate_employee(request)

        clockins = Clockin.objects.filter(employee_id=self.employee.id)

        qShift = request.GET.get('shift')
        if qShift:
            clockins = clockins.filter(shift__id=qShift)

        serializer = clockin_serializer.ClockinGetSerializer(clockins, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        self.validate_employee(request)
        request.data['employee'] = self.employee.id
        # checkin
        if 'started_at' in request.data:
            request.data['latitude_in'] = round(decimal.Decimal(request.data['latitude_in']), 11) if request.data['latitude_in'] else None
            request.data['longitude_in'] = round(decimal.Decimal(request.data['longitude_in']), 11) if request.data['longitude_in'] else None
            serializer = clockin_serializer.ClockinSerializer(data=request.data, context={"request": request})

        # checkout
        elif 'ended_at' in request.data:
            request.data['latitude_out'] = round(decimal.Decimal(request.data['latitude_out']), 11) if request.data['latitude_out'] else None
            request.data['longitude_out'] = round(decimal.Decimal(request.data['longitude_out']), 11) if request.data['longitude_out'] else None
            try:
                clockin = Clockin.objects.get(shift=request.data["shift"], employee=request.data["employee"], ended_at=None)
                serializer = clockin_serializer.ClockinSerializer(clockin, data=request.data, context={"request": request})
            except Clockin.DoesNotExist:
                return Response(validators.error_object("There is no previous clockin for this shift"), status=status.HTTP_400_BAD_REQUEST)
            except Clockin.MultipleObjectsReturned:
                return Response(validators.error_object("It seems there is more than one clockin without clockout for this shif"), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(validators.error_object("You need to specify started_at or ended_at"), status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeeAvailabilityBlockView(EmployeeView, CustomPagination):

    def get(self, request):
        self.validate_employee(request)

        unavailability_blocks = AvailabilityBlock.objects.all().filter(employee__id=self.employee.id)

        serializer = other_serializer.AvailabilityBlockSerializer(unavailability_blocks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        self.validate_employee(request)

        request.data['employee'] = self.employee.id
        serializer = other_serializer.AvailabilityBlockSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, block_id=None):
        self.validate_employee(request)

        try:
            block = AvailabilityBlock.objects.get(id=block_id, employee=self.employee)
        except AvailabilityBlock.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = other_serializer.AvailabilityBlockSerializer(block, data=request.data, context={"request": request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, unavailability_id):
        self.validate_employee(request)

        try:
            unavailability_block = EmployeeWeekUnvailability.objects.get(id=unavailability_id)
        except EmployeeWeekUnvailability.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        unavailability_block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeDeviceMeView(EmployeeView):
    def get(self, request, device_id=None):

        if request.user is None:
            return Response(validators.error_object('You have to be loged in'), status=status.HTTP_400_BAD_REQUEST)

        if device_id is not None:
            try:
                device = FCMDevice.objects.get(registration_id=device_id, user=request.user.id)
                serializer = notification_serializer.FCMDeviceSerializer(device, many=False)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except FCMDevice.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)
        else:
            devices = FCMDevice.objects.filter(user=request.user.id)
            serializer = notification_serializer.FCMDeviceSerializer(devices, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, device_id):

        if request.user is None:
            return Response(validators.error_object('No user was identified'), status=status.HTTP_400_BAD_REQUEST)

        try:
            device = FCMDevice.objects.get(registration_id=device_id, user=request.user.id)
            serializer = notification_serializer.FCMDeviceSerializer(device, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except FCMDevice.DoesNotExist:
            return Response(validators.error_object('Device not found'), status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, device_id=None):

        if request.user is None:
            return Response(validators.error_object('No user was identified'), status=status.HTTP_400_BAD_REQUEST)

        try:
            if device_id is None:
                devices = FCMDevice.objects.filter(user=request.user.id)
                devices.delete()
            else:
                device = FCMDevice.objects.get(registration_id=device_id, user=request.user.id)
                device.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except FCMDevice.DoesNotExist:
            return Response(validators.error_object('Device not found'), status=status.HTTP_404_NOT_FOUND)
