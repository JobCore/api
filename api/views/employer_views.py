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
    def validate_employer(self, request):
        if request.user.profile.employer == None:
            raise PermissionDenied("You don't seem to be an employer")
        self.employer = request.user.profile.employer
        
class EmployerMeView(EmployerView):
    def get(self, request):
        self.validate_employer(request)

        serializer = employer_serializer.EmployerGetSerializer(request.user.profile.employer, many=False)

        return Response(serializer.data, status=status.HTTP_200_OK)
        
class EmployerMeUsersView(EmployerView):
    def get(self, request, id=False):
        self.validate_employer(request)
        if (id):
            try:
                user = User.objects.get(id=id, profile__employer__id=self.employer.id)
            except User.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = UserGetSmallSerializer(user, many=False)
        else:
            users = User.objects.filter(profile__employer__id=self.employer.id)
            serializer = user_serializer.UserGetSmallSerializer(users, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class ApplicantsView(EmployerView):

    def get(self, request, application_id=False):
        self.validate_employer(request)
        
        if(application_id):
            try:
                application = ShiftApplication.objects.get(id=application_id)
            except ShiftApplication.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = shift_serializer.ApplicantGetSmallSerializer(application, many=False)
        else:
            applications = ShiftApplication.objects.select_related('employee','shift').filter(shift__employer__id=self.employer.id)
            # data = [applicant.id for applicant in applications]
            serializer = shift_serializer.ApplicantGetSmallSerializer(applications, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def delete(self, request, application_id):
        self.validate_employer(request)
        
        try:
            application = ShiftApplication.objects.get(id=application_id, shift__employer__id=self.employer.id)
        except ShiftApplication.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        application.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
class EmployerShiftInviteView(EmployerView):
    def get(self, request, id=False):
        self.validate_employer(request)
        if (id):
            try:
                invite = ShiftInvite.objects.get(id=id, employer__id=self.employer.id)
            except ShiftInvite.DoesNotExist:
                return Response(validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'), status=status.HTTP_404_NOT_FOUND)

            serializer = shift_serializer.ShiftInviteGetSerializer(invite, many=False)
        else:
            invites = ShiftInvite.objects.filter(sender__employer__id=self.employer.id)
            
            qEmployee_id = request.GET.get('employee')
            if qEmployee_id:
                invites = invites.filter(employer__id=qEmployee_id)

            qShift_id = request.GET.get('shift')
            if qShift_id:
                invites = invites.filter(shift__id=qShift_id)
            
            qStatus = request.GET.get('status')
            if qStatus:
                invites = invites.filter(status=qStatus)
                
            serializer = shift_serializer.ShiftInviteGetSerializer(invites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        self.validate_employer(request)
        invites = []

        # masive creation of shift invites
        if isinstance(request.data['shifts'],list):
            for s in request.data['shifts']:
                serializer = shift_serializer.ShiftCreateInviteSerializer(data={
                    "employee": request.data['employee'],
                    "sender": request.user.profile.id,
                    "shift": s
                }, context={"request": request})
                if serializer.is_valid():
                    serializer.save()
                    invites.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # add new invite to the shift
            serializer = shift_serializer.ShiftCreateInviteSerializer(data={
                    "employee": request.data['employee'],
                    "sender": request.user.profile.id,
                    "shift": request.data['shifts']
                }, context={"request": request})
            if serializer.is_valid():
                serializer.save()
                invites.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(invites, status=status.HTTP_201_CREATED)
        
    def delete(self, request, id):
        self.validate_employer(request)
        
        try:
            invite = ShiftInvite.objects.get(id=id, employer__id=self.employer.id)
        except ShiftInvite.DoesNotExist:
            return Response(validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'), status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmployerPayrollPeriodView(EmployerView):
    def get(self, request, period_id=None):
        self.validate_employer(request)
        
        if period_id:
            try:
                period = PayrollPeriod.objects.get(id=period_id)
            except PayrollPeriod.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = payment_serializer.PayrollPeriodGetSerializer(period)
        else:
            
            qStatus = request.GET.get('status')
            periods = PayrollPeriod.objects.filter(employer__id = self.employer.id, status=qStatus if qStatus else 'OPEN')
                
            serializer = payment_serializer.PayrollPeriodGetSerializer(periods, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
        
class EmployerVenueView(EmployerView):
    def get(self, request, id=False):
        self.validate_employer(request)
        if (id):
            try:
                venue = Venue.objects.get(id=id, employer__id=self.employer.id)
            except Venue.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = venue_serializer.VenueSerializer(venue, many=False)
        else:
            venues = Venue.objects.filter(employer__id=self.employer.id)
            serializer = venue_serializer.VenueSerializer(venues, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        self.validate_employer(request)
        
        request.data['employer'] = self.employer.id
        serializer = venue_serializer.VenueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        self.validate_employer(request)
        
        try:
            venue = Venue.objects.get(id=id, employer__id=self.employer.id)
        except Venue.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = venue_serializer.VenueSerializer(venue, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        self.validate_employer(request)
        
        try:
            venue = Venue.objects.get(id=id, employer__id=self.employer.id)
        except Venue.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        venue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
class FavListView(EmployerView):
    def get(self, request, id=False):
        self.validate_employer(request)
        
        if (id):
            try:
                favList = FavoriteList.objects.get(id=id, employer__id = self.employer.id)
            except FavoriteList.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = favlist_serializer.FavoriteListGetSerializer(favList, many=False)
        else:
            
            favLists = FavoriteList.objects.all()
            favLists = favLists.filter(employer__id=self.employer.id)
            serializer = favlist_serializer.FavoriteListGetSerializer(favLists, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        self.validate_employer(request)
        
        request.data['employer'] = self.employer.id
        serializer = favlist_serializer.FavoriteListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        self.validate_employer(request)
        
        try:
            favList = FavoriteList.objects.get(id=id, employer__id = self.employer.id)
        except FavoriteList.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = favlist_serializer.FavoriteListSerializer(favList, data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            serializedFavlist = favlist_serializer.FavoriteListGetSerializer(favList)
            return Response(serializedFavlist.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        self.validate_employer(request)
        
        try:
            favList = favlist_serializer.FavoriteList.objects.get(id=id, employer__id = self.employer.id)
        except FavoriteList.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        favList.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
class FavListEmployeeView(EmployerView):
    def put(self, request, employee_id):
        self.validate_employer(request)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = employee_serializer.EmployeeSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class EmployerShiftView(EmployerView, CustomPagination):
    def get(self, request, id=False):
        self.validate_employer(request)
        
        if (id):
            try:
                shift = Shift.objects.get(id=id, employer__id=self.employer.id)
            except Shift.DoesNotExist:
                return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = shift_serializer.ShiftGetSerializer(shift, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
        
            shifts = Shift.objects.filter(employer__id=self.employer.id).order_by('starting_at')
            
            qStatus = request.GET.get('status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(validators.error_object("Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
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
            
            qUnrated = request.GET.get('unrated')
            if qUnrated == 'true':
                shifts = shifts.filter(rate_set=None)
                
            if request.user.profile.employer is None:
                shifts = shifts.filter(employees__in = (request.user.profile.id,))
            else:
                shifts = shifts.filter(employer = request.user.profile.employer.id)
            
            serializer = shift_serializer.ShiftSerializer(shifts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
    def post(self, request):
        self.validate_employer(request)
        
        request.data["employer"] = self.employer.id
        serializer = shift_serializer.ShiftPostSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return_serializer = shift_serializer.ShiftGetSerializer(serializer.instance, many=False)
            return Response(return_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        self.validate_employer(request)
        
        try:
            shift = Shift.objects.get(id=id, employer__id = self.employer.id)
        except Shift.DoesNotExist:
            return Response({ "detail": "This shift was not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = shift_serializer.ShiftSerializer(shift, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        self.validate_employer(request)
        
        try:
            shift = Shift.objects.get(id=id, employer__id = self.employer.id)
        except Shift.DoesNotExist:
            return Response({ "detail": "This shift was not found, talk to the employer for any more details about what happened."}, status=status.HTTP_404_NOT_FOUND)

        shift.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmployerShiftCandidatesView(EmployerView, CustomPagination):
    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(validators.error_object('Not found.'), status=status.HTTP_404_NOT_FOUND)
            
        serializer = shift_serializer.ShiftCandidatesSerializer(shift, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        