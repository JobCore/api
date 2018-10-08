import pytest
import json
import datetime
from api.models import *
from api.views import *
from api.serializers import *
from api.pagination import CustomPagination
from django.contrib.auth.models import User, AnonymousUser
from mixer.backend.django import mixer
from rest_framework.test import APITestCase, APIRequestFactory
from django.urls import reverse, resolve
from rest_framework_jwt.views import ObtainJSONWebToken

@pytest.mark.django_db
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
        # Basic models
        cls.badge = mixer.blend('api.Badge')
        cls.position = mixer.blend('api.Position')
        cls.venue = mixer.blend('api.Venue')
        cls.shift = mixer.blend('api.Shift')
        cls.unauthorized_profile = mixer.blend(
            'api.Profile', user=cls.unauthorized_user)
        cls.employee_profile = mixer.blend(
            'api.Profile', user=cls.user_employee)
        cls.employer_profile = mixer.blend(
            'api.Profile', user=cls.user_employer)
        cls.unauthorized_employer = mixer.blend(
            'api.Employer', profile=cls.unauthorized_profile)
        cls.employee = mixer.blend(
            'api.Employee', profile=cls.employee_profile)
        cls.employer = mixer.blend(
            'api.Employer', profile=cls.employer_profile)
        cls.favlist = mixer.blend('api.FavoriteList', owner=cls.employer)
        # Request factory
        cls.factory = APIRequestFactory()

    # REGISTER

    def test_employer_register_success(self):
        """
        Ensure successful employer register
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': 'new_employer@gmail.com',
            'email': 'new_employer@gmail.com',
            'first_name': 'Employer name',
            'last_name': 'Employer lastname',
            'account_type': "employee",
            'password': self.password
        }
        response = UserRegisterView.post(self, request)
        assert response.status_code == 201
        user = User.objects.get(email=request.data['email'])
        profile = Profile.objects.get(user_id=user.id)
        employer = Employer.objects.get(profile=profile.id)
        assert employer.profile.user.username == request.data['username']