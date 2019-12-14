from django.test import TestCase
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser
from django.test.client import MULTIPART_CONTENT


class EmployeeMeTestSuite(TestCase, WithMakeUser):
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

        self.client.force_login(self.test_user_employee)

    def test_get_me(self):
        """
        Try to reach without credentials
        """
        url = reverse_lazy('api:me-employees')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertIn('user', response_json, response_json)
        self.assertIn('positions', response_json, response_json)
        self.assertIn('favoritelist_set', response_json, response_json)

        self.assertIsInstance(response_json['favoritelist_set'], list)
        self.assertIsInstance(response_json['positions'], list)

    def test_get_no_employee(self):
        """
        Try to reach without credentials
        """
        self.test_employee.delete()
        url = reverse_lazy('api:me-employees')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)

    def test_update_everything_me(self):
        payload = {
            'id': 9999,
            'response_time': 1000,
            'user': 12312312,
            'minimum_hourly_rate': '10.3',
            'stop_receiving_invites': True,
            'rating': 123.3,
            'total_ratings': 12312,
            'maximum_job_distance_miles': 30,
            'positions': [],
            'job_count': 123123,
            'badges': ['', '', ''],
            'created_at': '2010-01-01 00:00:00',
            'created_at': '2010-01-01 00:00:00',
        }

        url = reverse_lazy('api:me-employees')
        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertNotEquals(
            response_json['id'], payload['id'],
            'id should not change')

        self.assertEquals(
            response_json['response_time'], payload['response_time'])

        self.assertNotEquals(
            response_json['user'], payload['user'],
            'user id should not change')

        self.assertEquals(
            response_json['minimum_hourly_rate'],
            payload['minimum_hourly_rate'])

        self.assertEquals(
            response_json['stop_receiving_invites'],
            payload['stop_receiving_invites'])

        self.assertNotEquals(
            response_json['rating'],
            payload['rating'],
            'ratings should not be mutated')
        self.assertNotEquals(
            response_json['total_ratings'],
            payload['total_ratings'],
            'total ratings should not be mutated')

        self.assertEquals(
            response_json['maximum_job_distance_miles'],
            payload['maximum_job_distance_miles']
        )
        self.assertEquals(
            response_json['positions'],
            payload['positions']
        )
        self.assertNotEquals(
            response_json['job_count'],
            payload['job_count'],
            "job count shouldn't change here"
        )
        self.assertNotEquals(
            response_json['badges'],
            payload['badges'],
            "badges shouldn't change here"
        )
        self.assertNotEquals(
            response_json['created_at'],
            payload['created_at'],
            "timestamps shouldn't change"
        )
        self.assertNotEquals(
            response_json['created_at'],
            payload['created_at'],
            "timestamps shouldn't change"
        )

    def test_update_bad_positions(self):
        payload = {
            'positions': [9999999],
        }

        url = reverse_lazy('api:me-employees')
        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 400)

    def test_minimum_hours(self):
        payload = {
            'minimum_hourly_rate': 3,
        }

        url = reverse_lazy('api:me-employees')
        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 400)

        payload = {
            'minimum_hourly_rate': 8,
        }

        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 200)

    def test_max_job_distance(self):
        payload = {
            'maximum_job_distance_miles': 101,
        }

        url = reverse_lazy('api:me-employees')
        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 400)

        payload = {
            'maximum_job_distance_miles': 9,
        }

        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 400)

        payload = {
            'maximum_job_distance_miles': 10,
        }

        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 200)

        payload = {
            'maximum_job_distance_miles': 100,
        }

        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 200)
