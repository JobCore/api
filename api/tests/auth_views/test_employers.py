from django.test import TestCase
import json
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser


class EmployersTestSuite(TestCase, WithMakeUser):
    """
    Endpoint tests for login
    """
    def setUp(self):
        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

        self.test_user_employer, self.test_employer, _ = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer1',
                email='employer@testdoma.in',
                is_active=True,
            )
        )

    def test_get_all_employers(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:get-employers')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIsInstance(response_json, list)

        self.assertEquals(len(response_json), 1)

    def test_get_one_employer(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:id-employers',
                           kwargs=dict(id=self.test_employer.id))

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIsInstance(response_json, dict)
        self.assertEquals(response_json['id'], self.test_employer.id)
        self.assertEquals(response_json['bio'], self.test_employer.bio)
        self.assertEquals(response_json['website'], self.test_employer.website)
        self.assertEquals(response_json['title'], self.test_employer.title)

    def test_get_one_employer_non_existing(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:id-employers',
                           kwargs=dict(id=99999))

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_get_one_employer_bad_id(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:get-employers') + '/ZZZZZZz'

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_no_auth(self):
        """
        Unauthorized list
        """

        url = reverse_lazy('api:get-employers')

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            401,
            'It should return an error response')

    def test_update_employer_data(self):
        """
        Update employer data
        """

        url = reverse_lazy('api:id-employers',
                           kwargs=dict(id=self.test_employer.id))

        self.client.force_login(self.test_user_employer)

        payload = {
            'title': 'ABC',
            'bio': 'DEF',
            'website': 'GEF'
        }

        response = self.client.put(
            url, data=json.dumps(payload), content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIsInstance(response_json, dict)
        self.assertEquals(response_json['id'], self.test_employer.id)

        self.assertNotEquals(
            response_json['bio'], self.test_employer.bio)
        self.assertNotEquals(
            response_json['website'], self.test_employer.website)
        self.assertNotEquals(
            response_json['title'], self.test_employer.title)

        self.assertEquals(
            response_json['title'], 'ABC')
        self.assertEquals(
            response_json['bio'], 'DEF')
        self.assertEquals(
            response_json['website'], 'GEF')

    def test_update_employer_data_malicious_id(self):
        """
        Trying to spoof a custom ID for employer
        """

        url = reverse_lazy('api:id-employers',
                           kwargs=dict(id=self.test_employer.id))

        self.client.force_login(self.test_user_employer)

        payload = {
            'id': 9999,
            'title': 'ABC',
            'bio': 'DEF',
            'website': 'GEF'
        }

        response = self.client.put(
            url, data=json.dumps(payload), content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIsInstance(response_json, dict)
        self.assertEquals(response_json['id'], self.test_employer.id)

        self.assertNotEquals(
            response_json['bio'], self.test_employer.bio)
        self.assertNotEquals(
            response_json['website'], self.test_employer.website)
        self.assertNotEquals(
            response_json['title'], self.test_employer.title)

        self.assertEquals(
            response_json['title'], 'ABC')
        self.assertEquals(
            response_json['bio'], 'DEF')
        self.assertEquals(
            response_json['website'], 'GEF')

    def test_update_employer_data_employee(self):
        """
        Update employer data passing employee
        """

        url = reverse_lazy('api:id-employers',
                           kwargs=dict(id=self.test_employer.id))

        self.client.force_login(self.test_user_employee)

        payload = {
            'title': 'ABC',
            'bio': 'DEF',
            'website': 'GEF'
        }

        response = self.client.put(
            url, data=json.dumps(payload), content_type="application/json")

        self.assertEquals(
            response.status_code,
            403,
            'It should return an error response')
