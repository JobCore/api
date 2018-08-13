import json
from base64 import b64encode
from django.shortcuts import redirect
from django.core.mail import send_mail
from jobcore import settings
from django.http import HttpResponse
from django.views import generic
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope
from .pagination import CustomPagination

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken
from api.models import *
from api.serializers import *

# from .utils import GeneralException
import logging
logger = logging.getLogger(__name__)
from api.utils.email import get_template_content

class EmailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, slug):
        template = get_template_content(slug)
        return HttpResponse(template['html'])

class TokenUserView(APIView):
    permission_classes = [IsAuthenticated, TokenHasReadWriteScope]

    def post(self, request):
        try:
            data = request.data
            token = AccessToken.objects.filter(
                token=data["token"]).values().first()
            user = User.objects.get(id=token["user_id"])
            user = UserGetSerializer(user)

        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': user.data["id"],
            'email': user.data["email"],
            'username': user.data["username"],
            'token': {
                'token': token["token"],
                'expired': timezone.now() > token["expires"]
            }
        }, status=status.HTTP_200_OK)

class UserEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        try:
            user = User.objects.get(email=data["email"])
            serializer = UserLoginSerializer(user)
        except User.DoesNotExist:
            return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)

        encoded = str(user.id).encode('ascii')
        base64_id = b64encode(encoded).decode('unicode_escape')[:-2]
        tokenGenerator = PasswordResetTokenGenerator()
        token = tokenGenerator.make_token(user)

        try:
            link = "http://localhost:8000/api/user/reset/{uuid}/{token}".format(
                uuid=base64_id, token=token)
            send_email_message("password_reset", "alejandro@bestmiamiweddings.com",{
                link: link
            })
        except:
            return Response({'error': 'Error sending email. Check your internet connection.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            profile = Profile.objects.get(user_id=serializer.data["id"])
            if (request.data["type"] == "employer"):
                employer = Employer.objects.get(id=request.data['employer'])
                profile.employer = employer;
                profile.save();
            else:
                Employee.objects.create(profile=profile)
                profile.employee.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, TokenHasReadWriteScope]

    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
            serializer = UserGetSerializer(user)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.data.get("new_password"):
                # Check old password
                if not user.check_password(serializer.data.get("old_password")):
                    return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
                # Hash and save the password
                user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        permission_classes = [IsAuthenticated]

        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeView(APIView, CustomPagination):
    serializer_class = EmployeeGetSerializer

    def get(self, request, id=False):
        if (id):
            try:
                employee = Employee.objects.get(id=id)
            except Employee.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = EmployeeGetSerializer(employee, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            employees = Employee.objects.all()
            
            qFirst = request.GET.get('first_name')
            if qFirst:
                employees = employees.filter(profile__user__first_name__contains=qFirst)
            
            qLast = request.GET.get('last_name')
            if qLast:
                employees = employees.filter(profile__user__last_name__contains=qLast)

            qPositions = request.GET.getlist('positions')
            if qPositions:
                employees = employees.filter(positions__id__in=qPositions)

            qBadges = request.GET.getlist('badges')
            if qBadges:
                employees = employees.filter(badges__id__in=qBadges)
            
            serializer = EmployeeGetSerializer(employees, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            # page = self.paginator.paginate_queryset(employees, request)

            # if page is not None:
            #     serializer = self.serializer_class(page, many=True)
            #     return self.paginator.get_paginated_response(serializer.data)

    def put(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeeSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        employee.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplicantsView(APIView, CustomPagination):
    serializer_class = EmployeeGetSerializer

    # TODO: Optimization needed
    def get(self, request, id=False):
        applications = ShiftApplication.objects.select_related('employee','shift').all()
        # data = [applicant.id for applicant in applications]
        serializer = ApplicantGetSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployerView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                employer = Employer.objects.get(id=id)
            except Employer.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = EmployerGetSerializer(employer, many=False)
        else:
            employers = Employer.objects.all()
            serializer = EmployerGetSerializer(employers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        try:
            employer = Employer.objects.get(id=id)
        except Employer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EmployerSerializer(employer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            employer = Employer.objects.get(id=id)
        except Employer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        employer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                profile = Profile.objects.get(id=id)
            except Profile.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = ProfileGetSerializer(profile, many=False)
        else:
            employers = Profile.objects.all().exclude(
                employer__isnull=True, employee__isnull=True
            )
            serializer = ProfileGetSerializer(employers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    # No POST request needed
    # as Profiles are created automatically along with User register

    def put(self, request, id):
        try:
            profile = Profile.objects.get(id=id)
        except Profile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavListView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                favList = FavoriteList.objects.get(id=id)
            except FavoriteList.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = FavoriteListGetSerializer(favList, many=False)
        else:
            favLists = FavoriteList.objects.all()
            serializer = FavoriteListGetSerializer(favLists, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FavoriteListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            favList = FavoriteList.objects.get(id=id)
        except FavoriteList.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = FavoriteListSerializer(favList, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            favList = FavoriteList.objects.get(id=id)
        except FavoriteList.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        favList.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShiftView(APIView, CustomPagination):
    serializer_class = ShiftGetSerializer

    def get(self, request, id=False):
        if (id):
            try:
                shift = Shift.objects.get(id=id)
            except Shift.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = ShiftGetSerializer(shift, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            shifts = Shift.objects.all().order_by('date')
            
            qStatus = request.GET.get('not_status')
            if qStatus:
                shifts = shifts.filter(~Q(status = qStatus))
            
            serializer = self.serializer_class(shifts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            # page = PageNumberPagination.paginate_queryset(shifts, request)
            # if page is not None:
            #     serializer = self.serializer_class(page, many=True)
            #     return PageNumberPagination.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ShiftPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ShiftSerializer(shift, data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        shift.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ShiftCandidatesView(APIView, CustomPagination):
    serializer_class = ShiftGetSerializer

    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ShiftCandidatesSerializer(shift, data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VenueView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                venue = Venue.objects.get(id=id)
            except Venue.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = VenueSerializer(venue, many=False)
        else:
            venues = Venue.objects.all()
            serializer = VenueSerializer(venues, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = VenueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            venue = Venue.objects.get(id=id)
        except Venue.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = VenueSerializer(venue, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            venue = Venue.objects.get(id=id)
        except Venue.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        venue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PositionView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                position = Position.objects.get(id=id)
            except Position.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = PositionSerializer(position, many=False)
        else:
            positions = Position.objects.all()
            serializer = PositionSerializer(positions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PositionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            position = Position.objects.get(id=id)
        except Position.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PositionSerializer(position, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            position = Position.objects.get(id=id)
        except Position.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        position.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BadgeView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                badge = Badge.objects.get(id=id)
            except Badge.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = BadgeSerializer(badge, many=False)
        else:
            badges = Badge.objects.all()
            serializer = BadgeSerializer(badges, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BadgeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            badge = Badge.objects.get(id=id)
        except Badge.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = BadgeSerializer(badge, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            badge = Badge.objects.get(id=id)
        except Badge.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        badge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobCoreInviteView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                invite = JobCoreInvite.objects.get(id=id)
            except JobCoreInvite.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = JobCoreInviteGetSerializer(invite, many=False)
        else:
            invites = JobCoreInvite.objects.all()
            serializer = JobCoreInviteGetSerializer(invites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = JobCoreInvitePostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            invite = JobCoreInvite.objects.get(id=id)
        except JobCoreInvite.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = BadgeSerializer(invite, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            invite = JobCoreInvite.objects.get(id=id)
        except JobCoreInvite.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShiftInviteView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                invite = ShiftInvite.objects.get(id=id)
            except ShiftInvite.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = ShiftInviteSerializer(invite, many=False)
        else:
            invites = ShiftInvite.objects.all()
            serializer = ShiftInviteSerializer(invites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        invites = []
        if isinstance(request.data['shifts'],list):
            for s in request.data['shifts']:
                serializer = ShiftInviteSerializer(data={
                    "employee": request.data['employee'],
                    "sender": request.data['sender'],
                    "shift": s
                })
                if serializer.is_valid():
                    serializer.save()
                    invites.append(serializer.data)
                else:
                    return Response({'error': 'Error creating invite for shift'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = ShiftInviteSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                invites.append(serializer.data)
            else:
                return Response({'error': 'Error creating invite for shift'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(invites, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        try:
            invite = ShiftInvite.objects.get(id=id)
        except ShiftInvite.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RateView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                rate = Rate.objects.get(id=id)
            except Rate.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = RateSerializer(rate, many=False)
        else:
            rates = Rate.objects.all()
            serializer = RateSerializer(rates, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            invites.append(serializer.data)
        else:
            return Response({'error': 'Error saving rating'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(invites, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        try:
            rate = Rate.objects.get(id=id)
        except Rate.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        rate.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# class ImageView(APIView):
#     permission_classes = (AllowAny,)
#     authentication_classes = []

#     def get(self, request, image_name):
#         f = open('./static/'+image_name, 'rb')
#         return HttpResponse(f, content_type='image/png')
