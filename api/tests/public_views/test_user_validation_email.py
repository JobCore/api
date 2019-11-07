from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from rest_framework_jwt.settings import api_settings
from api.tests.mixins import WithMakeUser

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


@override_settings(STATICFILES_STORAGE=None)
class UserValidationEmailTestSuite(TestCase, WithMakeUser):
    """
    Endpoint tests for password reset
    """
    USER_VALID_URL = reverse_lazy('api:validate-email')

    def setUp(self):
        self.test_user, *_ = self._make_user(
            'employee',
            userkwargs=dict(
                username='test_user',
                email='test_user@testdoma.in',
                is_active=True,
            )
        )

    def test_with_bad_token(self):
        """
        Try to reach the view with a bad token
        """

        payload = {
            'token': ':really-evil-token:',
        }

        response = self.client.get(
            self.USER_VALID_URL,
            data=payload,
        )

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_reset_kind_of_bad_token(self):
        """
        Try to reach the form with a bad token, good shape, bad data
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

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

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

        self.assertEquals(
            response.status_code,
            200,
            'It should return an error response')

    def test_revalidate(self):
        """
        Try to revalidate user
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

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response = self.client.get(
            self.USER_VALID_URL,
            data=payload,
        )

        self.assertEquals(
            response.status_code,
            400,
            'It should return error when retry')
