import pytest
import json
import datetime
from api.models import *
from api.views import *
from api.serializers import *
from api.pagination import CustomPagination
from django.contrib.auth.models import User, AnonymousUser
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
    
    def test_shift_view_get_single(self):
        """
        Ensure single shift data is returned via GET
        """
        path = reverse('api:id-shifts', kwargs={'id': self.shift.id})
        request = self.factory.get(path)
        response = ShiftView.get(self, request, id=self.shift.id)
        assert response.status_code == 200

    def test_shift_view_get_single_invalid_shift(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-shifts', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = ShiftView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_shift_view_post(self):
        """
        Ensure shift data is created via POST
        """
        path = reverse('api:get-shifts')
        request = self.factory.post(path)
        force_authenticate(request, user=self.user_employer)
        request.user = self.user_employer
        request.data = {
            'status': 'OPEN',
            'starting_at': "2019-10-20T00:00",
            'ending_at': "2019-10-20T00:00",
            #'rating': 3,
            #'candidates': [self.employee.id],
            #'employees': [self.employee.id],
            'venue': self.venue.id,
            'position': self.position.id,
            'application_restriction': 'FAVORITES',
            'maximum_allowed_employees': 10,
            'minimum_hourly_rate': 8,
            'minimum_allowed_rating': 3,
            'allowed_from_list': [self.favlist.id],
        }
        response = ShiftView.post(self, request)
        assert response.status_code == 201
        assert Shift.objects.filter(status='OPEN').count() == 1

    def test_shift_view_post_invalid_data(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:get-shifts')
        request = self.factory.post(path)
        force_authenticate(request, user=self.user_employer)
        request.user = self.user_employer
        request.data = {
            'status': 'OPEN'
        }
        response = ShiftView.post(self, request)
        assert response.status_code == 400

    def test_shift_view_put(self):
        """
        Ensure shift data is updated via PUT
        """
        path = reverse('api:id-shifts', kwargs={'id': self.shift.id})
        request = self.factory.put(path)
        force_authenticate(request, user=self.user_employer)
        request.user = self.user_employer
        request.data = {
            'status': 'CANCELLED',
            'starting_at': "2019-10-20T00:00",
            'ending_at': "2019-10-20T00:00",
            'rating': 4,
            'candidates': [],
            'employees': [],
            'venue': self.venue.id,
            'position': self.position.id,
            'application_restriction': 'ANYONE',
            'maximum_allowed_employees': 20,
            'minimum_hourly_rate': 10,
            'minimum_allowed_rating': 1,
            'allowed_from_list': [],
        }
        response = ShiftView.put(self, request, id=self.shift.id)
        assert response.status_code == 200
        shift = Shift.objects.get(id=self.shift.id)
        assert shift.status == request.data['status']
        assert shift.starting_at.strftime("%Y-%m-%dT%H:%M") == request.data['starting_at']
        assert shift.ending_at.strftime("%Y-%m-%dT%H:%M") == request.data['ending_at']
        assert shift.rating == request.data['rating']
        assert shift.candidates.count() == len(request.data['candidates'])
        assert shift.venue.id == request.data['venue']
        assert shift.position.id == request.data['position']
        assert shift.application_restriction == request.data['application_restriction']

    def test_shift_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-shifts', kwargs={'id': self.shift.id})
        request = self.factory.put(path)
        force_authenticate(request, user=self.user_employer)
        request.user = self.user_employer
        request.data = {
            'status': None
        }
        response = ShiftView.put(self, request, id=self.shift.id)
        assert response.status_code == 400

    def test_shift_view_put_not_found(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-shifts', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'status': 'OPEN'
        }
        response = ShiftView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_shift_view_delete(self):
        """
        Ensure shift data is deleted via DELETE
        """
        path = reverse('api:id-shifts', kwargs={'id': self.shift.id})
        request = self.factory.delete(path)
        response = ShiftView.delete(self, request, id=self.shift.id)
        assert response.status_code == 204
        assert Shift.objects.filter(id=self.shift.id).count() == 0

    def test_shift_view_delete_invalid_shift(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-shifts', kwargs={'id': 9999})
        request = self.factory.delete(path)
        response = ShiftView.delete(self, request, id=9999)
        assert response.status_code == 404