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
    def setUpClass(cls):
        super(TestViews, cls).setUpClass()
        # Data
        cls.password = '*12345678'
        # Create Users
        cls.unauthorized_user = mixer.blend(
            User, email='user@gmail.com', password=cls.password)
        cls.user_employee = mixer.blend(
            User, email='user_employee@gmail.com', password=cls.password)
        cls.user_employer = mixer.blend(
            User, email='user_employer@gmail.com', password=cls.password)
        # Set/Hash Users' passwords
        cls.unauthorized_user.set_password(cls.unauthorized_user.password)
        cls.user_employee.set_password(cls.user_employee.password)
        cls.user_employer.set_password(cls.user_employer.password)
        cls.unauthorized_user.save()
        cls.user_employee.save()
        cls.user_employer.save()

        cls.employee = mixer.blend(
            'api.Employee', user=cls.user_employee)
        cls.employer = mixer.blend(
            'api.Employer')
        cls.unauthorized_employer = mixer.blend(
            'api.Employer')

        cls.unauthorized_employer_profile = mixer.blend(
            'api.Profile', user=cls.unauthorized_user, employer=cls.employer)
        cls.employee_profile = mixer.blend(
            'api.Profile', user=cls.user_employee, employee=cls.employee)
        cls.employer_profile = mixer.blend(
            'api.Profile', user=cls.user_employer, employer=cls.employer)
            
        # Basic models
        
        cls.badge = mixer.blend('api.Badge')
        cls.position = mixer.blend('api.Position')
        cls.venue = mixer.blend('api.Venue')
        cls.shift = mixer.blend('api.Shift')
        
        cls.jobcore_invite = mixer.blend('api.JobCoreInvite', 
            sender=cls.employer_profile, shift=cls.shift, email='aalejo+frank@gmail.com')
            
        cls.favlist = mixer.blend('api.FavoriteList', owner=cls.employer)
        # Request factory
        cls.factory = APIRequestFactory()

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
        
    def test_employer_user_signup_success(self):
        """
        Ensure successful employer user creation
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': 'new_employer@gmail.com',
            'email': 'new_employer@gmail.com',
            'first_name': 'Boby',
            'last_name': 'Dylan',
            'account_type': "employer",
            'employer': self.employer.id,
            'password': self.password
        }
        response = UserRegisterView.post(self, request)
        assert response.status_code == 201
        user = User.objects.get(email=request.data['email'])
        profile = Profile.objects.get(user_id=user.id)
        assert profile.employer.title == self.employer.title
        
        
    def test_talent_signup_success(self):
        """
        Ensure successful employer user creation
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': 'aalejo+frank@gmail.com',
            'email': 'aalejo+frank@gmail.com',
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
        
        # it should have one invite already
        invites = ShiftInvite.objects.filter(employee=profile.employee)
        assert len(invites) == 1
        
    def test_employer_register_existing_email(self):
        """
        Ensure employer register error if email is already in use
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': 'some_username',
            'email': self.user_employer.email,
            'password': self.password,
            'type': 'employer'
        }
        response = UserRegisterView.post(self, request)
        assert response.status_code == 400
        
    def test_user_register_error(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': '',
            'email': '',
            'password': ''
        }
        response = UserRegisterView.post(self, request)
        assert response.status_code == 400
        
    def test_password_reset_success(self):
        """
        Ensure successful employer register
        """
        path = reverse('api:password-reset-email')
        request = self.factory.post(path)
        request.data = {
            'email': self.user_employer.email
        }
        response = PasswordView.post(self, request)
        assert response.status_code == 200
        
    def test_password_reset_email_not_registered(self):
        """
        Ensure error code is returned when provided email is not registered
        """
        path = reverse('api:password-reset-email')
        request = self.factory.post(path)
        request.data = {
            'email': 'some_email@gmail.com'
        }
        response = PasswordView.post(self, request)
        assert response.status_code == 404