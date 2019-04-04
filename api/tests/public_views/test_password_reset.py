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
class PasswordResetTestSuite(TestCase):
    """
    Endpoint tests for password reset
    """
    PW_RESET_URL = reverse_lazy('api:password-reset-email')

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

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_send_link_with_good_input_notify_enabled(self, mocked_requests):
        """
        Send password change email with good data
        """
        mocked_requests.post.return_value.status_code = 200

        payload = {
            'email': 'test_user@testdoma.in',
        }
        response = self.client.post(
            self.PW_RESET_URL, 
            data=json.dumps(payload), 
            content_type="application/json")

        self.assertEquals(response.status_code, 200, 'It should return a success response')
        self.assertEquals(mocked_requests.post.called, True, 'It should have called requests.post to send mail')

    
    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=False)
    def test_send_link_with_good_input_notify_disabled(self, mocked_requests):
        """
        Send password change email (actually dont) with good data.
        """
        payload = {
            'email': 'test_user@testdoma.in',
        }
        response = self.client.post(
            self.PW_RESET_URL, 
            data=json.dumps(payload), 
            content_type="application/json")

        self.assertEquals(response.status_code, 200, 'It should return a success response')
        self.assertEquals(mocked_requests.post.called, False, 'It should NOT have called requests.post to send mail')
    
    @patch('api.utils.email.requests')
    def test_change_pw_non_existing_user(self, mocked_requests):
        """
        Send password change email (actually dont) with good data.
        """
        payload = {
            'email': 'nonsensical_user@testdoma.in',
        }
        response = self.client.post(
            self.PW_RESET_URL, 
            data=json.dumps(payload), 
            content_type="application/json")

        self.assertEquals(response.status_code, 404, 'It should return an error response')
        self.assertEquals(mocked_requests.post.called, False, 'It should NOT have called requests.post to send mail')
    
    @patch('api.utils.email.requests')
    def test_change_pw_no_mail(self, mocked_requests):
        """
        Send password change email (actually dont) with good data.
        """
        payload = {
        }
        response = self.client.post(
            self.PW_RESET_URL, 
            data=json.dumps(payload), 
            content_type="application/json")

        self.assertEquals(response.status_code, 400, 'It should return an error response')
        self.assertEquals(mocked_requests.post.called, False, 'It should NOT have called requests.post to send mail')
    
    @expectedFailure
    def test_reset_bad_token(self):
        """
        Try to reach the form with a bad token

        @todo: no fufiona si el token es muy invalido.
        raises: jwt.exceptions.DecodeError
        """

        # jtw_payload = jwt_payload_handler({
        #     "user_id": self.test_user.id
        # })

        # token = jwt_encode_handler(jtw_payload)

        payload = {
            'token': ':really-evil-token:',
        }

        response = self.client.get(
            self.PW_RESET_URL,
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
            self.PW_RESET_URL,
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
            self.PW_RESET_URL,
            data=payload,
        )

        self.assertEquals(response.status_code, 200, 'It should return an error response')

    @expectedFailure
    def test_reset_pw_bad_token(self):
        """
        Reset password with a bad token

        @todo: 
            jwt.exceptions.DecodeError: Not enough segments
            File "env/lib64/python3.6/site-packages/jwt/api_jws.py", line 183, in _load
        """

        payload = {
            'token': ':evil-token:',
            'new_password': 'password123456',
            'repeat_password': 'password789012',
        }

        response = self.client.put(
            self.PW_RESET_URL,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEquals(response.status_code, 200, 'It should return an error response')
    
    @expectedFailure
    def test_reset_pw_kindof_good_token(self):
        """
        Reset password with a bad token

        @todo: 
            jwt.exceptions.InvalidSignatureError: Signature verification failed
            File "env/lib64/python3.6/site-packages/jwt/api_jws.py", line 223, in _verify_signature
        """
        jtw_payload = jwt_payload_handler(self.test_user)

        token = jwt_encode_handler(jtw_payload)

        payload = {
            'token': token+'A=!',
            'new_password': 'password123456',
            'repeat_password': 'password789012',
        }

        response = self.client.put(
            self.PW_RESET_URL,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEquals(response.status_code, 200, 'It should return an error response')
    
    @expectedFailure
    def test_reset_pw_not_matching_pw(self):
        """
        Reset password with not maching password1/2

        @todo: 
            NameError: name 'ValidationError' is not defined
            File "api/serializers/auth_serializer.py", line 166, in validate
        """

        jtw_payload = jwt_payload_handler(self.test_user)

        token = jwt_encode_handler(jtw_payload)

        payload = {
            'token': token,
            'new_password': 'password123456',
            'repeat_password': 'password789012',
        }

        response = self.client.put(
            self.PW_RESET_URL,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEquals(response.status_code, 200, 'It should return an error response')
    
    def test_reset_pw_all_good(self):
        """
        Reset password with good input

        @todo: 
            NameError: name 'ValidationError' is not defined
            File "api/serializers/auth_serializer.py", line 166, in validate
        """

        jtw_payload = jwt_payload_handler(self.test_user)

        token = jwt_encode_handler(jtw_payload)

        payload = {
            'token': token,
            'new_password': 'password123456',
            'repeat_password': 'password123456',
        }

        response = self.client.put(
            self.PW_RESET_URL,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEquals(response.status_code, 204, 'It should return a success response')


