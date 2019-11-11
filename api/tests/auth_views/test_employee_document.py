from django.test import TestCase, override_settings
from django.test.client import MULTIPART_CONTENT
from django.urls import reverse_lazy
from io import BytesIO
from mixer.backend.django import mixer

from api.tests.mixins import WithMakeUser
from mock import patch


class EEDocumentTestCase(TestCase, WithMakeUser):
    def setUp(self):
        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile
        ) = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee12',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

        self.test_document = mixer.blend('api.Document')

    # @patch('cloudinary.uploader.upload')
    # def test_document_upload(self, mocked_uploader):
    #     """
    #     """
    #     mocked_uploader.return_value = {
    #         'secure_url': 'da_url'
    #     }
    #     url = reverse_lazy('api:me-documents')
    #     self.client.force_login(self.test_user_employee)
    #
    #     with BytesIO(b'the-data') as f:
    #         payload = {
    #             'document': f,
    #         }
    #         payload = self.client._encode_data(payload, MULTIPART_CONTENT)
    #         response = self.client.post(
    #             url, payload, content_type=MULTIPART_CONTENT)
    #
    #     response_json = response.json()
    #
    #     self.assertEquals(
    #         response.status_code,
    #         201,
    #         f'It should return a success response: {str(response_json)}')
    #
    # def test_document_delete(self):
    #     url = reverse_lazy('api:me-documents', kwargs=dict({
    #         'id': self.test_document.id}))
    #     self.client.force_login(self.test_user_employee)
    #     response = self.client.delete(url)
