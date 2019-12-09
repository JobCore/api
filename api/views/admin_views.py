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
from django.db.models import Q

from api.utils.email import send_fcm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken
from api.models import *
from api.utils.notifier import notify_password_reset_code
from api.utils import validators
from api.utils.utils import get_aware_datetime
from api.serializers import user_serializer, profile_serializer, shift_serializer, employee_serializer, \
    other_serializer, payment_serializer
from api.serializers import favlist_serializer, venue_serializer, employer_serializer, auth_serializer, \
    notification_serializer, clockin_serializer
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


class EmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        template = get_template_content(slug)
        return HttpResponse(template['html'])


class FMCView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        if "message_slug" not in body:
            body["message_slug"] = "invite_to_shift"

        result = send_fcm(body["message_slug"], [body["registration_id"]], {
            "COMPANY": "Blizard Inc",
            "POSITION": "Server",
            "DATE": "Whenever you have time",
            "LINK": 'https://jobcore.co/talent/invite',
            "DATA": body["data"]
        })

        return Response(result, status=status.HTTP_200_OK)


class EmployeeBadgesView(APIView):
    def put(self, request, employee_id=None):
        request_data = request.data.copy()
        request_data['employee'] = employee_id
        serializer = other_serializer.EmployeeBadgeSerializer(
            data=request_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayrollPeriodView(APIView):
    def get(self, request, period_id=None):
        if period_id:
            try:
                period = PayrollPeriod.objects.get(id=period_id)
            except PayrollPeriod.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = payment_serializer.PayrollPeriodGetSerializer(period)
        else:
            periods = PayrollPeriod.objects.all()

            qStatus = request.GET.get('status')
            if qStatus:
                periods = periods.filter(status=qStatus)

            qEmployer = request.GET.get('employer')
            if qEmployer:
                periods = periods.filter(employer__id=qEmployer)

            serializer = payment_serializer.PayrollPeriodGetSerializer(
                periods, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminClockinsview(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Clockin.objects.all()

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

# class DocumentAdmin(APIView):
#     def post(self, request):
#         result = cloudinary.uploader.upload(
#             request.FILES['document'],
#             tags=['i9_document'],
#             use_filename=1,
#             unique_filename=1,
#             resource_type='auto'
#
#         )
#         request.data['document'] = result['secure_url']
#         request.data['public_id'] = result['public_id']
#         serializer = other_serializer.DocumentSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             request_data = {}
#
#             request_data['employee'] = self.request.user.profile.employee.id
#             request_data['documents'] = [serializer.instance.id]
#             serializer = other_serializer.EmployeeDocumentSerializer(
#                     data=request_data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def get(self, request, document_id):
#         try:
#             document = Document.objects.get(
#                     id=document_id)
#         except Document.DoesNotExist:
#             return Reponse(validators_error_object(
#                 'Not found.'), status=status.HTTP_404_NOT_FOUND)
#         return Response(document.document, status=status.HTTP_200_OK)
#
#     def put(seelf, request, document_id):
#
#         try:
#             document = Document.objects.get(
#                     id=document_id)
#         except Document.DoesNotExist:
#             return Response(validators_error_object(
#                 'Not found.'), status=status.HTTP_404_NOT_FOUND)
#
#         serializer = other_serializer.DocumentSerializer(document, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
