import pytest
import json
import datetime
from api.views.general_views import ShiftView
from api.pagination import CustomPagination
from api.utils.notifier import get_talents_to_notify
# from django.contrib.auth.models import User, AnonymousUser
from mixer.backend.django import mixer
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
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
        cls.user_employee = mixer.blend(
            'auth.User', email='user_employee@gmail.com', password=cls.password)
        cls.user_employer = mixer.blend(
            'auth.User', email='user_employer@gmail.com', password=cls.password)
        # Set/Hash Users' passwords

        cls.unauthorized_user = mixer.blend(
            'auth.User', email='unauth@gmail.com', password=cls.password)

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
    
    def test_shift_view_get_single(self):
        """
        Ensure eveyone gets notification
        """
        path = reverse('api:id-shifts', kwargs={'id': self.shift.id})
        request = self.factory.get(path)
        response = ShiftView.get(self, request, id=self.shift.id)
        assert response.status_code == 200
