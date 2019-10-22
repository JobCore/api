from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from api.pagination import CustomPagination
from django.db.models import Q
from django.http import HttpRequest

import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api

from django.contrib.auth.models import User
from api.models import (
    Shift, ShiftApplication, Employee,
    ShiftInvite, Venue, FavoriteList,
    PayrollPeriod, Rate, Clockin, PayrollPeriodPayment,
    SHIFT_STATUS_CHOICES, SHIFT_INVITE_STATUS_CHOICES
)

from api.utils import validators

from api.serializers import (
    employer_serializer, user_serializer, shift_serializer,
    payment_serializer, venue_serializer, favlist_serializer,
    employee_serializer, clockin_serializer, rating_serializer
)

from django.utils import timezone
import datetime
import logging

from api.mixins import EmployerView


logger = logging.getLogger(__name__)
DATE_FORMAT = '%Y-%m-%d'


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

class EmployerMeImageView(EmployerView):

    def put(self, request):

        if 'image' not in request.FILES:
            return Response(
                validators.error_object('No image to update'),
                status=status.HTTP_400_BAD_REQUEST)

        result = cloudinary.uploader.upload(
            request.FILES['image'],
            public_id='employer' + str(self.employer.id),
            crop='limit',
            width=450,
            height=450,
            eager=[{
                'width': 200, 'height': 200,
                'crop': 'thumb', 'gravity': 'face',
                'radius': 100
            },
            ],
            tags=['employer_profile_picture']
        )

        self.employer.picture = result['secure_url']
        self.employer.save()
        serializer = employer_serializer.EmployerGetSerializer(self.employer)

        return Response(serializer.data, status=status.HTTP_200_OK)


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
                qs = qs.get(id=application_id)
                many = False
            except ShiftApplication.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)
        else:
            application = self.fetch_list(request)

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

        return self.get_queryset().filter(**lookup).order_by('-starting_at')

    def get(self, request, id=False):

        data = None
        single = bool(id)
        many = not (single)

        if single:
            try:
                data = self.fetch_one(request, id).get()
            except ShiftInvite.DoesNotExist:
                return Response(
                    validators.error_object(
                        'The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'),
                    # NOQA
                    status=status.HTTP_404_NOT_FOUND)
        else:
            data = self.fetch_list(request)

        serializer = shift_serializer.ShiftInviteGetSerializer(
            data, many=many)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        invites = []

        shifts = request.data['shifts']
        employees = request.data['employees']

        if not isinstance(shifts, list):
            shifts = [shifts]

        if not isinstance(employees, list):
            employees = [employees]

        for shift in shifts:
            for employee in employees:
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
                validators.error_object(
                    'The invite was not found, maybe the shift does not exist anymore. Talk to the employer for any more details about this error.'),
                # NOQA
                status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployerVenueView(EmployerView):
    def get_queryset(self):
        return Venue.objects.filter(employer_id=self.employer.id).order_by('title')

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
            TODAY = datetime.datetime.now(tz=timezone.utc)

            shifts = Shift.objects.filter(
                employer__id=self.employer.id)

            qStatus = request.GET.get('status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(validators.error_object(
                    "Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
            elif qStatus:
                status_list = qStatus.split(",")
                shifts = shifts.filter(status__in=list(map(lambda s: s.upper(), status_list)))
            else:
                shifts = shifts.exclude(status='CANCELLED')

            qStatus = request.GET.get('not_status')
            if validators.in_choices(qStatus, SHIFT_STATUS_CHOICES):
                return Response(validators.error_object(
                    "Invalid Status"), status=status.HTTP_400_BAD_REQUEST)
            elif qStatus:
                shifts = shifts.filter(~Q(status=qStatus))

            qUpcoming = request.GET.get('upcoming')
            if qUpcoming == 'true':
                shifts = shifts.filter(starting_at__gte=TODAY)

            qStart = request.GET.get('start')
            if qStart is not None and qStart != '':
                start = timezone.make_aware(datetime.datetime.strptime(qStart, DATE_FORMAT))
                shifts = shifts.filter(starting_at__gte=start)

            qEnd = request.GET.get('end')
            if qEnd is not None and qEnd != '':
                end = timezone.make_aware(datetime.datetime.strptime(qEnd, DATE_FORMAT))
                shifts = shifts.filter(ending_at__lte=end)

            qUnrated = request.GET.get('unrated')
            if qUnrated == 'true':
                shifts = shifts.filter(rate_set=None)

            qEmployeeNot = request.GET.get('employee_not')
            if qEmployeeNot is not None:
                shifts = shifts.exclude(employees__in=(int(qEmployeeNot),))

            serializer = shift_serializer.ShiftGetSerializer(shifts.order_by('-starting_at'), many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        _all_serializers = []
        request.data["employer"] = self.employer.id
        if 'multiple_dates' in request.data:
            for date in request.data['multiple_dates']:
                shift_date = dict(date)
                data = dict(request.data)
                data["starting_at"] = shift_date['starting_at']
                data["ending_at"] = shift_date['ending_at']
                data.pop('multiple_dates', None)
                serializer = shift_serializer.ShiftPostSerializer( data=data, context={"request": request})
                if serializer.is_valid():
                    _all_serializers.append(serializer)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = shift_serializer.ShiftPostSerializer( data=request.data, context={"request": request})
            if serializer.is_valid():
                _all_serializers.append(serializer)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        _shifts = []
        for s in _all_serializers:
            s.save()
            return_serializer = shift_serializer.ShiftGetSerializer(s.instance, many=False)
            _shifts.append(return_serializer.data)

        return Response(_shifts, status=status.HTTP_201_CREATED)

    def put(self, request, id):

        try:
            shift = Shift.objects.get(id=id, employer__id=self.employer.id)
        except Shift.DoesNotExist:
            return Response({ "detail": "This shift was not found" },
                            status=status.HTTP_404_NOT_FOUND)

        serializer = shift_serializer.ShiftUpdateSerializer(
            shift, data=request.data, context={ "request": request })

        posponed = request.GET.get('posponed')
        if serializer.is_valid():
            # if posponed=true it will not  save, just validate
            if posponed != 'true':
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


class ClockinsMeView(EmployerView):
    def get_queryset(self):
        return Clockin.objects.filter(shift__employer__id=self.employee.id)

    def fetch_one(self, id):
        return self.get_queryset().filter(id=id).first()

    def get(self, request, id=None):

        if id is not None:
            clockin = self.fetch_one(id)
            if clockin is None:
                return Response(
                    validators.error_object('The clockin was not found'),status=status.HTTP_404_NOT_FOUND)

            serializer = clockin_serializer.ClockinGetSerializer(clockin, many=False)
        else:
            clockins = self.get_queryset()

            qShift = request.GET.get('shift')
            if qShift:
                clockins = clockins.filter(shift__id=qShift)

            qEmployee = request.GET.get('employee')
            if qEmployee:
                clockins = clockins.filter(employee__id=qEmployee)

            qOpen = request.GET.get('open')
            if qOpen:
                clockins = clockins.filter(ended_at__isnull=(True if qOpen == 'true' else False))

            serializer = clockin_serializer.ClockinGetSerializer(
                clockins, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployerMePayrollPeriodsView(EmployerView):
    def get_queryset(self):
        return PayrollPeriod.objects.filter(employer_id=self.employer.id)

    def fetch_one(self, id):
        return self.get_queryset().filter(id=id).first()

    def get(self, request, period_id=None):

        if period_id is not None:
            period = self.fetch_one(period_id)
            if period is None:
                return Response(
                    validators.error_object('The payroll period was not found'),status=status.HTTP_404_NOT_FOUND)

            serializer = payment_serializer.PayrollPeriodGetSerializer(period, many=False)
        else:
            periods = self.get_queryset().order_by('-starting_at')
            serializer = payment_serializer.PayrollPeriodGetSerializer(periods, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployerMePayrollPeriodPaymentView(EmployerView):
    def get_queryset(self):
        return PayrollPeriodPayment.objects.filter(employer_id=self.employer.id)

    def fetch_one(self, id):
        return self.get_queryset().filter(id=id).first()

    def get(self, request, payment_id=None):

        if payment_id is not None:
            payment = self.fetch_one(payment_id)
            if payment is None:
                return Response(
                    validators.error_object('The payroll payment was not found'),status=status.HTTP_404_NOT_FOUND)

            serializer = payment_serializer.PayrollPeriodPaymentGetSerializer(payment, many=False)
        else:
            return Response(validators.error_object('You need to speficy a payment to review'), status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, payment_id=None):

        payment = self.fetch_one(payment_id)
        if payment is None:
            return Response(
                validators.error_object('The payroll payment was not found'),status=status.HTTP_404_NOT_FOUND)

        serializer = payment_serializer.PayrollPeriodPaymentSerializer(
            payment, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmployeerRateView(EmployerView):

    def get_queryset(self):
        return Rate.objects.filter(employer_id=self.employer.id)

    def build_lookup(self, request):
        lookup = {}

        # intentionally rewrite lookup to consider
        # employee OR employer, but not both at the same time

        qs_employee = request.GET.get('employee')
        if qs_employee:
            lookup = {'employee_id': qs_employee}

        qs_shift = request.GET.get('shift')
        if qs_shift:
            lookup['shift_id'] = qs_shift

        return lookup

    def get(self, request, id=False):
        many = True
        qs = self.get_queryset()
        if (id):
            try:
                qs = qs.get(id=id)
                many = False
            except Rate.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)
        else:
            lookup = self.build_lookup(request)
            qs = qs.filter(**lookup)

        serializer = rating_serializer.RatingGetSerializer(qs, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        serializer = rating_serializer.RatingSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class EmployerBatchActions(EmployerView):

    def post(self, request):

        log = []
        changes = request.data['changes']
        for entity in changes:
            for key in changes[entity]:
                shift = Shift.objects.get(id=key)
                serializer = shift_serializer.ShiftUpdateSerializer(shift, data=changes[entity][key], context={"request": request })
                if serializer.is_valid():
                    serializer.save()
                    log.append("Updating "+entity+" ")

        return Response(log, status=status.HTTP_200_OK)