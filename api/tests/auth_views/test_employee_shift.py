from django.test import TestCase
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES, COMPLETED
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urlencode


class EmployeeShiftTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for login
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
            ),
            employexkwargs=dict(
                ratings=0,
                total_ratings=0,
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
            employexkwargs=dict(
                rating=0,
                total_ratings=0,
            )
        )

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs={'status': SHIFT_STATUS_CHOICES[0][0]},
            employer=self.test_employer)

        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_shift,
            )

        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            )

        self.client.force_login(self.test_user_employee)

    def test_get_shifts(self):
        """
        Try to reach without credentials
        """
        url = reverse_lazy('api:me-employees-shift')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertEquals(len(response_json), 1)

    def test_filters_part_one(self):
        # one previously created
        shift_statuses = SHIFT_STATUS_CHOICES[1:]
        # 6 new choices

        shifts_to_do = [('status', status) for status, _ in shift_statuses]

        for field, value in shifts_to_do:
            shift, _, __ = self._make_shift(
                shiftkwargs={
                    field: value,
                    'starting_at': timezone.now() - timedelta(days=1),
                    'ending_at': timezone.now() + timedelta(days=1)
                },
                employer=self.test_employer)

            mixer.blend(
                'api.ShiftEmployee',
                employee=self.test_employee,
                shift=shift,
                success=True
            )

        url = reverse_lazy('api:me-employees-shift')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertEquals(len(response_json), 7)

        for value, _ in SHIFT_STATUS_CHOICES:
            search = {
                'status': value
            }

            querystring = urlencode(search)
            response = self.client.get('{}?{}'.format(url, querystring))
            self.assertEquals(response.status_code, 200)
            response_json = response.json()

            self.assertEquals(len(response_json), 1)

    def test_filters_part_two(self):

        url = reverse_lazy('api:me-employees-shift')

        # el primero que se crea en el setup esta expirado.
        search = {
            'expired': 'true',
        }

        querystring = urlencode(search)
        response = self.client.get('{}?{}'.format(url, querystring))
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertEquals(len(response_json), 1)

        shifts_to_do = [
            dict(
                starting_at=timezone.now() + timedelta(days=1),
                ending_at=timezone.now() + timedelta(days=2)
                ),
            dict(
                starting_at=timezone.now() - timedelta(days=2),
                ending_at=timezone.now() - timedelta(days=1)
                ),
            ]

        for shiftkwargs in shifts_to_do:
            shift, _, __ = self._make_shift(
                shiftkwargs={
                    'status': COMPLETED,
                    **shiftkwargs
                },
                employer=self.test_employer)

            mixer.blend(
                'api.ShiftEmployee',
                employee=self.test_employee,
                shift=shift,
                success=True
            )

        search = {
            'upcoming': 'true',
        }

        querystring = urlencode(search)
        response = self.client.get('{}?{}'.format(url, querystring))
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertEquals(len(response_json), 1)
