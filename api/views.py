import json
import os
import functools
import operator
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope
from api.pagination import CustomPagination

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from oauth2_provider.models import AccessToken
from api.models import *
from api.utils.notifier import notify_password_reset_code
from api.serializers import user_serializer, profile_serializer, shift_serializer, employee_serializer, other_serializer, favlist_serializer, venue_serializer, employer_serializer
from rest_framework_jwt.settings import api_settings

import api.utils.jwt
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER

# from .utils import GeneralException
import logging
logger = logging.getLogger(__name__)
from api.utils.email import get_template_content

class EmailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, slug):
        template = get_template_content(slug)
        return HttpResponse(template['html'])
        
class ValidateEmailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        token = request.GET.get('token')
        payload = jwt_decode_handler(token)
        try:
            user = User.objects.get(id=payload["user_id"])
            user.profile.status = ACTIVE #email validation completed
            user.profile.save()
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        template = get_template_content('email_validated')
        return HttpResponse(template['html'])

class PasswordView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        
        token = request.GET.get('token')
        data = jwt_decode_handler(token)
        try:
            user = User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            return Response({'error': 'Email not found on the database'}, status=status.HTTP_404_NOT_FOUND)

        payload = api.utils.jwt.jwt_payload_handler({
            "user_id": user.id
        })
        token = jwt_encode_handler(payload)

        template = get_template_content('reset_password_form', { "email": user.email, "token": token })
        return HttpResponse(template['html'])
        
    def post(self, request):
        email = request.data.get('email', None)
        if not email:
            return Response({'error': 'Email not found on the database'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(email=email)
            serializer = user_serializer.UserLoginSerializer(user)
        except User.DoesNotExist:
            return Response({'error': 'Email not found on the database'}, status=status.HTTP_404_NOT_FOUND)

        notify_password_reset_code(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def put(self, request):
        
        serializer = user_serializer.ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    #serializer_class = user_serializer.UserSerializer

    def post(self, request):
        serializer = user_serializer.UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, TokenHasReadWriteScope]

    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
            serializer = user_serializer.UserGetSerializer(user)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = user_serializer.UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = user_serializer.ChangePasswordSerializer(data=request.data)
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
    def get(self, request, id=False):
        if (id):
            try:
                employee = Employee.objects.get(id=id)
            except Employee.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = employee_serializer.EmployeeGetSerializer(employee, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            employees = Employee.objects.all()
            
            qName = request.GET.get('full_name')
            if qName:
                search_args = []
                for term in qName.split():
                    for query in ('profile__user__first_name__istartswith', 'profile__user__last_name__istartswith'):
                        search_args.append(Q(**{query: term}))
                
                employees = employees.filter(functools.reduce(operator.or_, search_args))
            else:
                qFirst = request.GET.get('first_name')
                if qFirst:
                    employees = employees.filter(profile__user__first_name__contains=qFirst)
                    entities = []
    
                qLast = request.GET.get('last_name')
                if qLast:
                    employees = employees.filter(profile__user__last_name__contains=qLast)

            qPositions = request.GET.getlist('positions')
            if qPositions:
                employees = employees.filter(positions__id__in=qPositions)

            qBadges = request.GET.getlist('badges')
            if qBadges:
                employees = employees.filter(badges__id__in=qBadges)
            
            serializer = employee_serializer.EmployeeGetSmallSerializer(employees, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    # there shoud be no POST because it is created on signup (registration)
    
    def delete(self, request, id):
        try:
            employee = Employee.objects.get(id=id)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        employee.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
class EmployeeMeView(APIView, CustomPagination):
    def get(self, request):
        if request.user.profile.employee == None:
            raise PermissionDenied("You are not a talent, you can not update your employee profile")
            
        try:
            employee = Employee.objects.get(id=request.user.profile.employee.id)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = employee_serializer.EmployeeGetSerializer(employee, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
        

    def put(self, request):
        
        if request.user.profile.employee == None:
            raise PermissionDenied("You are not a talent, you can not update your employee profile")

        try:
            employee = Employee.objects.get(id=request.user.profile.employee.id)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = employee_serializer.EmployeeSettingsSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AvailabilityBlockView(APIView, CustomPagination):

    def get(self, request, employee_id=False):
            
        if employee_id == False and request.user.profile.employee == None:
            raise PermissionDenied("You are not allowed to update employee availability")
        
        if employee_id == False:
            employee_id = request.user.profile.employee.id
                
        unavailability_blocks = AvailabilityBlock.objects.all().filter(employee__id=employee_id)
        
        serializer = other_serializer.AvailabilityBlockSerializer(unavailability_blocks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, employee_id=None):
        if request.user.profile.employee == None:
            raise PermissionDenied("You are not allowed to update employee availability")
        
        request.data['employee'] = request.user.profile.employee.id
        serializer = other_serializer.AvailabilityBlockSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, unavailability_id):
        try:
            unavailability_block = EmployeeWeekUnvailability.objects.get(id=unavailability_id)
        except EmployeeWeekUnvailability.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        unavailability_block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmployeeApplicationsView(APIView, CustomPagination):
    def get(self, request, id=False):
        if (id):
            try:
                employee = Employee.objects.get(id=id)
            except Employee.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            applications = ShiftApplication.objects.all().filter(employer__id=employee.id)
            
            serializer = shift_serializer.ShiftApplicationSerializer(applications, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

class ApplicantsView(APIView, CustomPagination):
    # TODO: Optimization needed
    def get(self, request, id=False):
        applications = shift_serializer.ShiftApplication.objects.select_related('employee','shift').all()
        # data = [applicant.id for applicant in applications]
        serializer = shift_serializer.ApplicantGetSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EmployerView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                employer = Employer.objects.get(id=id)
            except Employer.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = employer_serializer.EmployerGetSerializer(employer, many=False)
        else:
            employers = Employer.objects.all()
            serializer = employer_serializer.EmployerGetSerializer(employers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        try:
            employer = Employer.objects.get(id=id)
        except Employer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = employer_serializer.EmployerSerializer(employer, data=request.data)
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

class EmployerUsersView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = UserGetSmallSerializer(user, many=False)
        else:
            users = User.objects.all()
            serializer = user_serializer.UserGetSmallSerializer(users, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class ProfileView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                profile = Profile.objects.get(id=id)
            except Profile.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = profile_serializer.ProfileGetSerializer(profile, many=False)
        else:
            employers = Profile.objects.all().exclude(
                employer__isnull=True, employee__isnull=True
            )
            serializer = profile_serializer.ProfileGetSerializer(employers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    # No POST request needed
    # as Profiles are created automatically along with User register

    def put(self, request, id):
        try:
            profile = Profile.objects.get(id=id)
        except Profile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = profile_serializer.ProfileSerializer(profile, data=request.data, partial=True)
        userSerializer = user_serializer.UserUpdateSerializer(profile.user, data=request.data, partial=True)
        if serializer.is_valid() and userSerializer.is_valid():
            serializer.save()
            userSerializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FavListView(APIView):
    def get(self, request, id=False):
        if (id):
            try:
                favList = FavoriteList.objects.get(id=id)
            except FavoriteList.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if request.user.profile.employer.id != favList.employer.id:
                return Response("You are not allowed to access this information", status=status.HTTP_403_FORBIDDEN)
                
            serializer = favlist_serializer.FavoriteListGetSerializer(favList, many=False)
        else:
            
            is_employer = (request.user.profile.employer != None)
            if not is_employer:
                raise PermissionDenied("You are not allowed to access this information")
            else:
                favLists = FavoriteList.objects.all()
                favLists = favLists.filter(employer__id=request.user.profile.employer.id)
                serializer = favlist_serializer.FavoriteListGetSerializer(favLists, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = favlist_serializer.FavoriteListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            favList = FavoriteList.objects.get(id=id)
        except FavoriteList.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = favlist_serializer.FavoriteListSerializer(favList, data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            serializedFavlist = favlist_serializer.FavoriteListGetSerializer(favList)
            return Response(serializedFavlist.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            favList = favlist_serializer.FavoriteList.objects.get(id=id)
        except FavoriteList.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        favList.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FavListEmployeeView(APIView):
    def put(self, request, employee_id):
        
        if request.user.profile.employer == None:
            raise PermissionDenied("You are not allowed to have favorite lists")

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = employee_serializer.EmployeeSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShiftView(APIView, CustomPagination):
    def get(self, request, id=False):
        if (id):
            try:
                shift = Shift.objects.get(id=id)
            except Shift.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = shift_serializer.ShiftGetSerializer(shift, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            shifts = Shift.objects.all().order_by('starting_at')
            
            qStatus = request.GET.get('not_status')
            if qStatus:
                shifts = shifts.filter(~Q(status = qStatus))
            
            qUpcoming = request.GET.get('upcoming')
            if qUpcoming == 'true':
                shifts = shifts.filter(starting_at__gte=today)
                
            if request.user.profile.employer is None:
                shifts = shifts.filter(employees__in = (request.user.profile.id,))
            else:
                shifts = shifts.filter(employer = request.user.profile.employer.id)
            
            serializer = shift_serializer.ShiftSerializer(shifts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = shift_serializer.ShiftPostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = shift_serializer.ShiftSerializer(shift, data=request.data, context={"request": request})
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
    def put(self, request, id):
        try:
            shift = Shift.objects.get(id=id)
        except Shift.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = shift_serializer.ShiftCandidatesSerializer(shift, data=request.data, context={"request": request})
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

            serializer = venue_serializer.VenueSerializer(venue, many=False)
        else:
            venues = Venue.objects.all()
            serializer = venue_serializer.VenueSerializer(venues, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = venue_serializer.VenueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            venue = Venue.objects.get(id=id)
        except Venue.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = venue_serializer.VenueSerializer(venue, data=request.data)
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

            serializer = other_serializer.PositionSerializer(position, many=False)
        else:
            positions = Position.objects.all()
            serializer = other_serializer.PositionSerializer(positions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = other_serializer.PositionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            position = Position.objects.get(id=id)
        except Position.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = other_serializer.PositionSerializer(position, data=request.data)
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

            serializer = other_serializer.BadgeSerializer(badge, many=False)
        else:
            badges = Badge.objects.all()
            serializer = other_serializer.BadgeSerializer(badges, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = other_serializer.BadgeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            badge = Badge.objects.get(id=id)
        except Badge.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = other_serializer.BadgeSerializer(badge, data=request.data)
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

            serializer = other_serializer.JobCoreInviteGetSerializer(invite, many=False)
        else:
            invites = JobCoreInvite.objects.all()
            serializer = other_serializer.JobCoreInviteGetSerializer(invites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = other_serializer.JobCoreInvitePostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            invite = JobCoreInvite.objects.get(id=id)
        except JobCoreInvite.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = other_serializer.BadgeSerializer(invite, data=request.data)
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

            serializer = ShiftInviteGetSerializer(invite, many=False)
        else:
            invites = ShiftInvite.objects.all()
            
            is_employer = (request.user.profile.employer != None)
            if is_employer:
                invites = invites.filter(sender__employer__id=request.user.profile.employer.id)
                qEmployee_id = request.GET.get('employee')
                if qEmployee_id:
                    invites = invites.filter(employer__id=qEmployee_id)
            elif (request.user.profile.employee == None):
                raise ValidationError('This user doesn\'t seem to be an employee or employer')
            else:
                invites = invites.filter(employee__id=request.user.profile.employee.id)
            
            qStatus = request.GET.get('status')
            if qStatus:
                invites = invites.filter(status=qStatus)
                
            serializer = shift_serializer.ShiftInviteGetSerializer(invites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id, action):
        
        try:
            invite = ShiftInvite.objects.get(id=id)
        except ShiftInvite.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if action == 'apply':
            data={ "status": 'APPLIED' } 
        elif action == 'reject':
            data={ "status": 'REJECTED' } 
        else:
            raise ValidationError("You can either apply or reject an invite")

        shiftSerializer = shift_serializer.ShiftInviteSerializer(invite, data=data, many=False)
        appSerializer = shift_serializer.ShiftApplicationSerializer(data={
            "shift": invite.shift.id,
            "employee": invite.employee.id
        }, many=False)
        if shiftSerializer.is_valid() and appSerializer.is_valid():
            shiftSerializer.save()
            appSerializer.save()
            return Response(shiftSerializer.data, status=status.HTTP_200_OK)
        return Response(shiftSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        invites = []
        if request.user.profile.employer == None:
            raise PermissionDenied("You are not allowed to invite talents to shifts")
        # masive creation of shift invites
        if isinstance(request.data['shifts'],list):
            for s in request.data['shifts']:
                serializer = shift_serializer.ShiftInviteSerializer(data={
                    "employee": request.data['employee'],
                    "sender": request.user.profile.id,
                    "shift": s
                })
                if serializer.is_valid():
                    serializer.save()
                    invites.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # add new invite to the shift
            serializer = shift_serializer.ShiftInviteSerializer(data={
                    "employee": request.data['employee'],
                    "sender": request.user.profile.id,
                    "shift": request.data['shifts']
                })
            if serializer.is_valid():
                serializer.save()
                invites.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(invites, status=status.HTTP_201_CREATED)
        
    def delete(self, request, id):
        try:
            invite = ShiftInvite.objects.get(id=id)
        except ShiftInvite.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RateView(APIView):
    def get(self, request, user_id=False):
        if (user_id):
            try:
                rate = Rate.objects.get(id=user_id)
            except Rate.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = other_serializer.RateSerializer(rate, many=False)
        else:
            rates = Rate.objects.all()
            
            qEmployer = request.GET.get('employer')
            qEmployee = request.GET.get('employee')
            if qEmployee:
                rates = rates.filter(employee__id=qEmployee)
            elif qEmployer:
                rates = rates.filter(employee__id=qEmployer)
                
            serializer = other_serializer.RateSerializer(rates, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = other_serializer.RateSerializer(data=request.data)
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

class CatalogView(APIView):
    def get(self, request, catalog_type):
        
        if catalog_type == 'employees':
            employees = User.objects.exclude(employee__isnull=True)
            
            qName = request.GET.get('full_name')
            if qName:
                search_args = []
                for term in qName.split():
                    for query in ('profile__user__first_name__istartswith', 'profile__user__last_name__istartswith'):
                        search_args.append(Q(**{query: term}))
                
                employees = employees.filter(functools.reduce(operator.or_, search_args))

            qPositions = request.GET.getlist('positions')
            if qPositions:
                employees = employees.filter(positions__id__in=qPositions)

            qBadges = request.GET.getlist('badges')
            if qBadges:
                employees = employees.filter(badges__id__in=qBadges)
            
            employees = map(lambda emp: { "label": emp["first_name"] + ' ' + emp["last_name"], "value": emp["profile__employee__id"] }, employees.values('first_name', 'last_name', 'profile__employee__id'))
            return Response(employees, status=status.HTTP_200_OK)
        
        elif catalog_type == 'positions':
            positions = Position.objects.exclude()
            positions = map(lambda emp: { "label": emp["title"], "value": emp["id"] }, positions.values('title', 'id'))
            return Response(positions, status=status.HTTP_200_OK)
        
        elif catalog_type == 'badges':
            badges = Badge.objects.exclude()
            badges = map(lambda emp: { "label": emp["title"], "value": emp["id"] }, badges.values('title', 'id'))
            return Response(badges, status=status.HTTP_200_OK)
            
        return Response("no catalog", status=status.HTTP_200_OK)