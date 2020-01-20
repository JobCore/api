from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from django.apps import apps
from io import BytesIO
from django.test.client import MULTIPART_CONTENT
import random
from mock import patch

EmployeeDocument = apps.get_model('api', 'EmployeeDocument')
Document = apps.get_model('api', 'Document')
@override_settings(STATICFILES_STORAGE=None)
class DocumentTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for clockinout
    """
    def setUp(self):

        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile_employee
        ) = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

        (
            self.test_user_employer,
            self.test_employer,
            self.test_profile_employer
        ) = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer1',
                email='employer@testdoma.in',
                is_active=True,
            ),
        )
    
    def test_get_all_documents(self):
        mixer.blend(
            'api.EmployeeDocument',
            employee=self.test_employee,
            status="PENDING"
        )

        url = reverse_lazy('api:employee-document')
        self.client.force_login(self.test_user_employee)
        response = self.client.get(url, content_type='application/json')
        json_response = response.json()
        print((json_response))
        self.assertEquals(response.status_code, 200, response.content)
    def test_default_get_employee_document_ARCHIVED(self):
    # Test that, by default, archived document dont show on the default list of documents GET /emplyees/me/document
        mixer.blend(
            'api.EmployeeDocument',
            employee=self.test_employee,
            status="PENDING"
        )
        mixer.blend(
            'api.EmployeeDocument',
            employee=self.test_employee,
            status="APPROVED"
        )
        mixer.blend(
            'api.EmployeeDocument',
            employee=self.test_employee,
            status="ARCHIVED"
        )
        mixer.blend(
            'api.EmployeeDocument',
            employee=self.test_employee,
            status="REJECTED"
        )
        url = reverse_lazy('api:employee-document')
        self.client.force_login(self.test_user_employee)
        response = self.client.get(url, content_type='application/json')
        json_response = response.json()
        print(len(json_response))
        self.assertEquals(response.status_code, 200, response.content)
        self.assertEquals(len(json_response), 3, response.content)
        self.assertEquals(list(filter(lambda x: x == 'ARCHIVED', json_response)), [], 'It must be empty array because we dont want to show an archived employee document')
        self.assertEqual(EmployeeDocument.objects.filter(employee=self.test_employee, status__in=['ARCHIVED']).count(), 1) #still in the data

    # def test_employee_document_filtering(self):
    # Test filters for getting the list of documents:
        # self.random = random.randint(0, 2)
        # document_type = ['identity', 'employment', 'form']
        # status = ['PENDING', 'APPROVED', 'REJECTED']
        # mixer.blend(
        #         'api.EmployeeDocument',
        #         employee=self.test_employee,
        #         status='APPROVED',
        #         document_type = mixer.blend(
        #             'api.Document',
        #             title='employment'
        #         )
        #     )
        # for x in range(0, 3):
        #     mixer.blend(
        #         'api.EmployeeDocument',
        #         employee=self.test_employee,
        #         status=status[self.random],
        #         document_type = mixer.blend(
        #             'api.Document',
        #             title=document_type[x]
        #         )
        #     )
        #filtering type
        # url = reverse_lazy('api:employee-document', kwargs=dict(
        #     status='APPROVED'
        # ))
        # self.client.force_login(self.test_user_employee)
        # response = self.client.get(url, content_type='application/json')
        # json_response = response.json()
        # print(json_response)
        # self.assertEquals(response.status_code, 500, response.content)

    # @patch('cloudinary.uploader.upload')
    # def test_upload_document_validate_identity_TRUE(self, mocked_uploader):
        # Test if you upload a document of validate_identity = true all the others with validate_identity = true document for the same exmployee should be archived (historical)
        # mocked_uploader.return_value = {
        #     'secure_url': 'http://a-valid.url/for-the-doc'
        # }
        # url = reverse_lazy('api:employee-document')
        # self.client.force_login(self.test_user_employee)
        # document_type =  mixer.blend('api.Document', validates_identity=True)
        # document_type1 =  mixer.blend('api.Document', validates_identity=True)
        # document_type2 =  mixer.blend('api.Document', validates_identity=True)
        # mixer.blend(
        #         'api.EmployeeDocument',
        #         employee=self.test_employee,
        #         status='PENDING',
        #         document_type = document_type1
        #     )
        # mixer.blend(
        #         'api.EmployeeDocument',
        #         employee=self.test_employee,
        #         status='PENDING',
        #         document_type = document_type2
        #     )
        # with BytesIO(b'the-data') as f:
        #     payload = {
        #         'document': f,
        #         'document_type': document_type.id
        #     }
        #     response = self.client.post(url, payload, content_type=MULTIPART_CONTENT)
        #     json_response = response.json()
        #     print(json_response)
        #     print(EmployeeDocument.objects.filter(employee=self.test_employee, status__in=['ARCHIVED']).count())
        # self.assertEquals(
        #     response.status_code,
        #     201,
        #     f'It should return a success response: {str(response.content)}')
        # self.assertEquals(
        #     EmployeeDocument.objects.filter(employee=self.test_employee, status__in=['ARCHIVED']).count(),
        #     2,
        #     f'There should be two archived documents')

    # @patch('cloudinary.uploader.upload')
    # def test_upload_document_validate_identity_REJECTED_PENDING(self, mocked_uploader):
        # Repeat the above but if is previous document status for the same type are PENDING OR REJECTED they should be deleted.
        # mocked_uploader.return_value = {
        #     'secure_url': 'http://a-valid.url/for-the-doc'
        # }
        # url = reverse_lazy('api:employee-document')
        # self.client.force_login(self.test_user_employee)
        # document_type =  mixer.blend('api.Document', validates_identity=True)
        # document_type1 =  mixer.blend('api.Document', validates_identity=True)
        # document_type2 =  mixer.blend('api.Document', validates_identity=True)
        # mixer.blend(
        #         'api.EmployeeDocument',
        #         employee=self.test_employee,
        #         status='PENDING',
        #         document_type = document_type1
        #     )
        # mixer.blend(
        #         'api.EmployeeDocument',
        #         employee=self.test_employee,
        #         status='REJECTED',
        #         document_type = document_type2
        #     )
        # with BytesIO(b'the-data') as f:
        #     payload = {
        #         'document': f,
        #         'document_type': document_type.id
        #     }
        #     response = self.client.post(url, payload, content_type=MULTIPART_CONTENT)
        #     json_response = response.json()
        #     print(json_response)
        #     print(EmployeeDocument.objects.filter(employee=self.test_employee, status__in=['ARCHIVED']).count())
        # self.assertEquals(
        #     response.status_code,
        #     201,
        #     f'It should return a success response: {str(response.content)}')
        # self.assertEquals(
        #     EmployeeDocument.objects.filter(employee=self.test_employee).count(),
        #     1,
        #     f'There should be two archived documents')

    # @patch('cloudinary.uploader.upload')
    # def test_default_get_employee_document_double_approve_same_type(self, mocked_uploader):
    # # Test that, by default, archived document dont show on the default list of documents GET /emplyees/me/document

    #     document = mixer.blend(
    #             'api.Document',
    #             title='employment'
    #         )      
    #     mixer.blend(
    #         'api.EmployeeDocument',
    #         employee=self.test_employee,
    #         status="APPROVED",
    #         document_type = document     
    #     )

    #     mocked_uploader.return_value = {
    #         'secure_url': 'http://a-valid.url/for-the-doc'
    #     }
    #     url = reverse_lazy('api:employee-document')
    #     self.client.force_login(self.test_user_employee)

    #     with BytesIO(b'the-data') as f:
        
    #         payload = {
    #             'document': f,
    #             'document_type': document.id
    #         }
    #         # payload = self.client._encode_data(payload, MULTIPART_CONTENT)
    #         response = self.client.post(url, payload, content_type=MULTIPART_CONTENT)


        # url_get_document = reverse_lazy('api:employee-document')
        # self.client.force_login(self.test_user_employee)
        # response = self.client.get(url_get_document, content_type='application/json')
        # json_response = response.json()
        # print(json_response)
        # print(len(json_response))
        # self.assertEquals(response.status_code, 400, 'Cannot Have 2 Employee document with the status approved')


    # @patch('cloudinary.uploader.upload')
    # def test_verification_status_deductions(self, mocked_uploader):
    #     (
    #         self.test_user_employee2,
    #         self.test_employee2,
    #         self.test_profile_employee2
    #     ) = self._make_user(
    #         'employee',
    #         userkwargs=dict(
    #             username='employee2',
    #             email='employee2@testdoma.in',
    #             is_active=True,
    #         ),
    #         employexkwargs=dict(
    #             employment_verification_status='APPROVED'
    #         )
    #     )

    #     mocked_uploader.return_value = {
    #         'secure_url': 'http://a-valid.url/for-the-doc'
    #     }

    #     url = reverse_lazy('api:employee-document')
    #     self.client.force_login(self.test_user_employee2)

    #     with BytesIO(b'the-data') as f:
    #         _type = mixer.blend('api.Document')
    #         payload = {
    #             'document': f,
    #             'document_type': _type.id
    #         }
    #         response = self.client.post(url, payload, content_type=MULTIPART_CONTENT)

    #     self.assertEquals(
    #         response.status_code,
    #         201,
    #         f'It should return a success response: {str(response.content)}')
   