from django.test import TestCase

from django.urls import reverse_lazy

from api.models import AppVersion
from api.tests.mixins import WithMakeUser


class AppVersionTestSuite(TestCase, WithMakeUser):

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

    def test_get_my_documents(self):
        AppVersion.objects.create(version=10)
        url = reverse_lazy('api:version')
        self.client.force_login(self.test_user_employee)
        response = self.client.get(url, content_type='application/json')
        json_response = response.json()
        self.assertEquals(response.status_code, 200, response.content)
        self.assertEquals(json_response.get("version"), 10, response.content)
