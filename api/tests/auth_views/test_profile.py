from unittest import expectedFailure
from django.test import TestCase
from mixer.backend.django import mixer
import json
from django.urls import reverse_lazy
from decimal import Decimal
# from rest_framework_jwt.settings import api_settings
# jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


class ProfileTestSuite(TestCase):
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

    def _make_user(
            self, kind, userkwargs={}, employexkwargs={}, profilekwargs={}):

        if kind not in ['employee', 'employer']:
            raise RuntimeError('Do you know what are you doing?')

        user = mixer.blend('auth.User', **userkwargs)
        user.set_password('pass1234')
        user.save()

        emptype = 'api.Employee' if kind == 'employee' else 'api.Employer'

        if kind == 'employee':
            employexkwargs.update({
                'user': user
            })

        emp = mixer.blend(emptype, **employexkwargs)
        emp.save()

        profilekwargs = profilekwargs.copy()
        profilekwargs.update({
            'user': user,
            kind: emp,
        })

        profile = mixer.blend('api.Profile', **profilekwargs)
        profile.save()

        return user, emp, profile

    # @expectedFailure
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

        @todo esto falla miserablemente por:
            User.profile.RelatedObjectDoesNotExist: User has no profile.
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

        @todo esto falla miserablemente, no hay validaciones
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
