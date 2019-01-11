import json
import os
import functools
import operator
from django.utils.dateparse import parse_datetime
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope
from api.pagination import CustomPagination
from django.db.models import Q

from api.utils.email import send_fcm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken
from api.models import *
from api.utils.notifier import notify_password_reset_code
from api.utils import validators
from api.utils.utils import get_aware_datetime
from api.serializers import user_serializer, profile_serializer, shift_serializer, employee_serializer, other_serializer, payment_serializer
from api.serializers import favlist_serializer, venue_serializer, employer_serializer, auth_serializer, notification_serializer, clockin_serializer
from api.serializers import rating_serializer
from rest_framework_jwt.settings import api_settings

import api.utils.jwt
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

from django.utils import timezone
import datetime
TODAY = datetime.datetime.now(tz=timezone.utc)

# from .utils import GeneralException
import logging
logger = logging.getLogger(__name__)
from api.utils.email import get_template_content

import cloudinary
import cloudinary.uploader
import cloudinary.api

class EmployerView(APIView):
    def validate_employee(self, request):
        if request.user.profile.employee == None:
            raise PermissionDenied("You don't seem to be a talent")
        self.employee = self.request.user.profile.employee
        
class EmployeeMeRatingsView(EmployerView):
    def get(self, request):
        self.validate_employee(request)
            
        ratings = Rate.objects.filter(employee__id=self.employee)
        
        qShift = request.GET.get('shift')
        if qShift is not None:
            try:
                clockin = Clockin.objects.get(shift=qShift, employee__id=self.employee.id)
            except Clockin.DoesNotExist:
                return Response(validators.error_object('This talent has not worked on this shift, no clockins have been found'), status=status.HTTP_400_BAD_REQUEST)
            except Clockin.MultipleObjectsReturned:
                pass
            
            ratings = ratings.filter(shift=qShift)

        qEmployer = request.GET.get('employer')
        if qEmployer is not None:
            ratings = ratings.filter(shift__employer=qEmployer)
        
        serializer = other_serializer.RatingGetSerializer(ratings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class EmployeeMeApplicationsView(EmployerView, CustomPagination):
    def get(self, request, id=False):
        self.validate_employee(request)

        applications = ShiftApplication.objects.all().filter(employee__id=self.employee.id).order_by('shift__starting_at')
        
        serializer = shift_serializer.ApplicantGetSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class EmployeeMeShiftView(EmployerView, CustomPagination):
    def get(self, request):
        self.validate_employee(request)
            
        shifts = Shift.objects.all().order_by('starting_at')
        
        qStatus = request.GET.get('status')
        if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
            return Response(validators.error_object("Invalid status"), status=status.HTTP_400_BAD_REQUEST)
        elif qStatus:
            shifts = shifts.filter(status__in = qStatus.split(","))
        
        qStatus = request.GET.get('not_status')
        if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
            return Response(validators.error_object("Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
        elif qStatus:
            shifts = shifts.filter(~Q(status = qStatus))
        
        qUpcoming = request.GET.get('upcoming')
        if qUpcoming == 'true':
            shifts = shifts.filter(starting_at__gte=TODAY)
        
        qFailed = request.GET.get('failed')
        if qFailed == 'true':
            shifts = shifts.filter(shiftemployee__success=False)
            
        shifts = shifts.filter(employees__in = (self.employee.id,))
        
        serializer = shift_serializer.ShiftSerializer(shifts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class EmployeeMeView(EmployerView, CustomPagination):
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
        
class ShiftMeInviteView(EmployerView):
    def get(self, request, id=False):
        self.validate_employee(request)
        
        invites = ShiftInvite.objects.filter(employee__id=self.employee.id)
        
        qStatus = request.GET.get('status')
        if qStatus:
            invites = invites.filter(status=qStatus)
            
        serializer = shift_serializer.ShiftInviteGetSerializer(invites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
            
class ClockinsMeView(EmployerView):
    def get(self, request, id=False):
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
            serializer = clockin_serializer.ClockinSerializer(data=request.data, context={"request": request})
            
        # checkout
        elif 'ended_at' in request.data:
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
        
class EmployeeAvailabilityBlockView(EmployerView, CustomPagination):

    def get(self, request, employee_id=False):
        self.validate_employee(request)
        
        unavailability_blocks = AvailabilityBlock.objects.all().filter(employee__id=self.employee.id)
        
        serializer = other_serializer.AvailabilityBlockSerializer(unavailability_blocks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, employee_id=None):
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
        
class EmployeeShiftInviteView(EmployerView):
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

    def put(self, request, id, action):
        self.validate_employee(request)
        try:
            invite = ShiftInvite.objects.get(id=id, employee__id=self.employee.id)
        except ShiftInvite.DoesNotExist:
            return Response(validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'), status=status.HTTP_404_NOT_FOUND)
        
        if action == 'apply':
            data={ "status": 'APPLIED' } 
        elif action == 'reject':
            data={ "status": 'REJECTED' } 
        else:
            return Response(validators.error_object("You can either apply or reject an invite"), status=status.HTTP_400_BAD_REQUEST)

        shiftSerializer = shift_serializer.ShiftInviteSerializer(invite, data=data, many=False)
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

class EmployeeDeviceMeView(APIView):
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
            