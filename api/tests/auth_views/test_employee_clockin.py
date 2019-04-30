from django.test import TestCase
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES, COMPLETED
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urlencode


class EmployeeClockInTestSuite(TestCase, WithMakeUser, WithMakeShift):
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
                maximum_clockin_delta_minutes=15,
                maximum_clockout_delay_minutes=15,
                rating=0,
                total_ratings=0,
            )
        )

        self.test_shift, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': SHIFT_STATUS_CHOICES[0][0],
                'maximum_clockin_delta_minutes': 15,
                'maximum_clockout_delay_minutes': 15,
                'starting_at': timezone.now(),
                'ending_at': timezone.now() + timedelta(hours=8)
            },
            employer=self.test_employer)

        self.test_shift2, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': SHIFT_STATUS_CHOICES[0][0],
                'maximum_clockin_delta_minutes': 15,
                'maximum_clockout_delay_minutes': 15,
                'starting_at': timezone.now(),
                'ending_at': timezone.now() + timedelta(hours=8)
            },
            employer=self.test_employer)

        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_shift,
        )

        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_shift2,
        )

        self.client.force_login(self.test_user_employee)

    def test_get_clockins(self):
        """
        Try to reach without credentials
        """
        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
        )

        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=self.test_shift2,
            author=self.test_profile_employee,
        )

        url = reverse_lazy('api:me-employees-clockins')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertEquals(len(response_json), 2)

        payload = {
            'shift': self.test_shift.id
        }
        response = self.client.get(url, data=payload)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertEquals(len(response_json), 1)

        payload = {
            'shift': self.test_shift2.id
        }
        response = self.client.get(url, data=payload)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertEquals(len(response_json), 1)

    def test_clocking_in_out_good(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60*15)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()

        self.assertEquals(
            response_json['started_at'],
            started_at.strftime('%FT%R:%S.%fZ')
            )

        ended_at = self.test_shift.ending_at - timedelta(seconds=60*15)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ended_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()

        self.assertEquals(
            response_json['ended_at'],
            ended_at.strftime('%FT%R:%S.%fZ')
            )

    def test_clocking_out_first(self):
        url = reverse_lazy('api:me-employees-clockins')

        ended_at = timezone.now() + timedelta(hours=2)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ended_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

    def test_clocking_in_before_shift_time(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at - timedelta(hours=1)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

    def test_clocking_in_after_shift_time(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.ending_at + timedelta(hours=1)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

    def test_clocking_in_without_clocking_out(self):
        mixer.blend(
            'api.ClockIn',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            started_at=self.test_shift.starting_at,
            latitude_in=-64,
            longitude_in=10,
            latitude_out=-64,
            longitude_out=10,
            ended_at=None,
            )

        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=15*60)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

    def test_clocking_in_far_away(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=15*60)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -63,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

    def test_clocking_in_lacking_data(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=15*60)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

    def test_clocking_out_lacking_data(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60*15)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)

        ended_at = timezone.now() + timedelta(hours=2)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ended_at,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

    def test_clocking_out_twice(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60*15)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()

        self.assertEquals(
            response_json['started_at'],
            started_at.strftime('%FT%R:%S.%fZ')
            )

        ended_at = self.test_shift.ending_at - timedelta(seconds=60*15)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ended_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()

        self.assertEquals(
            response_json['ended_at'],
            ended_at.strftime('%FT%R:%S.%fZ')
            )

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)
        response_json = response.json()

    def test_clocking_post_empty(self):
        url = reverse_lazy('api:me-employees-clockins')

        payload = {
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)
