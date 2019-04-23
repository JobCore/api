from django.test import TestCase
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from mock import patch
from io import BytesIO
from django.test.client import MULTIPART_CONTENT
from api.tests.mixins import WithMakeUser


class ProfileTestSuite(TestCase, WithMakeUser):
    """
    Endpoint tests for login
    """
    def setUp(self):
        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile
        ) = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

    @patch('cloudinary.uploader.upload')
    def test_post_profile(self, mocked_uploader):
        """
        Get user profile
        """

        mocked_uploader.return_value = {
            'secure_url': 'da_url'
        }

        url = reverse_lazy('api:me-profiles-image')
        self.client.force_login(self.test_user_employee)

        with BytesIO(b'the-data') as f:
            payload = {
                'image': f,
            }
            payload = self.client._encode_data(payload, MULTIPART_CONTENT)
            response = self.client.put(
                url, payload, content_type=MULTIPART_CONTENT)

        response_json = response.json()

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        self.assertEquals(response_json['picture'], 'da_url')

    def test_post_unknown_profile(self):
        """
        Get user profile
        """

        user = mixer.blend('auth.User')
        user.set_password('pass1234')
        user.save()

        url = reverse_lazy('api:me-profiles-image')
        self.client.force_login(user)

        with BytesIO(b'the-data') as f:
            payload = {
                'image': f,
            }
            payload = self.client._encode_data(payload, MULTIPART_CONTENT)
            response = self.client.put(
                url, payload, content_type=MULTIPART_CONTENT)

        self.assertEquals(
            response.status_code,
            403,
            'It should return an error response')
