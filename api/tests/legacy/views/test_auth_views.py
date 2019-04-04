import pytest
import json
import datetime
from api.models import (Position, Badge, Employer, Employee, Profile, AvailabilityBlock, 
    FavoriteList, Venue, Shift, ShiftEmployee, ShiftApplication, ShiftInvite, JobCoreInvite, 
    Rate, FCMDevice, Notification, Clockin, PayrollPeriod, PayrollPeriodPayment, 
)
from api.views.general_views import (EmployerView, UserRegisterView, PasswordView)
from api.serializers import *
from api.pagination import CustomPagination
from django.contrib.auth.models import User, AnonymousUser
from mixer.backend.django import mixer
from rest_framework.test import APITestCase, APIRequestFactory
from django.urls import reverse, resolve
from rest_framework_jwt.views import ObtainJSONWebToken
from django.core.exceptions import ValidationError
from django.test import override_settings


@pytest.mark.django_db
@override_settings(STATICFILES_STORAGE=None)
@override_settings(EMAIL_NOTIFICATIONS_ENABLED=False)
class TestViews(APITestCase, CustomPagination):
    #pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @classmethod
    def setUpClass(self):
        super(TestViews, self).setUpClass()
        # Data
        self.password = '*12345678'
        # Create Users
        self.unauthorized_user = mixer.blend(
            User, email='user@gmail.com', password=self.password)
        self.user_employee = mixer.blend(
            User, email='user_employee@gmail.com', password=self.password)
        self.user_employer = mixer.blend(
            User, email='user_employer@gmail.com', password=self.password)
        # Set/Hash Users' passwords
        self.unauthorized_user.set_password(self.unauthorized_user.password)
        self.user_employee.set_password(self.user_employee.password)
        self.user_employer.set_password(self.user_employer.password)
        self.unauthorized_user.save()
        self.user_employee.save()
        self.user_employer.save()

        self.employee = mixer.blend(
            'api.Employee', user=self.user_employee)
        self.employer = mixer.blend(
            'api.Employer')
        self.unauthorized_employer = mixer.blend(
            'api.Employer')

        self.unauthorized_employer_profile = mixer.blend(
            'api.Profile', user=self.unauthorized_user, employer=self.employer)
        self.employee_profile = mixer.blend(
            'api.Profile', user=self.user_employee, employee=self.employee)
        self.employer_profile = mixer.blend(
            'api.Profile', user=self.user_employer, employer=self.employer)
            
        # Basic models
        
        self.badge = mixer.blend('api.Badge')
        self.position = mixer.blend('api.Position')
        self.venue = mixer.blend('api.Venue')
        
        five_minutes = datetime.timedelta(minutes=5)
        self.shifts_expired = [ 
            mixer.blend(Shift, starting_at = timezone.now() - five_minutes),
            mixer.blend(Shift, starting_at = timezone.now() - five_minutes),
            mixer.blend(Shift, starting_at = timezone.now() - five_minutes)
        ];
        self.shifts_not_expired = [ 
            mixer.blend(Shift, starting_at = timezone.now() + five_minutes),
            mixer.blend(Shift, starting_at = timezone.now() + five_minutes),
            mixer.blend(Shift, starting_at = timezone.now() + five_minutes)
        ];
        
        self.jobcore_invites = [ 
            mixer.blend('api.JobCoreInvite', sender=self.employer_profile, shift=self.shifts_expired[0], email='new_talent@jobcore.co'),
            mixer.blend('api.JobCoreInvite', sender=self.employer_profile, shift=self.shifts_not_expired[0], email='new_talent@jobcore.co')
        ]
            
        self.favlist = mixer.blend('api.FavoriteList', owner=self.employer)
        # Request factory
        self.factory = APIRequestFactory()

    # REGISTER

    # def test_employer_create_success(self):
    #     """
    #     Ensure successful employer register
    #     """
    #     path = reverse('api:get-employers')
    #     request = self.factory.post(path)
    #     request.data = {
    #         'title': 'new_employer@gmail.com',
    #         'website': 'new_employer@gmail.com',
    #         'bio': 'Boby',
    #         'response_time': 'Dylan',
    #         'automatically_accept_from_favlists': "employer",
    #         'total_ratings': 1,
    #         'badges': self.password
    #     }
    #     response = EmployerView.post(self, request)
    #     assert response.status_code == 201
        
    # def test_employer_user_signup_success(self):
    #     """
    #     Ensure successful employer user creation
    #     """
    #     request = self.factory.post('user/register')
    #     request.data = {
    #         'username': 'new_employer@jobcore.co',
    #         'email': 'new_employer@jobcore.co',
    #         'first_name': 'Boby',
    #         'last_name': 'Dylan',
    #         'account_type': "employer",
    #         'employer': self.employer.id,
    #         'password': self.password
    #     }
    #     response = UserRegisterView.post(self, request)
    #     assert response.status_code == 201
    #     user = User.objects.get(email=request.data['email'])
    #     profile = Profile.objects.get(user_id=user.id)
    #     assert profile.employer.title == self.employer.title
        
        
    def test_talent_signup_success(self):
        """
        Ensure successful employer user creation
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': 'new_talent@jobcore.co',
            'email': 'new_talent@jobcore.co',
            'first_name': 'Frank',
            'last_name': 'Sinatra',
            'account_type': "employee",
            'password': self.password
        }
        response = UserRegisterView.post(self, request)
        assert response.status_code == 201
        user = User.objects.get(email=request.data['email'])
        profile = Profile.objects.get(user_id=user.id)
        assert profile.employee.user.email == request.data['email']
        
        # it should 7 availability blocks already (one for each day of the week)
        ava_blocks = AvailabilityBlock.objects.filter(employee=profile.employee)
        assert len(ava_blocks) == 7
        for block in ava_blocks:
            assert block.allday == True
        
        # it should have one invite already
        invites = ShiftInvite.objects.filter(employee=profile.employee)
        assert len(invites) == 1
    
    def test_talent_signup_wrong_email(self):
        """
        Ensure successful employer user creation
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': 'new_talent@jobcbh;kdfjgbndfkhjgdljfnljkdfnljkfgdkljkdfghjbkdfhvbhcvsjkhbfsjekhbfkjshrbfsjhbrfjkhwebfkjhsbfjhwebsfihjbsefibsefhbdeufboueiydbfousdfybfgiuysdbgbore.co',
            'email': 'new_talent@jobcbh;kdfjgbndfkhjgdljfnljkdfnljkfgdkljkdfghjbkdfhvbhcvsjkhbfsjekhbfkjshrbfsjhbrfjkhwebfkjhsbfjhwebsfihjbsefibsefhbdeufboueiydbfousdfybfgiuysdbgbore.co',
            'first_name': 'Frank',
            'last_name': 'Sinatra',
            'account_type': "employee",
            'password': self.password
        }
        response = UserRegisterView.post(self, request)
        response = UserRegisterView.post(self, request)
        raise BaseException("Hello")
    # def test_employer_register_existing_email(self):
    #     """
    #     Ensure employer register error if email is already in use
    #     """
    #     path = reverse('api:register')
    #     request = self.factory.post(path)
    #     request.data = {
    #         'username': 'some_username',
    #         'email': self.user_employer.email,
    #         'password': self.password,
    #         'type': 'employer'
    #     }
    #     response = UserRegisterView.post(self, request)
    #     assert response.status_code == 400
        
    # def test_user_register_error(self):
    #     """
    #     Ensure error code when invalid data is provided
    #     """
    #     path = reverse('api:register')
    #     request = self.factory.post(path)
    #     request.data = {
    #         'username': '',
    #         'email': '',
    #         'password': ''
    #     }
    #     response = UserRegisterView.post(self, request)
    #     assert response.status_code == 400
        
    # def test_password_reset_success(self):
    #     """
    #     Ensure successful employer register
    #     """
    #     path = reverse('api:password-reset-email')
    #     request = self.factory.post(path)
    #     request.data = {
    #         'email': self.user_employer.email
    #     }
    #     response = PasswordView.post(self, request)
    #     assert response.status_code == 200
        
    # def test_password_reset_email_not_registered(self):
    #     """
    #     Ensure error code is returned when provided email is not registered
    #     """
    #     path = reverse('api:password-reset-email')
    #     request = self.factory.post(path)
    #     request.data = {
    #         'email': 'some_email@gmail.com'
    #     }
    #     response = PasswordView.post(self, request)
    #     assert response.status_code == 404