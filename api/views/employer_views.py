# import json
# import os
# import functools
# import operator
# from django.utils.dateparse import parse_datetime
# from django.http import HttpResponse
# from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly  # NOQA
# from api.utils.email import send_fcm
# from django.contrib.auth.tokens import PasswordResetTokenGenerator
# from oauth2_provider.models import AccessToken
# from api.utils.notifier import notify_password_reset_code
# from api.utils.utils import get_aware_datetime
# from api.serializers import user_serializer, profile_serializer, shift_serializer, employee_serializer, other_serializer, payment_serializer  # NOQA
# from api.serializers import favlist_serializer, venue_serializer, employer_serializer, auth_serializer, notification_serializer, clockin_serializer  # NOQA
# from api.serializers import rating_serializer
# from .utils import GeneralException
# from rest_framework.views import APIView

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from api.pagination import CustomPagination
from django.db.models import Q

from django.contrib.auth.models import User
from api.models import *
from api.utils import validators

from api.serializers import (
    employer_serializer, user_serializer, shift_serializer,
    payment_serializer, venue_serializer, favlist_serializer,
    employee_serializer,
)

from django.utils import timezone
import datetime
import logging

from api.mixins import EmployerView

TODAY = datetime.datetime.now(tz=timezone.utc)
logger = logging.getLogger(__name__)


class EmployerMeView(EmployerView):
    def get(self, request):
        serializer = employer_serializer.EmployerGetSerializer(
            request.user.profile.employer, many=False)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = employer_serializer.EmployerSerializer(
            request.user.profile.employer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerMeUsersView(EmployerView):
    def get_queryset(self):
        return User.objects.filter(profile__employer_id=self.employer.id)

    def get(self, request, id=False):
        qs = self.get_queryset()
        many = True
        # no hay un endpoint que use esto.
        # if id:
        #     try:
        #         qs = qs.get(id=id)
        #         many = False
        #     except User.DoesNotExist:
        #         return Response(validators.error_object(
        #             'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = user_serializer.UserGetSmallSerializer(qs, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApplicantsView(EmployerView):
    def get_queryset(self):
        return ShiftApplication.objects.filter(
            shift__employer_id=self.employer.id).select_related(
                'employee', 'shift')
                
    def fetch_list(self, request):
        lookup = {}
        return self.get_queryset().filter(**lookup)

    def get(self, request, application_id=False):
        qs = self.get_queryset()
        many = True
        if application_id:
            try:
                application = qs.get(id=application_id)
                many = False
            except ShiftApplication.DoesNotEåxist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)
        else:
            application = self.fetch_list(request)

        serializer = shift_serializer.ApplicantGetSmallSerializer(
            application, many=many)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, application_id):
        qs = self.get_queryset()
        try:
            application = qs.get(id=application_id)
        except ShiftApplication.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        application.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerShiftInviteView(EmployerView):
    def get_queryset(self):
        return ShiftInvite.objects.filter(sender__employer_id=self.employer.id)

    def fetch_one(self, request, id):
        return self.get_queryset().filter(id=id)

    def fetch_list(self, request):
        lookup = {}

        if 'status' in self.request.GET:
            status = request.GET.get('status')
            available_statuses = dict(SHIFT_INVITE_STATUS_CHOICES)

            if status not in available_statuses:
                valid_choices = '", "'.join(available_statuses.keys())

                raise ValidationError({
                    'status': 'Not a valid status, valid choices are: "{}"'.format(valid_choices)  # NOQA
                    })
            lookup['status'] = status

        if 'employee' in self.request.GET:
            employee = self.request.GET.get('employee')
            lookup['employee_id'] = employee

        if 'shift' in self.request.GET:
            shift = self.request.GET.get('shift')
            lookup['shift_id'] = shift

        return self.get_queryset().filter(**lookup)

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

    def post(self, request):
        invites = []

        # masive creation of shift invites
        if isinstance(request.data['shifts'], list):
            for s in request.data['shifts']:
                serializer = shift_serializer.ShiftCreateInviteSerializer(
                    data={
                        "employee": request.data['employee'],
                        "sender": request.user.profile.id,
                        "shift": s},
                    context={
                        "request": request})
                if serializer.is_valid():
                    serializer.save()
                    invites.append(serializer.data)
                else:
                    return Response(serializer.errors,
                                    status=status.HTTP_400_BAD_REQUEST)
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
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(invites, status=status.HTTP_201_CREATED)

    def delete(self, request, id):

        try:
            invite = self.fetch_one(request, id).get()
        except ShiftInvite.DoesNotExist:
            return Response(
                validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'),
                status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerPayrollPeriodView(EmployerView):
    def get(self, request, period_id=None):

        if period_id:
            try:
                period = PayrollPeriod.objects.get(id=period_id)
            except PayrollPeriod.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = payment_serializer.PayrollPeriodGetSerializer(period)
        else:

            qStatus = request.GET.get('status')
            periods = PayrollPeriod.objects.filter(
                employer__id=self.employer.id,
                status=qStatus if qStatus else 'OPEN')

            serializer = payment_serializer.PayrollPeriodGetSerializer(
                periods, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployerVenueView(EmployerView):
    def get(self, request, id=False):
        if (id):
            try:
                venue = Venue.objects.get(id=id, employer__id=self.employer.id)
            except Venue.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = venue_serializer.VenueSerializer(venue, many=False)
        else:
            venues = Venue.objects.filter(employer__id=self.employer.id)
            serializer = venue_serializer.VenueSerializer(venues, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        request.data['employer'] = self.employer.id
        serializer = venue_serializer.VenueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):

        try:
            venue = Venue.objects.get(id=id, employer__id=self.employer.id)
        except Venue.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = venue_serializer.VenueSerializer(venue, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):

        try:
            venue = Venue.objects.get(id=id, employer__id=self.employer.id)
        except Venue.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        venue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavListView(EmployerView):
    def get(self, request, id=False):

        if (id):
            try:
                favList = FavoriteList.objects.get(
                    id=id, employer__id=self.employer.id)
            except FavoriteList.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = favlist_serializer.FavoriteListGetSerializer(
                favList, many=False)
        else:

            favLists = FavoriteList.objects.all()
            favLists = favLists.filter(employer__id=self.employer.id)
            serializer = favlist_serializer.FavoriteListGetSerializer(
                favLists, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        request.data['employer'] = self.employer.id
        serializer = favlist_serializer.FavoriteListSerializer(
            data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):

        try:
            favList = FavoriteList.objects.get(
                id=id, employer__id=self.employer.id)
        except FavoriteList.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = favlist_serializer.FavoriteListSerializer(
            favList, data=request.data)
        if serializer.is_valid():
            serializer.save()

            serializedFavlist = favlist_serializer.FavoriteListGetSerializer(
                favList)
            return Response(serializedFavlist.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):

        try:
            favList = favlist_serializer.FavoriteList.objects.get(
                id=id, employer__id=self.employer.id)
        except FavoriteList.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        favList.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavListEmployeeView(EmployerView):
    def put(self, request, employee_id):

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = employee_serializer.EmployeeFavlistSerializer(
            employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerShiftView(EmployerView, CustomPagination):
    def get(self, request, id=False):

        if (id):
            try:
                shift = Shift.objects.get(id=id, employer__id=self.employer.id)
            except Shift.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = shift_serializer.ShiftGetSerializer(shift, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:

            shifts = Shift.objects.filter(
                employer__id=self.employer.id).order_by('starting_at')

            qStatus = request.GET.get('status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(validators.error_object(
                    "Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
            elif qStatus:
                shifts = shifts.filter(status__in=qStatus.split(","))

            qStatus = request.GET.get('not_status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(validators.error_object(
                    "Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
            elif qStatus:
                shifts = shifts.filter(~Q(status=qStatus))

            qUpcoming = request.GET.get('upcoming')
            if qUpcoming == 'true':
                shifts = shifts.filter(starting_at__gte=TODAY)

            qUnrated = request.GET.get('unrated')
            if qUnrated == 'true':
                shifts = shifts.filter(rate_set=None)

            if request.user.profile.employer is None:
                shifts = shifts.filter(
                    employees__in=(
                        request.user.profile.id,))
            else:
                shifts = shifts.filter(
                    employer=request.user.profile.employer.id)

            serializer = shift_serializer.ShiftGetSerializer(shifts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        request.data["employer"] = self.employer.id
        serializer = shift_serializer.ShiftPostSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return_serializer = shift_serializer.ShiftGetSerializer(
                serializer.instance, many=False)
            return Response(return_serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):

        try:
            shift = Shift.objects.get(id=id, employer__id=self.employer.id)
        except Shift.DoesNotExist:
            return Response({"detail": "This shift was not found"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = shift_serializer.ShiftSerializer(
            shift, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):

        try:
            shift = Shift.objects.get(id=id, employer__id=self.employer.id)
        except Shift.DoesNotExist:
            return Response(
                {
                    "detail": "This shift was not found, talk to the employer for any more details about what happened."},
                status=status.HTTP_404_NOT_FOUND)

        shift.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerShiftCandidatesView(EmployerView, CustomPagination):
    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = shift_serializer.ShiftCandidatesAndEmployeesSerializer(
            shift, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployerShiftEmployeesView(EmployerView, CustomPagination):
    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = shift_serializer.ShiftCandidatesAndEmployeesSerializer(
            shift, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
