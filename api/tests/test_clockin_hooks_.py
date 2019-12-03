from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta
from django.apps import apps

Clockin = apps.get_model('api', 'Clockin')

class HookTestClockinHooks(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for Invites
    """
    def setUp(self):
        position = mixer.blend('api.Position')

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
            )
        )

        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile_employee
        ) = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                stop_receiving_invites=True,
                positions=[position.id],
                maximum_job_distance_miles= 20
            ),
            profilekwargs = dict(
                latitude = 40,
                longitude = -73
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=timezone.now() - timedelta(days=3), ending_at=timezone.now() + timedelta(hours=8) - timedelta(days=3), position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
            employer=self.test_employer)

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=timezone.now() - timedelta(days=3), ending_at=timezone.now() + timedelta(hours=8) - timedelta(days=3), position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
            employer=self.test_employer)

        mixer.blend(
                'api.Clockin',
                employee=self.test_employee,
                shift=self.test_shift,
                author=self.test_profile_employee,
                ended_at=None,
                starting_at= timezone.now()- timedelta(days=3)
            )
        mixer.blend(
            'api.ShiftInvite',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee
        )
        self.client.force_login(self.test_user_employee)

    def test_expired_hook_after_delay(self):

        url = reverse_lazy("api:hook-process-expired-shifts")
        response = self.client.get(
            url,
            content_type="application/json")

        response_json = response.json()
       
        self.assertEquals(len(response.json()), 0, "No se debe recibir shift con fecha expirada")
