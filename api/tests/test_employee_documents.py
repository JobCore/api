from django.test import TestCase

from django.urls import reverse_lazy
from mock import patch
from io import BytesIO
from django.test.client import MULTIPART_CONTENT

from api.models import EmployeeDocument, Employee
from api.tests.mixins import WithMakeUser


class EmployeeDocumentTestSuite(TestCase, WithMakeUser):

    def setUp(self):
        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile_employee
        ) = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1234',
                email='employee1234@testdoma.in',
                is_active=True,
            )
        )

    @patch('cloudinary.uploader.upload')
    def test_add_document(self, mocked_uploader):
        mocked_uploader.return_value = {
            'secure_url': 'http://a-valid.url/for-the-doc'
        }
        url = reverse_lazy('api:employee-document')
        self.client.force_login(self.test_user_employee)

        with BytesIO(b'the-data') as f:
            payload = {
                'document': f,
            }
            # payload = self.client._encode_data(payload, MULTIPART_CONTENT)
            response = self.client.post(url, payload, content_type=MULTIPART_CONTENT)
        print(response.content)
        self.assertEquals(
            response.status_code,
            201,
            f'It should return a success response: {str(response.content)}')

    @patch('cloudinary.uploader.upload')
    def test_get_my_documents(self, mocked_uploader):
        document = {
            'document': 'http://a-valid.url/for-the-doc',
            "employee_id": Employee.objects.all()[0].id
        }

        EmployeeDocument.objects.create(**document)
        url = reverse_lazy('api:employee-document')
        self.client.force_login(self.test_user_employee)
        response = self.client.get(url, content_type='application/json')
        json_response = response.json()
        self.assertEquals(response.status_code, 200, response.content)
        self.assertEquals(len(json_response), 1, response.content)
        self.assertEquals(json_response[0].get("document"), document.get("document"), response.content)
