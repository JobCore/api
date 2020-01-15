from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta, datetime
from django.apps import apps
import pytz

Employer = apps.get_model('api', 'Employer')
Profile = apps.get_model('api', 'Profile')

@override_settings(STATICFILES_STORAGE=None)
class TestShiftApplication(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for clockinout
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
            )
        )

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(hours=8)

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=12),
            employer=self.test_employer)

    
        self.client.force_login(self.test_user_employer)

    # def test_employee_accepted_delete_other_jobs_with_the_same_time(self):
    #     #Si a un employee lo aceptan en un trabajo deben eliminarse las otras aplicaciones con el mismo tiempo del trabajo aceptado. Deben recibir una notification de que han sido eliminada
    #     #enhancement has not been made
        

    