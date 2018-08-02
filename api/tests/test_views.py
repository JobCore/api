import pytest
import json
import datetime
from api.models import *
from api.views import *
from api.serializers import *
from api.pagination import CustomPagination
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import User, AnonymousUser
from mixer.backend.django import mixer
from rest_framework.test import APITestCase, APIRequestFactory
from django.urls import reverse, resolve


@pytest.mark.django_db
class TestViews(APITestCase, CustomPagination):
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

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
        # Tokens with linked user
        cls.valid_token_employee = mixer.blend(
            AccessToken, user_id=cls.user_employee.id)
        cls.valid_token_employer = mixer.blend(
            AccessToken, user_id=cls.user_employer.id)
        # Tokens without linked user
        cls.invalid_token = mixer.blend(AccessToken)
        # Request factory
        cls.factory = APIRequestFactory()

    # TOKEN

    def test_token_view(self):
        """
        Ensure user data is returned when token is sent via POST
        """
        path = reverse('api:token-user')
        request = self.factory.post(path)
        request.data = {'token': self.valid_token_employer}
        request.content_type = 'application/json'
        response = TokenUserView.post(self, request)
        assert response.status_code == 200

    def test_token_view_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:token-user')
        request = self.factory.post(path)
        request.data = {'token': self.invalid_token}
        request.content_type = 'application/json'
        response = TokenUserView.post(self, request)
        assert response.status_code == 404

    # LOGIN

    def test_user_login_view_success(self):
        """
        Ensure successful login
        """
        path = reverse('api:login')
        request = self.factory.post(path)
        request.data = {
            'email': self.user_employer.email,
            'password': self.password
        }
        response = UserLoginView.post(self, request)
        assert response.status_code == 200

    def test_user_login_view_user_without_token(self):
        """
        Ensure successful login and token generation for user
        """
        path = reverse('api:login')
        request = self.factory.post(path)
        request.data = {
            'email': self.unauthorized_user.email,
            'password': self.password
        }
        response = UserLoginView.post(self, request)
        assert response.status_code == 200

    def test_user_login_view_email_error(self):
        """
        Ensure error code when invalid email is provided
        """
        path = reverse('api:login')
        request = self.factory.post(path)
        request.data = {
            'email': 'unauthorized@gmail.com',
            'password': '*unauthorized123'
        }
        response = UserLoginView.post(self, request)
        assert response.status_code == 401

    def test_user_login_view_email_required_error(self):
        """
        Ensure error code when no email is provided
        """
        path = reverse('api:login')
        request = self.factory.post(path)
        request.data = {
            'password': '*unauthorized123'
        }
        response = UserLoginView.post(self, request)
        assert response.status_code == 401

    def test_user_login_view_email_not_registered_error(self):
        """
        Ensure error code when non registered email is provided
        """
        path = reverse('api:login')
        request = self.factory.post(path)
        request.data = {
            'email': "email_not_registerd@gmail.com",
            'password': '*unauthorized123'
        }
        response = UserLoginView.post(self, request)
        assert response.status_code == 401

    def test_user_login_view_password_error(self):
        """
        Ensure error code when invalid password is provided
        """
        path = reverse('api:login')
        request = self.factory.post(path)
        request.data = {
            'email': self.user_employer.email,
            'password': '*unauthorized123'
        }
        response = UserLoginView.post(self, request)
        assert response.status_code == 401

    # REGISTER

    def test_employer_register_success(self):
        """
        Ensure successful employer register
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': 'New_employer',
            'first_name': 'Employer name',
            'last_name': 'Employer lastname',
            'email': 'new_employer@gmail.com',
            'password': self.password,
            'type': 'employer'
        }
        response = UserRegisterView.post(self, request)
        user = User.objects.get(email=request.data['email'])
        profile = Profile.objects.get(user_id=user.id)
        employer = Employer.objects.get(profile=profile.id)
        assert response.status_code == 201
        assert employer.profile.user.username == request.data['username']

    def test_employee_register_success(self):
        """
        Ensure successful employee register
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': 'New_employee',
            'first_name': 'Employee name',
            'last_name': 'Employee lastname',
            'email': 'new_employee@gmail.com',
            'password': self.password,
            'type': 'employee'
        }
        response = UserRegisterView.post(self, request)
        user = User.objects.get(email=request.data['email'])
        profile = Profile.objects.get(user_id=user.id)
        employee = Employee.objects.get(profile=profile.id)
        assert response.status_code == 201
        assert employee.profile.user.username == request.data['username']

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

    def test_employer_register_existing_username(self):
        """
        Ensure employer register error if username is already in use
        """
        path = reverse('api:register')
        request = self.factory.post(path)
        request.data = {
            'username': self.user_employer.username,
            'email': 'some_email@gmail.com',
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

    # PASSWORD RESET

    def test_password_reset_success(self):
        """
        Ensure successful employer register
        """
        path = reverse('api:password-reset-email')
        request = self.factory.post(path)
        request.data = {
            'email': self.user_employer.email
        }
        response = UserEmailView.post(self, request)
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
        response = UserEmailView.post(self, request)
        assert response.status_code == 404

    # USER

    def test_user_view_get(self):
        """
        Ensure user data is returned via GET
        """
        path = reverse('api:id-user', kwargs={'id': self.user_employer.id})
        request = self.factory.get(path)
        response = UserView.get(self, request, id=self.user_employer.id)
        assert response.status_code == 200

    def test_user_view_get_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-user', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = UserView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_user_view_put(self):
        """
        Ensure user data is updated via PUT
        """
        path = reverse('api:id-user', kwargs={'id': self.user_employer.id})
        request = self.factory.put(path)
        request.data = {
            'first_name': 'NewName',
            'last_name': 'NewLastname'
        }
        response = UserView.put(self, request, id=self.user_employer.id)
        assert response.status_code == 200
        user = User.objects.get(id=self.user_employer.id)
        assert user.first_name == request.data['first_name']

    def test_user_view_put_existing_email(self):
        """
        Ensure error code when user is updated with unique existing email
        """
        path = reverse('api:id-user', kwargs={'id': self.unauthorized_user.id})
        request = self.factory.put(path)
        request.data = {
            'email': self.user_employer.email
        }
        response = UserView.put(self, request, id=self.unauthorized_user.id)
        assert response.status_code == 304

    def test_user_view_put_existing_username(self):
        """
        Ensure error code when user is updated with unique existing username
        """
        path = reverse('api:id-user', kwargs={'id': self.unauthorized_user.id})
        request = self.factory.put(path)
        request.data = {
            'username': self.user_employer.username
        }
        response = UserView.put(self, request, id=self.unauthorized_user.id)
        assert response.status_code == 304

    def test_user_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-user', kwargs={'id': self.user_employer.id})
        request = self.factory.put(path)
        request.data = {
            'email': '',
        }
        response = UserView.put(self, request, id=self.user_employer.id)
        assert response.status_code == 304

    def test_user_view_put_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-user', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'first_name': 'NewName',
            'last_name': 'NewLastname'
        }
        response = UserView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_user_view_patch_password_change_success(self):
        """
        Ensure user password is changed via PATCH
        """
        path = reverse('api:id-user', kwargs={'id': self.user_employer.id})
        request = self.factory.patch(path)
        request.data = {
            'old_password': self.password,
            'new_password': '*NewPassword123'
        }
        response = UserView.patch(self, request, id=self.user_employer.id)
        assert response.status_code == 200
        user = User.objects.get(id=self.user_employer.id)
        assert user.check_password(request.data['new_password'])

    def test_user_view_patch_password_wrong_old_password(self):
        """
        Ensure error code is returned when old password is wrong
        """
        path = reverse('api:id-user', kwargs={'id': self.user_employer.id})
        request = self.factory.patch(path)
        request.data = {
            'old_password': '*87654321',
            'new_password': '*NewPassword123'
        }
        response = UserView.patch(self, request, id=self.user_employer.id)
        assert response.status_code == 400

    def test_user_view_patch_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-user', kwargs={'id': 9999})
        request = self.factory.patch(path)
        request.data = {
            'old_password': self.password,
            'new_password': '*NewPassword123'
        }
        response = UserView.patch(self, request, id=9999)
        assert response.status_code == 404

    def test_user_view_patch_error(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-user', kwargs={'id': self.user_employer.id})
        request = self.factory.patch(path)
        request.data = {
            'old_password': self.password,
            'password': '*NewPassword123'
        }
        response = UserView.patch(self, request, id=self.user_employer.id)
        assert response.status_code == 400

    def test_user_view_delete(self):
        """
        Ensure user data is deleted via DELETE
        """
        user = self.user_employer
        path = reverse('api:id-user', kwargs={'id': self.user_employer.id})
        request = self.factory.delete(path)
        response = UserView.delete(self, request, id=self.user_employer.id)
        assert response.status_code == 204
        assert User.objects.filter(email=user.email).count() == 0

    def test_user_view_delete_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-user', kwargs={'id': 9999})
        request = self.factory.delete(path)
        response = UserView.delete(self, request, id=9999)
        assert response.status_code == 404

    # EMPLOYEE

    def test_employee_view_get_single(self):
        """
        Ensure single employee data is returned via GET
        """
        path = reverse('api:id-employees', kwargs={'id': self.employee.id})
        request = self.factory.get(path)
        response = EmployeeView.get(self, request, id=self.employee.id)
        assert response.status_code == 200

    def test_employee_view_get_single_invalid_employee(self):
        """
        Ensure single employee data is returned via GET
        """
        path = reverse('api:id-employees', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = EmployeeView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_employee_view_put(self):
        """
        Ensure employee data is updated via PUT
        """
        path = reverse('api:id-employees',
                       kwargs={'id': self.employee.id})
        request = self.factory.put(path)
        request.data = {
            'response_time': 20,
            'minimum_hourly_rate': 10.0,
            'rating': 4.5,
            'badges': [self.badge.id],
            'positions': [self.position.id]
        }
        response = EmployeeView.put(self, request, id=self.employee.id)
        assert response.status_code == 200
        employee = Employee.objects.get(id=self.employee.id)
        assert employee.response_time == request.data['response_time']

    def test_employee_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-employees', kwargs={'id': self.employee.id})
        request = self.factory.put(path)
        request.data = {
            'badges': ['responsible'],
        }
        response = EmployeeView.put(self, request, id=self.employee.id)
        assert response.status_code == 304

    def test_employee_view_put_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-employees', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'response_time': 20,
            'minimum_hourly_rate': 10.0,
            'rating': 4.5,
            'badges': [self.badge.id],
            'positions': [self.position.id]
        }
        response = EmployeeView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_employee_view_delete(self):
        """
        Ensure employee data is deleted via DELETE
        """
        employee = self.employee
        path = reverse('api:id-employees', kwargs={'id': self.employee.id})
        request = self.factory.delete(path)
        response = EmployeeView.delete(self, request, id=self.employee.id)
        assert response.status_code == 204
        assert Employee.objects.filter(profile=employee.profile).count() == 0

    def test_employee_view_delete_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-employees', kwargs={'id': 9999})
        request = self.factory.delete(path)
        response = EmployeeView.delete(self, request, id=9999)
        assert response.status_code == 404

    # EMPLOYEER

    def test_employer_view_get_single(self):
        """
        Ensure single employer data is returned via GET
        """
        path = reverse('api:id-employers', kwargs={'id': self.employer.id})
        request = self.factory.get(path)
        response = EmployerView.get(self, request, id=self.employer.id)
        assert response.status_code == 200

    def test_employer_view_get_single_invalid_employer(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-employers', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = EmployerView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_employer_view_get_all(self):
        """
        Ensure all employers are returned via GET
        """
        path = reverse('api:get-employers')
        request = self.factory.get(path)
        response = EmployerView.get(self, request)
        assert response.status_code == 200

    def test_employer_view_put(self):
        """
        Ensure employer data is updated via PUT
        """
        path = reverse('api:id-employers',
                       kwargs={'id': self.employer.id})
        request = self.factory.put(path)
        request.data = {
            'title': 'Employer Title',
            'website': 'www.employer.com',
            'response_time': 20,
            'rating': 4.5,
            'badges': [self.badge.id]
        }
        response = EmployerView.put(self, request, id=self.employer.id)
        assert response.status_code == 200
        employer = Employer.objects.get(id=self.employer.id)
        assert employer.title == request.data['title']

    def test_employer_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-employers', kwargs={'id': self.employer.id})
        request = self.factory.put(path)
        request.data = {
            'badges': ['responsible'],
        }
        response = EmployerView.put(self, request, id=self.employer.id)
        assert response.status_code == 304

    def test_employer_view_put_invalid_employer(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-employers', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'title': 'Employer Title',
            'website': 'www.employer.com',
            'response_time': 20,
            'rating': 4.5,
            'badges': [self.badge.id]
        }
        response = EmployerView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_employer_view_delete(self):
        """
        Ensure employer data is deleted via DELETE
        """
        employer = self.employer
        path = reverse('api:id-employers', kwargs={'id': self.employer.id})
        request = self.factory.delete(path)
        response = EmployerView.delete(self, request, id=self.employer.id)
        assert response.status_code == 204
        assert Employer.objects.filter(profile=employer.profile).count() == 0

    def test_employer_view_delete_invalid_employer(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-employers', kwargs={'id': 9999})
        request = self.factory.delete(path)
        response = EmployerView.delete(self, request, id=9999)
        assert response.status_code == 404

    # PROFILE

    def test_profile_view_get_single(self):
        """
        Ensure single profile data is returned via GET
        """
        path = reverse('api:id-profiles',
                       kwargs={'id': self.employer_profile.id})
        request = self.factory.get(path)
        response = ProfileView.get(self, request, id=self.employer_profile.id)
        assert response.status_code == 200

    def test_profile_view_get_single_invalid_profile(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-profiles', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = ProfileView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_profile_view_get_all(self):
        """
        Ensure profiles are returned via GET
        """
        path = reverse('api:get-profiles')
        request = self.factory.get(path)
        response = ProfileView.get(self, request)
        assert response.status_code == 200

    def test_profile_view_put(self):
        """
        Ensure profile data is updated via PUT
        """
        path = reverse('api:id-profiles',
                       kwargs={'id': self.employer_profile.id})
        request = self.factory.put(path)
        request.data = {
            'bio': 'My bio',
            'picture': 'http://lorempixel.com/300/300/people',
            'location': 'My city',
        }
        response = ProfileView.put(self, request, id=self.employer_profile.id)
        assert response.status_code == 200
        profile = Profile.objects.get(id=self.employer_profile.id)
        assert profile.picture == request.data['picture']

    def test_profile_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-profiles',
                       kwargs={'id': self.employer_profile.id})
        request = self.factory.put(path)
        request.data = {
            'birth_date': '00-00-0000',
        }
        response = ProfileView.put(self, request, id=self.employer_profile.id)
        assert response.status_code == 304

    def test_profile_view_put_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-profiles', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'bio': 'My bio',
            'picture': 'http://lorempixel.com/300/300/people',
            'location': 'My city',
        }
        response = ProfileView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_favorite_list_view_get_single(self):
        """
        Ensure single list data is returned via GET
        """
        path = reverse('api:id-favlists', kwargs={'id': self.favlist.id})
        request = self.factory.get(path)
        response = FavListView.get(self, request, id=self.favlist.id)
        assert response.status_code == 200

    def test_favorite_list_view_get_single_invalid_list(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-favlists', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = FavListView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_favorite_list_view_get_all(self):
        """
        Ensure all lists are returned via GET
        """
        path = reverse('api:get-favlists')
        request = self.factory.get(path)
        response = FavListView.get(self, request)
        assert response.status_code == 200

    def test_favorite_list_view_post(self):
        """
        Ensure list is created via POST
        """
        path = reverse('api:get-favlists')
        request = self.factory.post(path)
        request.data = {
            'title': 'New List Title',
            'employees': [self.employee.id],
            'owner': self.employer.id
        }
        response = FavListView.post(self, request)
        assert response.status_code == 201
        assert FavoriteList.objects.filter(title='New List Title').count() == 1

    def test_favorite_list_view_post_invalid_data(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:get-favlists')
        request = self.factory.post(path)
        request.data = {
            'title': 'List Title',
            'employees': ['Employer #1']
        }
        response = FavListView.post(self, request)
        assert response.status_code == 400

    def test_favorite_list_view_put(self):
        """
        Ensure list data is updated via PUT
        """
        path = reverse('api:id-favlists',
                       kwargs={'id': self.favlist.id})
        request = self.factory.put(path)
        request.data = {
            'title': 'List Title',
            'employees': [self.employee.id]
        }
        response = FavListView.put(self, request, id=self.favlist.id)
        assert response.status_code == 200
        favlist = FavoriteList.objects.get(id=self.favlist.id)
        assert favlist.title == request.data['title']

    def test_favorite_list_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-favlists', kwargs={'id': self.favlist.id})
        request = self.factory.put(path)
        request.data = {
            'employees': ['Employee #1'],
        }
        response = FavListView.put(self, request, id=self.favlist.id)
        assert response.status_code == 304

    def test_favorite_list_view_put_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-favlists', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'title': 'List Title',
            'employees': [self.employee.id]
        }
        response = FavListView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_favorite_list_view_delete(self):
        """
        Ensure list data is deleted via DELETE
        """
        favlist = self.favlist
        path = reverse('api:id-favlists', kwargs={'id': self.favlist.id})
        request = self.factory.delete(path)
        response = FavListView.delete(self, request, id=self.favlist.id)
        assert response.status_code == 204
        assert FavoriteList.objects.filter(
            owner=self.employer.id).count() == 0

    def test_favorite_list_view_delete_invalid_list(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-favlists', kwargs={'id': 9999})
        request = self.factory.delete(path)
        response = FavListView.delete(self, request, id=9999)
        assert response.status_code == 404

    # SHIFT

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
        request.data = {
            'status': 'OPEN',
            'date': '2018-03-31',
            'start_time': "13:00",
            'finish_time': "16:00",
            'rating': 3,
            'candidates': [self.employee.id],
            'employees': [self.employee.id],
            'venue': self.venue.id,
            'position': self.position.id,
            'application_restriction': 'FAVORITES',
            'maximum_allowed_employees': 10,
            'minimum_hourly_rate': 8,
            'minimum_allowed_rating': 3,
            'allowed_from_list': [self.favlist.id],
            'required_badges': [self.badge.id]
        }
        response = ShiftView.post(self, request)
        print(response.data)
        assert response.status_code == 201
        assert Shift.objects.filter(status='OPEN').count() == 1

    def test_shift_view_post_invalid_data(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:get-shifts')
        request = self.factory.post(path)
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
        request.data = {
            'status': 'CANCELLED',
            'date': '2018-01-31',
            'start_time': "13:00",
            'finish_time': "16:00",
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
            'required_badges': []
        }
        response = ShiftView.put(self, request, id=self.shift.id)
        assert response.status_code == 200
        shift = Shift.objects.get(id=self.shift.id)
        assert shift.application_restriction == request.data['application_restriction']

    def test_shift_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-shifts', kwargs={'id': self.shift.id})
        request = self.factory.put(path)
        request.data = {
            'status': None
        }
        response = ShiftView.put(self, request, id=self.shift.id)
        assert response.status_code == 304

    def test_shift_view_put_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-shifts', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'status': 'OPEN',
            'date': '2018-03-31',
            'start_time': "13:00T00:00",
            'finish_time': "16:00T00:00",
            'rating': 3,
            'candidates': [self.employee.id],
            'employees': self.employee.id,
            'venue': self.venue.id,
            'position': self.position.id,
            'application_restriction': 'ANYONE',
            'maximum_allowed_employees': 10,
            'minimum_hourly_rate': 8,
            'minimum_allowed_rating': 3,
            'allowed_from_list': [self.favlist.id],
            'required_badges': [self.badge.id]
        }
        response = ShiftView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_shift_view_delete(self):
        """
        Ensure shift data is deleted via DELETE
        """
        shift = self.shift
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

    # VENUE

    def test_venue_view_get_single(self):
        """
        Ensure single venue data is returned via GET
        """
        path = reverse('api:id-venues', kwargs={'id': self.venue.id})
        request = self.factory.get(path)
        response = VenueView.get(self, request, id=self.venue.id)
        assert response.status_code == 200

    def test_venue_view_get_single_invalid_venue(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-venues', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = VenueView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_venue_view_get_all(self):
        """
        Ensure all venues are returned via GET
        """
        path = reverse('api:get-venues')
        request = self.factory.get(path)
        response = VenueView.get(self, request)
        assert response.status_code == 200

    def test_venue_view_post(self):
        """
        Ensure venue data is created via POST
        """
        path = reverse('api:get-venues')
        request = self.factory.post(path)
        request.data = {
            'title': 'New Venue Title',
            'street': 'New Venue Street',
            'country': 'New Venue Country',
            'state': 'New Venue State',
            'zip_code': 12345
        }
        response = VenueView.post(self, request)
        assert response.status_code == 201
        assert Venue.objects.filter(title='New Venue Title').count() == 1

    def test_venue_view_post_invalid_data(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:get-venues')
        request = self.factory.post(path)
        request.data = {
            'title': None
        }
        response = VenueView.post(self, request)
        assert response.status_code == 400

    def test_venue_view_put(self):
        """
        Ensure venue data is updated via PUT
        """
        path = reverse('api:id-venues', kwargs={'id': self.venue.id})
        request = self.factory.put(path)
        request.data = {
            'title': 'Venue Title',
            'street': 'Venue Street',
            'country': 'Venue Country',
            'state': 'Venue State',
            'zip_code': 12345
        }
        response = VenueView.put(self, request, id=self.venue.id)
        assert response.status_code == 200
        venue = Venue.objects.get(id=self.venue.id)
        assert venue.title == request.data['title']

    def test_venue_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-venues', kwargs={'id': self.venue.id})
        request = self.factory.put(path)
        request.data = {
            'title': None,
            'zip_code': '12345'
        }
        response = VenueView.put(self, request, id=self.venue.id)
        assert response.status_code == 304

    def test_venue_view_put_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-venues', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'title': 'Venue Title',
            'street': 'Venue Street',
            'country': 'Venue Country',
            'state': 'Venue State',
            'zip_code': 'Venue Zip Code'
        }
        response = VenueView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_venue_view_delete(self):
        """
        Ensure venue data is deleted via DELETE
        """
        venue = self.venue
        path = reverse('api:id-venues', kwargs={'id': self.venue.id})
        request = self.factory.delete(path)
        response = VenueView.delete(self, request, id=self.venue.id)
        assert response.status_code == 204
        assert Venue.objects.filter(id=self.venue.id).count() == 0

    def test_venue_view_delete_invalid_venue(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-venues', kwargs={'id': 9999})
        request = self.factory.delete(path)
        response = VenueView.delete(self, request, id=9999)
        assert response.status_code == 404

    # POSITION

    def test_position_view_get_single(self):
        """
        Ensure single position data is returned via GET
        """
        path = reverse('api:id-positions', kwargs={'id': self.position.id})
        request = self.factory.get(path)
        response = PositionView.get(self, request, id=self.position.id)
        assert response.status_code == 200

    def test_position_view_get_single_invalid_position(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-positions', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = PositionView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_position_view_get_all(self):
        """
        Ensure all positions are returned via GET
        """
        path = reverse('api:get-positions')
        request = self.factory.get(path)
        response = PositionView.get(self, request)
        assert response.status_code == 200

    def test_position_view_post(self):
        """
        Ensure position data is created via POST
        """
        path = reverse('api:get-positions')
        request = self.factory.post(path)
        request.data = {
            'title': 'New Position Title',
            'street': 'New Position Street',
            'country': 'New Position Country',
            'state': 'New Position State',
            'zip_code': 12345
        }
        response = PositionView.post(self, request)
        assert response.status_code == 201
        assert Position.objects.filter(title='New Position Title').count() == 1

    def test_position_view_post_invalid_data(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:get-positions')
        request = self.factory.post(path)
        request.data = {
            'title': None
        }
        response = PositionView.post(self, request)
        assert response.status_code == 400

    def test_position_view_put(self):
        """
        Ensure position data is updated via PUT
        """
        path = reverse('api:id-positions', kwargs={'id': self.position.id})
        request = self.factory.put(path)
        request.data = {
            'title': 'Position Title'
        }
        response = PositionView.put(self, request, id=self.position.id)
        assert response.status_code == 200
        position = Position.objects.get(id=self.position.id)
        assert position.title == request.data['title']

    def test_position_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-positions', kwargs={'id': self.position.id})
        request = self.factory.put(path)
        request.data = {
            'title': None
        }
        response = PositionView.put(self, request, id=self.position.id)
        assert response.status_code == 304

    def test_position_view_put_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-positions', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'title': 'Position Title'
        }
        response = PositionView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_position_view_delete(self):
        """
        Ensure position data is deleted via DELETE
        """
        position = self.position
        path = reverse('api:id-positions', kwargs={'id': self.position.id})
        request = self.factory.delete(path)
        response = PositionView.delete(self, request, id=self.position.id)
        assert response.status_code == 204
        assert Position.objects.filter(id=self.position.id).count() == 0

    def test_position_view_delete_invalid_position(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-positions', kwargs={'id': 9999})
        request = self.factory.delete(path)
        response = PositionView.delete(self, request, id=9999)
        assert response.status_code == 404
    # BADGE

    def test_badge_view_get_single(self):
        """
        Ensure badge data is returned via GET
        """
        path = reverse('api:id-badges', kwargs={'id': self.badge.id})
        request = self.factory.get(path)
        response = BadgeView.get(self, request, id=self.badge.id)
        assert response.status_code == 200

    def test_badge_view_get_single_invalid_badge(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-badges', kwargs={'id': 9999})
        request = self.factory.get(path)
        response = BadgeView.get(self, request, id=9999)
        assert response.status_code == 404

    def test_badge_view_get_all(self):
        """
        Ensure all badges are returned via GET
        """
        path = reverse('api:get-badges')
        request = self.factory.get(path)
        response = BadgeView.get(self, request)
        assert response.status_code == 200

    def test_badge_view_post(self):
        """
        Ensure badge data is created via POST
        """
        path = reverse('api:get-badges')
        request = self.factory.post(path)
        request.data = {
            'title': 'New Badge Title',
            'image_url': 'http://lorempixel.com/300/300/people'
        }
        response = BadgeView.post(self, request)
        assert response.status_code == 201
        assert Badge.objects.filter(title='New Badge Title').count() == 1

    def test_badge_view_post_invalid_data(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:get-badges')
        request = self.factory.post(path)
        request.data = {
            'title': None
        }
        response = BadgeView.post(self, request)
        assert response.status_code == 400

    def test_badge_view_put(self):
        """
        Ensure badge data is updated via PUT
        """
        path = reverse('api:id-badges', kwargs={'id': self.badge.id})
        request = self.factory.put(path)
        request.data = {
            'title': 'New Badge Title',
            'image_url': 'http://lorempixel.com/300/300/people'
        }
        response = BadgeView.put(self, request, id=self.badge.id)
        assert response.status_code == 200
        badge = Badge.objects.get(id=self.badge.id)
        assert badge.title == request.data['title']

    def test_badge_view_put_invalid_update(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-badges', kwargs={'id': self.badge.id})
        request = self.factory.put(path)
        request.data = {
            'title': None
        }
        response = BadgeView.put(self, request, id=self.badge.id)
        assert response.status_code == 304

    def test_badge_view_put_invalid_user(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-badges', kwargs={'id': 9999})
        request = self.factory.put(path)
        request.data = {
            'title': 'New Badge Title',
            'image_url': 'http://lorempixel.com/300/300/people'
        }
        response = BadgeView.put(self, request, id=9999)
        assert response.status_code == 404

    def test_badge_view_delete(self):
        """
        Ensure badge data is deleted via DELETE
        """
        badge = self.badge
        path = reverse('api:id-badges', kwargs={'id': self.badge.id})
        request = self.factory.delete(path)
        response = BadgeView.delete(self, request, id=self.badge.id)
        assert response.status_code == 204
        assert Badge.objects.filter(id=self.badge.id).count() == 0

    def test_badge_view_delete_invalid_badge(self):
        """
        Ensure error code when invalid data is provided
        """
        path = reverse('api:id-badges', kwargs={'id': 9999})
        request = self.factory.delete(path)
        response = BadgeView.delete(self, request, id=9999)
        assert response.status_code == 404
