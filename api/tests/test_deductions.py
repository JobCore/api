from django.test import TestCase

from django.urls import reverse_lazy
from django.test.client import MULTIPART_CONTENT

from api.models import EmployerDeduction, Employer
from api.tests.mixins import WithMakeUser


class EmployeeDocumentTestSuite(TestCase, WithMakeUser):

    def setUp(self):
        self.test_user_employer, self.test_employer, self.test_profile_employer = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer1',
                email='employer@testdoma.in',
                is_active=True,
            )
        )
        self.test_user_employer2, self.test_employer2, self.test_profile_employer2 = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer2',
                email='employer2@testdoma.in',
                is_active=True,
            )
        )
        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

    def test_add_deduction_by_employee(self):
        url = reverse_lazy('api:me-employer-deduction')
        self.client.force_login(self.test_user_employee)

        data = {
            "employer": self.test_employer.id,
            "name": "Test Deduction",
            "value": 1.1,
        }

        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 403, response.content)

    def test_add_deduction(self):
        url = reverse_lazy('api:me-employer-deduction')
        self.client.force_login(self.test_user_employer)

        data = {
            "employer": self.test_employer.id,
            "name": "Test Deduction",
            "description": "Test Description",
            "value": 1.1,
        }

        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 201, response.content)
        response_json = response.json()
        self.assertEqual(EmployerDeduction.objects.count(), 1, response_json)
        self.assertIsInstance(response_json.pop('id'), int, response_json)
        self.assertDictEqual(response_json,
                             {"name": data['name'], "description": data['description'],
                              "type": "PERCENTAGE", "value": data['value'], "lock": False,
                              "employer": data['employer']},
                             response_json)

    def test_get(self):
        url = reverse_lazy('api:me-employer-deduction')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, response.content)
        response_json = response.json()
        self.assertEqual(len(response_json), 2, response_json)
        for item in response_json:
            self.assertIsInstance(item.get('id'), int, item)
            self.assertIsInstance(item.get('name'), str, item)
            self.assertEqual(item.get('employer'), self.test_user_employer.profile.employer.id, item)
            self.assertTrue(item.get('lock'), item)
            self.assertIsInstance(item.get('type'), str, item)
            self.assertIsInstance(item.get('value'), float, item)
            self.assertIsInstance(item.get('description'), str, item)

        data = {
            "employer_id": self.test_employer2.id,
            "name": "Test Deduction",
            "description": "Test Description",
            "value": 1.1,
        }
        EmployerDeduction.objects.create(**data)

        # Only predefined deductions, because I'm not the owner
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, response.content)
        response_json = response.json()
        self.assertEqual(len(response_json), 2, response_json)

        data = {
            "employer_id": self.test_employer.id,
            "name": "Test Deduction",
            "description": "Test Description",
            "value": 1.1,
        }
        EmployerDeduction.objects.create(**data)

        response = self.client.get(url)
        self.assertEquals(response.status_code, 200, response.content)
        response_json = response.json()
        self.assertEquals(len(response_json), 3, response_json)
        self.assertEquals(response_json[2].get("name"), data['name'], response_json)
        self.assertEquals(response_json[2].get("description"), data['description'], response_json)
        self.assertEquals(response_json[2].get("value"), data['value'], response_json)
        self.assertEquals(response_json[2].get("employer"), data['employer_id'], response_json)

    def test_update(self):
        self.client.force_login(self.test_user_employer)

        data = {
            "employer_id": self.test_employer.id,
            "name": "Test Deduction",
            "description": "Test Description",
            "value": 1.1,
        }
        original_deduction = EmployerDeduction.objects.create(**data)

        new_data = {
            "name": "New Test Deduction",
            "description": "New Test Description",
            "value": 25.0,
        }
        url = reverse_lazy('api:me-employer-single-deduction', kwargs=dict(id=original_deduction.id))
        response = self.client.put(url, new_data, content_type='application/json')
        self.assertEquals(response.status_code, 200, response.content)
        results = response.json()
        self.assertEquals(results.get("name"), new_data['name'], results)
        self.assertEquals(results.get("description"), new_data['description'], results)
        self.assertEquals(results.get("value"), new_data['value'], results)

    def test_delete(self):
        self.client.force_login(self.test_user_employer)

        data = {
            "employer_id": self.test_employer.id,
            "name": "Test Deduction",
            "description": "Test Description",
            "value": 1.1,
        }
        original_deduction = EmployerDeduction.objects.create(**data)

        self.assertEquals(EmployerDeduction.objects.count(), 1, EmployerDeduction.objects.all())
        url = reverse_lazy('api:me-employer-single-deduction', kwargs=dict(id=original_deduction.id))
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 202, response.content)
        self.assertEquals(EmployerDeduction.objects.count(), 0, EmployerDeduction.objects.all())
