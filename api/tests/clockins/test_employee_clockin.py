from django.test import TestCase
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta
from django.apps import apps

Clockin = apps.get_model('api', 'Clockin')


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

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
        ).count()

        self.assertEquals(len(response_json), count)

        payload = {
            'shift': self.test_shift.id
        }

        response = self.client.get(url, data=payload)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()

        self.assertEquals(len(response_json), count)

        payload = {
            'shift': self.test_shift2.id
        }
        response = self.client.get(url, data=payload)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift2.id,
        ).count()

        self.assertEquals(len(response_json), count)

    def test_clocking_in_out_good(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60 * 15)

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

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()

        self.assertEquals(count, 1)

        ended_at = self.test_shift.ending_at - timedelta(seconds=60 * 15)

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

        qs_clockin = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        )

        self.assertEquals(qs_clockin.count(), 1)

        clockin = qs_clockin.get()

        self.assertEquals(clockin.id, response_json['id'])

        self.assertEquals(clockin.started_at, started_at)
        self.assertEquals(clockin.ended_at, ended_at)

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

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()

        self.assertEquals(count, 0)

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

        maximun = self.test_shift.maximum_clockin_delta_minutes
        started_at = self.test_shift.starting_at + timedelta(seconds=maximun * 60)

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

        started_at = self.test_shift.starting_at + timedelta(seconds=15 * 60)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -63,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    def test_clocking_in_lacking_data(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=15 * 60)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    def test_clocking_out_lacking_data(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60 * 15)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

        ended_at = timezone.now() + timedelta(hours=2)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ended_at,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        db_clockin = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).get()

        self.assertEquals(db_clockin.ended_at, None)

    #
    def test_clocking_out_twice(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60 * 15)

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

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

        self.assertEquals(
            response_json['started_at'],
            started_at.strftime('%FT%R:%S.%fZ')
        )

        ended_at = self.test_shift.ending_at - timedelta(seconds=60 * 15)

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

        db_clockin = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).get()

        self.assertEquals(
            response_json['ended_at'],
            ended_at.strftime('%FT%R:%S.%fZ')
        )

        payload['ended_at'] = payload['ended_at'] - timedelta(minutes=1)

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        self.assertEquals(db_clockin.ended_at, ended_at)

    #
    def test_clocking_post_empty(self):
        url = reverse_lazy('api:me-employees-clockins')

        payload = {
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    #
    def test_clocking_in_to_evil_shift(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60 * 15)

        payload = {
            'shift': ':9999:',
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    #
    def test_clocking_in_to_wrong_shift(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60 * 15)

        payload = {
            'shift': 9999,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    def test_clocking_in_to_non_belonging_shift(self):
        (
            new_user_employee,
            new_employee,
            new_profile_employe2
        ) = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee2',
                email='employee2@testdoma.in',
                is_active=True,
            ),
            employexkwargs=dict(
                ratings=0,
                total_ratings=0,
            )
        )
        new_shift, _, __ = self._make_shift(
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
            employee=new_employee,
            shift=new_shift,
        )

        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60 * 15)

        payload = {
            'shift': new_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    def test_clocking_out_to_non_belonging_shift(self):
        (
            new_user_employee,
            new_employee,
            new_profile_employe2
        ) = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee2',
                email='employee2@testdoma.in',
                is_active=True,
            ),
            employexkwargs=dict(
                ratings=0,
                total_ratings=0,
            )
        )
        new_shift, _, __ = self._make_shift(
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
            employee=new_employee,
            shift=new_shift,
        )

        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at + timedelta(seconds=60 * 15)

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

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

        self.assertEquals(
            response_json['started_at'],
            started_at.strftime('%FT%R:%S.%fZ')
        )

        ended_at = self.test_shift.ending_at - timedelta(seconds=60 * 15)

        payload = {
            'shift': new_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ended_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        db_clockin = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).get()

        self.assertEquals(db_clockin.ended_at, None)

    def test_clocking_in_before_delta_minutes(self):
        url = reverse_lazy('api:me-employees-clockins')

        maximun_plus_one = self.test_shift.maximum_clockin_delta_minutes + 1
        started_at = self.test_shift.starting_at - timedelta(seconds=60 * maximun_plus_one)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': started_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    def test_clocking_in_just_before_delta_minutes(self):
        url = reverse_lazy('api:me-employees-clockins')

        clockin_delta = self.test_shift.maximum_clockin_delta_minutes
        started_at = self.test_shift.starting_at - timedelta(seconds=60 * clockin_delta)

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

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

    def test_clocking_in_within_delta_minutes(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at

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

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

    #
    def test_clocking_out_within_time(self):
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ClockIn',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            started_at=self.test_shift.starting_at,
            latitude_in=-64,
            longitude_in=10,
            ended_at=None,
        )

        ended_at = self.test_shift.ending_at

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ended_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        print(response.content)
        self.assertEquals(response.status_code, 201)


        response_json = response.json()

        self.assertEquals(
            response_json['ended_at'],
            ended_at.strftime('%FT%R:%S.%fZ')
        )
        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

    def test_clocking_out_within_delta_minutes(self):
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ClockIn',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            started_at=self.test_shift.starting_at,
            latitude_in=-64,
            longitude_in=10,
            ended_at=None,
        )

        # the maximum allowed time to clock out
        clockout_delta = self.test_shift.maximum_clockout_delay_minutes
        ending_at = self.test_shift.ending_at + timedelta(seconds=60 * (clockout_delta - 1))

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ending_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        # trying a clock OUT on a shift within the delta out
        self.assertEquals(response.status_code, 201)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

    def test_clocking_out_after_delta_minutes(self):
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ClockIn',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            started_at=self.test_shift.starting_at,
            latitude_in=-64,
            longitude_in=10,
            ended_at=None,
        )

        # the maximum allowed time to clock out
        clockout_delta = self.test_shift.maximum_clockout_delay_minutes
        ending_at = self.test_shift.ending_at + timedelta(seconds=60 * (clockout_delta + 1))

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ending_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)

        # trying a clock OUT on a shift within the delta out
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)
