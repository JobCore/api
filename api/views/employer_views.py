from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
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

        serializer = shift_serializer.ApplicantGetSmallSerializer(
            qs, many=many)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, application_id):
        qs = self.get_queryset()
        try:
            qs = qs.get(id=application_id)
        except ShiftApplication.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        qs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerShiftInviteView(EmployerView):
    def get_queryset(self):
        return ShiftInvite.objects.filter(sender__employer_id=self.employer.id)

    def fetch_one(self, request, id):
        return self.get_queryset().filter(id=id)

    def fetch_list(self, request):
        lookup = {}

        if 'status' in self.request.GET:
            status = request.GET.get('status').upper()
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

    def post(self, request, **kwargs):
        invites = []

        shifts = request.data['shifts']
        employee = request.data['employee']

        if not isinstance(shifts, list):
            shifts = [shifts]

        for shift in shifts:
            data = {
                "employee": employee,
                "sender": request.user.profile.id,
                "shift": shift,
            }

            serializer = shift_serializer.ShiftCreateInviteSerializer(
                data=data,
                context={
                    "request": request
                })

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                    )

            serializer.save()
            invites.append(serializer.data)
        return Response(invites, status=status.HTTP_201_CREATED)

    def delete(self, request, id):

        try:
            invite = self.fetch_one(request, id).get()
        except ShiftInvite.DoesNotExist:
            return Response(
                validators.error_object('The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'),  # NOQA
                status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerVenueView(EmployerView):
    def get_queryset(self):
        return Venue.objects.filter(employer_id=self.employer.id)

    def get(self, request, id=False):
        qs = self.get_queryset()
        many = True
        if id:
            try:
                qs = qs.get(id=id)
                many = False
            except Venue.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = venue_serializer.VenueSerializer(qs, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        request_data = request.data.copy()

        request_data['employer'] = self.employer.id
        serializer = venue_serializer.VenueSerializer(data=request_data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):

        try:
            venue = self.get_queryset().get(id=id)
        except Venue.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = venue_serializer.VenueSerializer(venue, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):

        try:
            venue = self.get_queryset().get(id=id)
        except Venue.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        venue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavListView(EmployerView):
    def get_queryset(self):
        return FavoriteList.objects.filter(employer_id=self.employer.id)

    def get(self, request, id=False):
        qs = self.get_queryset()
        many = True

        if (id):
            try:
                qs = qs.get(id=id)
                many = False
            except FavoriteList.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = favlist_serializer.FavoriteListGetSerializer(
            qs, many=many)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        request.data['employer'] = self.employer.id
        serializer = favlist_serializer.FavoriteListSerializer(
            data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, id):

        try:
            favList = self.get_queryset().get(id=id)
        except FavoriteList.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = favlist_serializer.FavoriteListSerializer(
            favList, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        serializedFavlist = favlist_serializer.FavoriteListGetSerializer(
            favList)
        return Response(serializedFavlist.data, status=status.HTTP_200_OK)

    def delete(self, request, id):

        try:
            favList = self.get_queryset().get(id=id)
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
