from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils import timezone

from api.models import Clockin, PayrollPeriod, PayrollPeriodPayment
from api.tests.mixins import WithMakeUser, WithMakeShift

User = get_user_model()


class PayrollPeriodTestSuite(TestCase, WithMakeShift, WithMakeUser):
    fixtures = ['development/0-catalog.yaml', 'development/1-users.yaml', 'development/2-favlists.yaml',
                'development/3-shifts.yaml', 'development/4-clockins.yaml', 'development/5-document.yaml',
                'development/5-payroll.yaml']

    def setUp(self):
        begin_date = timezone.now() - timedelta(days=21)
        self.test_user_employer = User.objects.get(id=8)

        self.test_user_employer.profile.employer.payroll_period_starting_time = begin_date
        self.test_user_employer.profile.employer.save()
        # update existing data to ensure creation of a single period
        start_date = begin_date
        end_data = start_date + timedelta(days=7)
        PayrollPeriod.objects.filter(id=1).update(starting_at=start_date.strftime('%Y-%m-%d') + 'T00:00:00Z',
                                                  ending_at=end_data.strftime('%Y-%m-%d') + 'T23:59:59Z')
        start_date = begin_date + timedelta(days=7)
        end_data = start_date + timedelta(days=7)
        PayrollPeriod.objects.filter(id=1).update(starting_at=start_date.strftime('%Y-%m-%d') + 'T00:00:00Z',
                                                  ending_at=end_data.strftime('%Y-%m-%d') + 'T23:59:59Z')
        # update date and time from clockin registries, for usage in PayrollPeriod creation
        clockin_date = end_data + timedelta(days=2)
        Clockin.objects.filter(id=2).update(started_at=clockin_date.strftime('%Y-%m-%dT20:20:00Z'),
                                            ended_at=clockin_date.strftime('%Y-%m-%dT23:45:00Z'),
                                            status="APPROVED")
        clockin_date = clockin_date + timedelta(days=1)
        Clockin.objects.filter(id=3).update(started_at=clockin_date.strftime('%Y-%m-%dT20:20:00Z'),
                                            ended_at=clockin_date.strftime('%Y-%m-%dT23:45:00Z'),
                                            status="APPROVED")
        self.qty = PayrollPeriod.objects.count()
        self.payroll_payment_qty = PayrollPeriodPayment.objects.count()

    def test_period_generation(self):
        url = reverse_lazy('api:hook-generate_periods')
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PayrollPeriod.objects.count(), self.qty + 1)
        self.assertEqual(PayrollPeriodPayment.objects.count(), self.payroll_payment_qty + 1)
