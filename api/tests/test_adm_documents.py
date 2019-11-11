from django.test import TestCase
from django.test.client import MULTIPART_CONTENT
from django.urls import reverse_lazy

from io import BytesIO
from mixer.backend.django import mixer
from mock import patch

from api.tests.mixins import WithMakeUser
from api.models import Document


# class AdminDocumentTestSuite(TestCase, WithMakeUser):
#     def setUp(self):
#         (
#             self.test_user_employee,
#             self.test_employee,
#             self.test_profile_employee
#         ) = self._make_user(
#             'employee',
#             userkwargs=dict(
#                 username='employee',
#                 email='employee@testdoma.in',
#                 is_active=True,
#             )
#         )
#
#     @patch('cloudinary.uploader.upload')
#     def test_add_document(self, mocked_uploader):
#         """
#
#         :param mocked_uploader:
#         :return:
#         """
#         mocked_uploader.return_value = {
#             'secure_url': 'da_url'
#         }
#
#         url = reverse_lazy('api:admin-document')
#         self.client.force_login(self.test_user_employee)
#
#         with BytesIO(b'the-data') as f:
#             payload = {
#                 'document': f,
#             }
#             payload = self.client._encode_data(payload, MULTIPART_CONTENT)
#             response = self.client.post(
#                 url, payload, content_type=MULTIPART_CONTENT)
#
#         self.assertEquals(
#             response.status_code,
#             201,
#             f'It should return a success response: {str(response.content)}')
#
#     def test_get_document(self):
#         document = mixer.blend('api.Document')
#         url = reverse_lazy('api:admin-get-document', kwargs={
#             'document_id': document.id})
#
#         self.client.force_login(self.test_user_employee)
#         response = self.client.get(url)
#         self.assertEquals(response.status_code, 200)
#         self.assertEquals(response.json(), document.document)
#
#     def test_change_status_document(self):
#         self.client.force_login(self.test_user_employee)
#         document = mixer.blend('api.Document', state=Document.PENDING)
#         url = reverse_lazy('api:admin-get-document', kwargs={
#             'document_id': document.id})
#         payload = {'state': Document.APPROVED}
#         response = self.client.put(url, data=payload, content_type='application/json')
#         document.refresh_from_db()
#         self.assertEquals(document.state, Document.APPROVED)
