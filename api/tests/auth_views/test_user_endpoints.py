from django.test import TestCase
from mixer.backend.django import mixer
# from django.apps import apps
# import json
from django.urls.base import reverse_lazy
from rest_framework_jwt.settings import api_settings

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class UpdateEmployerTestSuite(TestCase):
    """
    Endpoint tests for login
    """
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

    def test_get_user_unauthorized(self):
        """
        Try to reach without credentials
        """
        url = reverse_lazy('api:id-user', kwargs=dict(id=1))
        self.client.logout()
        response = self.client.get(url)
        self.assertEquals(response.status_code, 401)

    def test_get_user(self):
        """
        Try to reach with auth
        """
        url = reverse_lazy('api:id-user', kwargs=dict(id=1))
        self.client.force_login(self.test_user)

        response = self.client.get(url)
        # @todo, El endpoint tolera Cookie, HTTP Basic y JWT
        # como auth methods, por qué no puedo leer esto
        # sin JWT? @duda

        self.assertEquals(response.status_code, 401)
