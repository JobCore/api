import functools
import operator
import datetime
import logging

import cloudinary
import cloudinary.uploader
import cloudinary.api

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone

from jwt.exceptions import DecodeError

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    AllowAny, IsAuthenticatedOrReadOnly, IsAdminUser
)
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings


import api.utils.jwt
from api.pagination import CustomPagination

from api.models import *
from api.utils.notifier import notify_password_reset_code, notify_email_validation
from api.utils import validators
from api.utils.utils import get_aware_datetime

from api.serializers import (
    user_serializer, profile_serializer, shift_serializer,
    employee_serializer, other_serializer, payment_serializer
)
from api.serializers import (
    employer_serializer, auth_serializer, clockin_serializer,
    position_serializer
)
from api.serializers import rating_serializer
from api.utils.email import get_template_content

jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

TODAY = datetime.datetime.now(tz=timezone.utc)
logger = logging.getLogger(__name__)


class ValidateEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.GET.get('token')

        try:
            payload = jwt_decode_handler(token)
        except DecodeError:
            raise ValidationError('Invalid Token')

        try:
            user = User.objects.get(id=payload["user_id"])
            if user.profile.status != 'PENDING_EMAIL_VALIDATION':
                raise ValidationError('Your email has been already activated')

            try:
                db_token = UserToken.objects.get(token=token, email=user.email)
                db_token.delete()

                user.profile.status = 'ACTIVE'  # email validation completed
                user.profile.save()

                template = get_template_content('email_validated')
                return HttpResponse(template['html'])

            except UserToken.DoesNotExist:
                return Response(validators.error_object(
                    'Invalid validation token'), status=status.HTTP_404_NOT_FOUND)

        except User.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)


class ValidateSendEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, email=None):

        if email is None:
            raise ValidationError('Invalid email to validate')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(validators.error_object(
                'The user was not found'), status=status.HTTP_400_BAD_REQUEST)

            if user.profile.status != 'PENDING_EMAIL_VALIDATION':
                return Response(validators.error_object('This user is already validated'), status=status.HTTP_400_BAD_REQUEST)

        notify_email_validation(user)

        return Response({ "details": "The email was sent" }, status=status.HTTP_200_OK)


class PasswordView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):

        token = request.GET.get('token')
        try:
            data = jwt_decode_handler(token)
        except DecodeError:
            raise ValidationError('Invalid Token')

        try:
            user = User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            return Response({
                'error': 'Email not found on the database'
            }, status=status.HTTP_404_NOT_FOUND)

        token = api.utils.jwt.internal_payload_encode({
            "user_email": user.email
        })
        template = get_template_content(
            'reset_password_form', {
                "email": user.email, "token": token})
        return HttpResponse(template['html'])

    def post(self, request):
        email = request.data.get('email', None)
        if not email:
            return Response(
                validators.error_object('Email not found on the database'),
                status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            serializer = auth_serializer.UserLoginSerializer(user)
        except User.DoesNotExist:
            return Response(
                validators.error_object('Email not found on the database'),
                status=status.HTTP_404_NOT_FOUND)

        notify_password_reset_code(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):

        serializer = auth_serializer.ChangePasswordSerializer(
            data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    # serializer_class = user_serializer.UserSerializer

    def post(self, request):
        token = None
        if "token" in request.data:
            token = request.data["token"]

        serializer = auth_serializer.UserRegisterSerializer(data=request.data, context={"token": token })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
            serializer = user_serializer.UserGetSerializer(user)
        except User.DoesNotExist:
            return Response(validators.error_object(
                'The user was not found'), status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        permission_classes = [IsAdminUser]

        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(validators.error_object(
                'The user was not found'), status=status.HTTP_404_NOT_FOUND)

        serializer = user_serializer.UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        permission_classes = [IsAdminUser]

        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(validators.error_object(
                'The user was not found'), status=status.HTTP_404_NOT_FOUND)

        serializer = user_serializer.ChangePasswordSerializer(
            data=request.data)
        if serializer.is_valid():
            if serializer.data.get("new_password"):
                # Check old password
                if not user.check_password(
                        serializer.data.get("old_password")):
                    return Response({
                        "old_password": ["Wrong password."]
                        }, status=status.HTTP_400_BAD_REQUEST)
                # Hash and save the password
                user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        permission_classes = [IsAdminUser]

        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(validators.error_object(
                'The user was not found'), status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeView(APIView, CustomPagination):
    def get(self, request, id=False):
        if (id):
            try:
                employee = Employee.objects.get(id=id)
            except Employee.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = employee_serializer.EmployeeGetSerializer(
                employee, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            employees = Employee.objects.all()

            qName = request.GET.get('full_name')
            if qName:
                search_args = []
                for term in qName.split():
                    for query in ('profile__user__first_name__istartswith',
                                  'profile__user__last_name__istartswith'):
                        search_args.append(Q(**{query: term}))

                employees = employees.filter(
                    functools.reduce(operator.or_, search_args))
            else:
                qFirst = request.GET.get('first_name')
                if qFirst:
                    employees = employees.filter(
                        profile__user__first_name__contains=qFirst)

                qLast = request.GET.get('last_name')
                if qLast:
                    employees = employees.filter(
                        profile__user__last_name__contains=qLast)

            qPositions = request.GET.getlist('positions')
            if qPositions:
                employees = employees.filter(positions__id__in=qPositions)

            qBadges = request.GET.getlist('badges')
            if qBadges:
                employees = employees.filter(badges__id__in=qBadges)

            serializer = employee_serializer.EmployeeGetSmallSerializer(
                employees, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
    # there shoud be no POST because it is created on signup (registration)

class EmployerView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                employer = Employer.objects.get(id=id)
            except Employer.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = employer_serializer.EmployerGetSerializer(
                employer, many=False)
        else:
            employers = Employer.objects.all()
            serializer = employer_serializer.EmployerGetSerializer(
                employers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileMeView(APIView):
    def get(self, request):
        try:
            # access to trigger sql query & error
            profile = getattr(request.user, 'profile')
        except Profile.DoesNotExist:
            raise PermissionDenied("You don't seem to have a profile")

        serializer = profile_serializer.ProfileGetSerializer(
            profile, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # No POST request needed
    # as Profiles are created automatically along with User register

    def put(self, request):
        if request.user.profile is None:
            raise PermissionDenied("You don't seem to have a profile")

        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                validators.error_object('Not found.'),
                status=status.HTTP_404_NOT_FOUND)

        if "latitude" in request.data:
            request.data["latitude"] = round(request.data["latitude"], 6)
        if "longitude" in request.data:
            request.data["longitude"] = round(request.data["longitude"], 6)

        serializer = profile_serializer.ProfileSerializer(
            profile, data=request.data,
            context={"request": request}, partial=True)

        userSerializer = user_serializer.UserUpdateSerializer(
            profile.user, data=request.data, partial=True)

        if serializer.is_valid() and userSerializer.is_valid():
            serializer.save()
            userSerializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileMeImageView(APIView):

    def put(self, request):

        try:
            profile = Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            raise PermissionDenied("You don't seem to have a profile")

        if 'image' not in request.FILES:
            return Response(
                validators.error_object('no image'),
                status=status.HTTP_400_BAD_REQUEST)

        result = cloudinary.uploader.upload(
            request.FILES['image'],
            public_id='profile' + str(profile.id),
            crop='limit',
            width=450,
            height=450,
            eager=[{
                'width': 200, 'height': 200,
                'crop': 'thumb', 'gravity': 'face',
                'radius': 100
            },
            ],
            tags=['profile_picture']
        )

        profile.picture = result['secure_url']
        profile.save()
        serializer = profile_serializer.ProfileSerializer(profile)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PositionView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                position = Position.objects.get(id=id)
            except Position.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = position_serializer.PositionSerializer(
                position, many=False)
        else:
            positions = Position.objects.all()
            serializer = position_serializer.PositionSerializer(
                positions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = position_serializer.PositionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            position = Position.objects.get(id=id)
        except Position.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = position_serializer.PositionSerializer(
            position, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            position = Position.objects.get(id=id)
        except Position.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        position.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BadgeView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                badge = Badge.objects.get(id=id)
            except Badge.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = other_serializer.BadgeSerializer(badge, many=False)
        else:
            badges = Badge.objects.all()
            serializer = other_serializer.BadgeSerializer(badges, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        permission_classes = (IsAdminUser,)

        serializer = other_serializer.BadgeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        permission_classes = (IsAdminUser,)

        try:
            badge = Badge.objects.get(id=id)
        except Badge.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        serializer = other_serializer.BadgeSerializer(badge, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        permission_classes = (IsAdminUser,)

        try:
            badge = Badge.objects.get(id=id)
        except Badge.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        badge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RateView(APIView):

    def get_queryset(self):
        return Rate.objects.all()

    def build_lookup(self, request):
        lookup = {}

        # intentionally rewrite lookup to consider
        # employee OR employer, but not both at the same time

        qs_employer = request.GET.get('employer')
        qs_employee = request.GET.get('employee')

        if qs_employee:
            lookup = {'employee_id': qs_employee}

        if qs_employer:
            lookup = {'employer_id': qs_employer}

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

class CatalogView(APIView):
    def get(self, request, catalog_type):

        if catalog_type == 'employees':
            employees = User.objects.exclude(employee__isnull=True)

            qName = request.GET.get('full_name')
            if qName:
                search_args = []
                for term in qName.split():
                    for query in ('profile__user__first_name__istartswith',
                                  'profile__user__last_name__istartswith'):
                        search_args.append(Q(**{query: term}))

                employees = employees.filter(
                    functools.reduce(operator.or_, search_args))

            qPositions = request.GET.getlist('positions')
            if qPositions:
                employees = employees.filter(positions__id__in=qPositions)

            qBadges = request.GET.getlist('badges')
            if qBadges:
                employees = employees.filter(badges__id__in=qBadges)

            employees = map(
                lambda emp: {
                    "label": emp["first_name"] +
                    ' ' +
                    emp["last_name"],
                    "value": emp["profile__employee__id"]},
                employees.values(
                    'first_name',
                    'last_name',
                    'profile__employee__id'))
            return Response(employees, status=status.HTTP_200_OK)

        elif catalog_type == 'positions':
            positions = Position.objects.exclude()
            positions = map(
                lambda emp: {
                    "label": emp["title"],
                    "value": emp["id"]},
                positions.values(
                    'title',
                    'id'))
            return Response(positions, status=status.HTTP_200_OK)

        elif catalog_type == 'badges':
            badges = Badge.objects.exclude()
            badges = map(
                lambda emp: {
                    "label": emp["title"],
                    "value": emp["id"]},
                badges.values(
                    'title',
                    'id'))
            return Response(badges, status=status.HTTP_200_OK)
        elif catalog_type == 'narrow-preferences':
            return Response({
                'minimum_job_distance_miles': 20,
                'maximum_hourly_rate': 12,
                'minimum_availability_hours': 20,
                'minimum_job_positions': 1
            }, status=status.HTTP_200_OK)

        return Response("no catalog", status=status.HTTP_200_OK)

class PayrollShiftsView(APIView, CustomPagination):
    def get(self, request):

        clockins = Clockin.objects.all()

        qStatus = request.GET.get('status')
        if qStatus is not None:
            clockins = Clockin.objects.filter(status=qStatus)

        qShift = request.GET.get('shift')
        if qShift is not None and qShift is not '':
            clockins = clockins.filter(shift=qShift)
        else:
            qEnded_at = request.GET.get('ending_at')
            if qEnded_at is not None and qEnded_at is not '':
                clockins = clockins.filter(ended_at__lte=qEnded_at)

            qStarted_at = request.GET.get('starting_at')
            if qStarted_at is not None and qStarted_at is not '':
                clockins = clockins.filter(started_at__gte=qStarted_at)

        payrolDic = {}
        for clockin in clockins:
            clockinSerialized = clockin_serializer.ClockinGetSerializer(
                clockin)
            if str(clockin.employee.id) in payrolDic:
                payrolDic[str(clockin.employee.id)]["clockins"].append(
                    clockinSerialized.data)
            else:
                employeeSerialized = employee_serializer.EmployeeGetSmallSerializer(  # NOQA
                    clockin.employee)
                payrolDic[str(clockin.employee.id)] = {
                    "clockins": [clockinSerialized.data],
                    "talent": employeeSerialized.data
                }

        payrol = []
        for key, value in payrolDic.items():
            payrol.append(value)

        return Response(payrol, status=status.HTTP_200_OK)

    def put(self, request, id):

        if request.user.profile.employer is None:
            return Response(
                validators.error_object("You don't seem to be an employer"),
                status=status.HTTP_400_BAD_REQUEST)

        try:
            Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return Response({"detail": "The employee was not found"},
                            status=status.HTTP_404_NOT_FOUND)

        _serializers = []
        for clockin in request.data:
            try:
                old_clockin = Clockin.objects.get(id=clockin["id"])
                serializer = clockin_serializer.ClockinPayrollSerializer(
                    old_clockin, data=clockin)
            except Clockin.DoesNotExist:
                serializer = clockin_serializer.ClockinPayrollSerializer(
                    data=clockin)

            if not serializer.is_valid():
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
            _serializers.append(serializer)

        for serializer in _serializers:
            serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectedPaymentsView(APIView):
    def get(self, request, employer_id=None):

        if employer_id is None:
            return Response(
                validators.error_object('The employer must be specified'),
                status=status.HTTP_404_NOT_FOUND)

        qStarted_at = request.GET.get('starting_at')
        if qStarted_at is None:
            return Response(
                validators.error_object('You need to specify starting_at'),
                status=status.HTTP_404_NOT_FOUND)

        qEmployee = request.GET.get('employee')

        qLen = request.GET.get('period_length')
        qType = request.GET.get('period_type')

        # try:
        projection = payment_serializer.get_projected_payments(
            employer_id=employer_id,
            start_date=get_aware_datetime(qStarted_at),
            talent_id=qEmployee,
            period_length=int(qLen) if qLen is not None else 7,
            period_type=qType.upper() if qType is not None else 'DAYS'
        )

        talent = None
        if qEmployee:
            try:
                employee = Employee.objects.get(id=qEmployee)
                talent = employee_serializer.EmployeeGetSerializer(
                    employee, many=False).data
            except Employee.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

        return Response({
            "days": projection,
            "employee": talent
        }, status=status.HTTP_200_OK)


class JobCoreInviteView(APIView):
    def get(self, request, id=False):

        if request.user is None:
            raise PermissionDenied("You don't seem to be logged in")

        if (id):
            try:
                invite = JobCoreInvite.objects.get(
                    id=id, sender__id=request.user.profile.id)
            except JobCoreInvite.DoesNotExist:
                return Response(validators.error_object(
                    'Not found.'), status=status.HTTP_404_NOT_FOUND)

            serializer = other_serializer.JobCoreInviteGetSerializer(
                invite, many=False)
        else:
            invites = JobCoreInvite.objects.filter(
                sender__id=request.user.profile.id)
            serializer = other_serializer.JobCoreInviteGetSerializer(
                invites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        if request.user is None:
            raise PermissionDenied("You don't seem to be logged in")

        request.data['sender'] = request.user.profile.id

        serializer = other_serializer.JobCoreInvitePostSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):

        if request.user is None:
            raise PermissionDenied("You don't seem to be logged in")

        try:
            invite = JobCoreInvite.objects.get(
                id=id, sender__id=request.user.profile.id)

            request.data['sender'] = request.user.profile.id

            serializer = other_serializer.JobCoreInvitePostSerializer(
                invite, data=request.data, context={"request": request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except JobCoreInvite.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):

        if request.user is None:
            raise PermissionDenied("You don't seem to be logged in")

        try:
            invite = JobCoreInvite.objects.get(
                id=id, sender__id=request.user.profile.id)
            invite.delete()
        except JobCoreInvite.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)


class OnboardingView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, view_slug=None):

        views = {
            "dashboard": [
                {
                    "heading": "Dashboard Tutorial",
                    "message": "Click on the dolar icon to review your pending and cleared payments",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559831505/static/onboarding/dashboard1.png"
                },
                {
                    "heading": "Dashboard Tutorial",
                    "message": "Click on the envelope to review and apply to job invitations",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559831505/static/onboarding/dashboard2.png"
                },
                {
                    "heading": "Dashboard Tutorial",
                    "message": "Click on the suitcase to review your upcoming jobs",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559831505/static/onboarding/dashboard3.png"
                },
                {
                    "heading": "Dashboard Tutorial",
                    "message": "Click on the start and see how employers have rated you",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559831505/static/onboarding/dashboard4.png"
                }
            ],
            "invitations": [
                {
                    "heading": "Invitations Tutorial",
                    "message": "Swipe left to accept or right to reject the job invites",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                },
                {
                    "heading": "Invitations Tutorial",
                    "message": "Click on an invite to view details",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                }
            ],
            "job_preferences": [
                {
                    "heading": "Job Preferences Tutorial",
                    "message": "Setup your minimum job requirements and you will start receiving invites accordingly.",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                }
            ],
            "my_jobs": [
                {
                    "heading": "Jobs Tutorial",
                    "message": "Click on pending and review your the jobs that you have applied but have received no answer yet",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                },
                {
                    "heading": "Jobs Tutorial",
                    "message": "Click on approved for upcoming approved jobs",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                },
                {
                    "heading": "Jobs Tutorial",
                    "message": "Click on completed for historical data about previous jobs you have completed",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                },
                {
                    "heading": "Jobs Tutorial",
                    "message": "Click on failed to review jobs that you commited but not attended",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                }
            ],
            "profile": [
                {
                    "heading": "My Profile Tutorial",
                    "message": "More detailed profiles tend to get the most job invitations, take some time to fill your information",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                }
            ],
            "availablility": [
                {
                    "heading": "Availability Tutorial",
                    "message": "You will not receive invites for the dates and times that you are not available",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                }
            ],
            "my_payments": [
                {
                    "heading": "My Payments Tutorial",
                    "message": "Click on any pending or cleared payment to get information about the shift you worked on",
                    "img_url": "https://res.cloudinary.com/hq02xjols/image/upload/v1559164967/static/onboarding/Screen_Shot_2019-05-29_at_5.21.39_PM.png"
                }
            ]
        }

        if view_slug is None:
            return Response(views, status=status.HTTP_200_OK)
        else:
            if view_slug in views:
                return Response(views[view_slug], status=status.HTTP_200_OK)
            else:
                return Response([], status=status.HTTP_200_OK)

