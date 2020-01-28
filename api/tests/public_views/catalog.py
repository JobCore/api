from django.test import TestCase

from django.urls import reverse_lazy
from mock import patch
from io import BytesIO
from django.test.client import MULTIPART_CONTENT
from mixer.backend.django import mixer

from api.models import EmployeeDocument, Employee
from api.tests.mixins import WithMakeUser
from django.apps import apps

Position = apps.get_model('api', 'Position')

class PublicCatalog(TestCase, WithMakeUser):

    def setUp(self):
        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        position1 = mixer.blend('api.Position')
        position2 = mixer.blend('api.Position')
        position3 = mixer.blend('api.Position')
        position4 = mixer.blend('api.Position')
        position5 = mixer.blend('api.Position')

    def test_get_catalog_positions_sorted(self):

        url = reverse_lazy('api:get-catalog',
                           kwargs=dict(catalog_type='positions'))
        self.client.force_login(self.test_user_employee)

        response = self.client.get(url, content_type="application/json")
        
        print(response.json())
      
        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIsInstance(response_json, list)

        self.assertEquals(len(response_json), 1)
