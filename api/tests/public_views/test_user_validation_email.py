from django.test import TestCase, override_settings
from unittest import expectedFailure, skipIf
from mixer.backend.django import mixer
from django.apps import apps
import json
from django.urls.base import reverse_lazy
from django.test import tag
from mock import patch, call
from rest_framework_jwt.settings import api_settings

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

@override_settings(STATICFILES_STORAGE=None)
@tag('here')
class UserValidationEmailTestSuite(TestCase):
    """
    Endpoint tests for password reset
    """
    USER_VALID_URL = reverse_lazy('api:validate-email')

    def setUp(self):
        self.test_user = self._make_user_with_profile(
            username='test_user',
            email='test_user@testdoma.in',
            is_active=True,
        )

    def _make_user_with_profile(self, **kwargs):
        test_user = mixer.blend(
            'auth.User', 
            **kwargs
            )

        test_user.set_password('pass1234')
        test_user.save()

        test_profile = mixer.blend('api.Profile', user=test_user)
        test_profile.save()
        return test_user

    @expectedFailure
    def test_with_bad_token(self):
        """
        Try to reach the view with a bad token

        @todo: no fufiona si el token es muy invalido.
        raises: jwt.exceptions.DecodeError
        """

        payload = {
            'token': ':really-evil-token:',
        }

        response = self.client.get(
            self.USER_VALID_URL,
            data=payload,
        )

        self.assertEquals(response.status_code, 400, 'It should return an error response')
    
    @expectedFailure
    def test_reset_kind_of_bad_token(self):
        """
        Try to reach the form with a bad token, good shape, bad data

        @todo: no fufiona, jwt.exceptions.InvalidSignatureError
            además, nunca se usa el jwt_payload_handler interno 
            cuando se llama a api_settings.JWT_PAYLOAD_HANDLER

        """

        jtw_payload = jwt_payload_handler(self.test_user)

        token = jwt_encode_handler(jtw_payload) + 'A=!'

        payload = {
            'token': token,
        }

        response = self.client.get(
            self.USER_VALID_URL,
            data=payload,
        )

        self.assertEquals(response.status_code, 400, 'It should return an error response')

    def test_reset_good_token(self):
        """
        Try to reach the form with a good token.
        """

        jtw_payload = jwt_payload_handler(self.test_user)

        token = jwt_encode_handler(jtw_payload)

        payload = {
            'token': token,
        }

        response = self.client.get(
            self.USER_VALID_URL,
            data=payload,
        )

        self.assertEquals(response.status_code, 200, 'It should return an error response')


