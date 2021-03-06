from django.test import TestCase
from mixer.backend.django import mixer
from django.apps import apps
import json
from rest_framework_jwt.settings import api_settings
from api.tests.mixins import WithMakeUser
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


class LoginTestSuite(TestCase, WithMakeUser):
    """
    Endpoint tests for login
    """
    LOGIN_URL = '/api/login'

    def setUp(self):
        self.test_user, *_ = self._make_user(
            'employee',
            userkwargs=dict(
                username='test_user',
                email='test_user@testdoma.in',
                is_active=True,
            )
        )

    def _simple_login_flow(self, payload):
        """
        Login Helper
        """
        response = self.client.post(
            self.LOGIN_URL,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIn('token', response_json, 'it should have a token')
        self.assertIn('user', response_json, 'it should have user details')

        jwt_decoded = jwt_decode_handler(response_json['token'])

        self.assertEquals(
            self.test_user.id,
            response_json['user']['id'],
            'Response should have be the same user id')

        self.assertEquals(
            self.test_user.id,
            jwt_decoded['user_id'],
            'Token should have the same user id')

        self.assertEquals(
            self.test_user.username,
            response_json['user']['username'],
            'Response should have be the same username')

        self.assertEquals(
            self.test_user.username,
            jwt_decoded['username'],
            'Token should have the same username')

        self.assertEquals(
            self.test_user.email,
            response_json['user']['email'],
            'Response should have be the same email')

        self.assertEquals(
            self.test_user.email,
            jwt_decoded['email'],
            'Token should have the same email')

        return response_json

    def test_good_user_password(self):
        """
        Login with valid user/password
        """
        payload = {
            'username_or_email': 'test_user',
            'password': 'pass1234',
        }
        self._simple_login_flow(payload)

    def test_good_email_password(self):
        """
        Login with valid user/password
        """
        payload = {
            'username_or_email': 'test_user@testdoma.in',
            'password': 'pass1234',
        }
        self._simple_login_flow(payload)

    def test_no_password(self):
        """
        Login with no password
        """
        payload = {
            'username_or_email': 'test_user@testdoma.in',
            'password': '',
        }
        response = self.client.post(
            self.LOGIN_URL,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        response_json = response.json()

        self.assertIn(
            'password',
            response_json,
            'It should return feedback messages')

    def test_non_existing_username(self):
        """
        Login non-existing username
        """
        payload = {
            'username_or_email': 'test_userz@testdoma.in',
            'password': '',
        }

        response = self.client.post(
            self.LOGIN_URL,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        response_json = response.json()

        self.assertIn(
            'password',
            response_json,
            'It should return feedback messages')

    def test_no_email(self):
        """
        Login with no email
        """
        payload = {
            'username_or_email': '',
            'password': ':lolololol:',
        }
        response = self.client.post(
            self.LOGIN_URL,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        response_json = response.json()
        self.assertIn(
            'username_or_email',
            response_json,
            'It should return feedback messages')

    def test_nothing_provided(self):
        """
        Login with no email
        """
        payload = {
            'username_or_email': '',
            'password': '',
        }
        response = self.client.post(
            self.LOGIN_URL,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        response_json = response.json()
        self.assertIn(
            'username_or_email',
            response_json,
            'It should return feedback messages')
        self.assertIn(
            'password',
            response_json,
            'It should return feedback messages')

    def test_invalid_username_password(self):
        """
        Login with invalid user/password
        """
        payload = {
            'username_or_email': 'test_user',
            'password': ':lolololol:',
        }
        response = self.client.post(
            self.LOGIN_URL,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        response_json = response.json()
        self.assertIn(
            'non_field_errors',
            response_json,
            'It should return feedback messages')

    def test_invalid_email_password(self):
        """
        Login with invalid email/password
        """
        payload = {
            'username_or_email': 'test_user@testdoma.in',
            'password': ':lolololol:',
        }
        response = self.client.post(
            self.LOGIN_URL,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        response_json = response.json()
        self.assertIn(
            'non_field_errors',
            response_json,
            'It should return feedback messages')

    def test_login_inactive_user(self):
        """
        Login with an inactive user
        """
        inactive_user, *_ = self._make_user(
            'employee',
            userkwargs=dict(
                username='test_user2',
                email='test_user2@testdoma.in',
                is_active=False,
            )
        )

        payload = {
            'username_or_email': 'test_user2',
            'password': 'pass1234',
        }
        response = self.client.post(
            self.LOGIN_URL,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        response_json = response.json()
        self.assertIn(
            'non_field_errors',
            response_json,
            'It should return feedback messages')

    def test_login_with_regid(self):
        """
        Login with enabled Push Notifications
        """
        payload = {
            'username_or_email': 'test_user',
            'password': 'pass1234',
            'registration_id': ':push-notif-id:',
        }
        self._simple_login_flow(payload)

        FCMDevice = apps.get_model('api.FCMDevice')
        device = (
            FCMDevice.objects
            .filter(
                user=self.test_user,
                registration_id=payload['registration_id']
            ).first()
        )

        self.assertIsNotNone(device, 'Devise should be created')

    def test_login_with_regid_change_Devise(self):
        """
        Login with enabled Push Notifications
        """
        payload = {
            'username_or_email': 'test_user',
            'password': 'pass1234',
            'registration_id': ':push-notif-id-1:',
        }
        self._simple_login_flow(payload)

        FCMDevice = apps.get_model('api.FCMDevice')
        device1 = (
            FCMDevice.objects
            .filter(
                user=self.test_user,
                registration_id=payload['registration_id']
            ).first()
        )

        self.assertIsNotNone(device1, 'Devise should be created')

        payload['registration_id'] = ':push-z-id-2:'

        self._simple_login_flow(payload)

        device2 = (
            FCMDevice.objects
            .filter(
                user=self.test_user,
                registration_id=payload['registration_id']
            ).first()
        )

        self.assertIsNotNone(device2, 'Devise should be created')

        self.assertNotEquals(device1.registration_id, device2.registration_id)
