from unittest import expectedFailure
from django.test import TestCase
from mixer.backend.django import mixer
import json
from django.urls import reverse_lazy
from decimal import Decimal
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

    def test_get_profile(self):
        """
        Get user profile
        """

        url = reverse_lazy('api:me-profiles')
        self.client.force_login(self.test_user_employee)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIsInstance(response_json, dict)
        self.assertIn('user', response_json)
        self.assertIn('employee', response_json)
        # self.assertNotIn(
        #     'employer', response_json, "It shouldn't show employer data")

    # @expectedFailure
    def test_get_profile_non_existing(self):
        """
        Get user profile for a user without profile
        """

        user = mixer.blend(
            'auth.User',
            username='testjoe',
            email='testjoe@testdoma.in',
            is_active=True,
        )

        user.set_password('pass1234')
        user.save()

        url = reverse_lazy('api:me-profiles')
        self.client.force_login(user)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            403,
            'It should return a success response')

    @expectedFailure
    def test_not_enough_info(self):
        """
        Edit profile with lacking data

        @todo Faltan validaciones en el serializer.
        """
        payload = {
            'picture': '',
            'bio': '',
            'location': '',
            'street_address': '',
            'country': '',
            'city': '',
            'state': '',
            'phone_number': '',
            'status': '',
        }

        url = reverse_lazy('api:me-profiles')
        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url, data=json.dumps(payload), content_type="application/json")

        self.assertEquals(
            response.status_code,
            401,
            'It should return an error response')

    def test_lat_lon_1(self):
        """
        Round Lat/lon to 6 decimal places
        """
        payload = {
            'latitude': 2e-7,
            'longitude': 2e-7,
        }

        url = reverse_lazy('api:me-profiles')
        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url, data=json.dumps(payload), content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return an error response')

        response_json = response.json()

        self.assertEquals(Decimal(response_json['latitude']), Decimal(0))
        self.assertEquals(Decimal(response_json['longitude']), Decimal(0))

    def test_lat_lon_2(self):
        """
        Round Lat/lon to 6 decimal places
        """
        payload = {
            'latitude': 6e-7,
            'longitude': 6e-7,
        }

        url = reverse_lazy('api:me-profiles')
        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url, data=json.dumps(payload), content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return an error response')

        response_json = response.json()

        self.assertEquals(
            Decimal(response_json['latitude']), Decimal('0.000001'))
        self.assertEquals(
            Decimal(response_json['longitude']), Decimal('0.000001'))
