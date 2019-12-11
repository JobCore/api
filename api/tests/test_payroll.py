from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta
from django.apps import apps

Employer = apps.get_model('api', 'Employer')
Profile = apps.get_model('api', 'Profile')

@override_settings(STATICFILES_STORAGE=None)
class Payroll(TestCase, WithMakeUser, WithMakeShift):
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
            ),
            employexkwargs=dict(
                rating=0,
                created_at=timezone.now()
            )
        )

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(hours=8)

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=14),
            employer=self.test_employer)

        self.test_payrollperiod = mixer.blend(
            'api.PayrollPeriod',
            shift=self.test_shift,
            employer=self.test_employer
        )

        self.client.force_login(self.test_user_employer)

    def test_payroll_setting_update(self):
        url = reverse_lazy('api:me-employer')
        url_process_payroll = reverse_lazy('api:hook-generate_periods')
        response_process_payroll = self.client.get(
            url_process_payroll + "?employer="+str(self.test_employer.id),
            content_type="application/json")

        self.assertEquals(
            response_process_payroll.status_code,
            400,
            'You have to setup your payroll configuration')

        self.assertEquals(
            self.test_employer.payroll_period_starting_time, None)
        payload = {
            'payroll_period_starting_time': timezone.now(),
            'payroll_period_length': 15,
            'payroll_period_type': 'DAYS'
        }   

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")
 
        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        updated_employer = Profile.objects.get(
            user=self.test_user_employer).employer
  
        self.assertNotEqual(
            updated_employer.payroll_period_starting_time, None)

    def test_first_payrollperiod(self):
        (
            self.test_user_employer2,
            self.test_employer2,
            self.test_profile_employer2
        ) = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer2',
                email='employer2@testdoma.in',
                is_active=True,
            ),
            employexkwargs=dict(
                rating=0,
                created_at=timezone.now(),
                payroll_period_starting_time= timezone.now(),
                payroll_period_length= 7,
                payroll_period_type= 'DAYS'
            )
        )
        url_process_payroll = reverse_lazy('api:hook-generate_periods')
        response_process_payroll = self.client.get(
            url_process_payroll + "?employer="+str(self.test_employer2.id),
            content_type="application/json")

        res = response_process_payroll.json()
 
        self.assertEquals(
            response_process_payroll.json()[0]['starting_at'], self.test_profile_employer2.created_at)