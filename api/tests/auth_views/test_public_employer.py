from django.test import TestCase
from mixer.backend.django import mixer
# from django.apps import apps
# import json
from django.urls.base import reverse_lazy
# from rest_framework_jwt.settings import api_settings
# jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
import re


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

        self.employer = mixer.blend('api.Employer')
        self.employer.save()

        self.client.force_login(self.test_user)

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

    def test_unauthorized_get_employer(self):
        """
        Try to reach without credentials
        """
        url = reverse_lazy('api:get-employers')
        self.client.logout()
        response = self.client.get(url)
        self.assertEquals(response.status_code, 401)

    def test_authorized_list_employer(self):
        """
        Try to reach with credentials
        """
        url = reverse_lazy('api:get-employers')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        respjson = response.json()

        self.assertEquals(len(respjson), 1)

    def test_authorized_get_employer(self):
        """
        Try to reach with credentials
        """
        url = reverse_lazy('api:id-employers', kwargs={
            'id': self.employer.id
            })

        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        respjson = response.json()

        self.assertEquals(respjson['id'], self.employer.id)

    def test_authorized_get_employer_bad_id(self):
        """
        Try to reach with credentials
        """
        url = reverse_lazy('api:id-employers', kwargs={
            'id': 999
            })

        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

        url = re.sub(r"999", ':evil-data:', str(url))

        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)
