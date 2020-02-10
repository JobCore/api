from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils import timezone

from api.models import Clockin, EmployeePayment, PayrollPeriod, PayrollPeriodPayment

User = get_user_model()


class PayrollPeriodTestSuite(TestCase):
    fixtures = ['development/0-catalog.yaml', 'development/1-users.yaml', 'development/2-favlists.yaml',
                'development/3-shifts.yaml', 'development/4-clockins.yaml', 'development/5-document.yaml',
                'development/5-payroll.yaml']

    def setUp(self):
        begin_date = timezone.now() - timedelta(days=21)
        self.test_user_employer = User.objects.get(id=1)
        self.test_user_employer2 = User.objects.get(id=9)
        self.test_user_employee = User.objects.get(id=2)

        self.test_user_employer.profile.employer.payroll_period_starting_time = begin_date
        self.test_user_employer.profile.employer.save()
        # update existing data to ensure creation of a single period
        start_date = begin_date
        end_data = start_date + timedelta(days=7)
        PayrollPeriod.objects.filter(id=1).update(starting_at=start_date.strftime('%Y-%m-%d') + 'T00:00:00Z',
                                                  ending_at=end_data.strftime('%Y-%m-%d') + 'T23:59:59Z')
        start_date = begin_date + timedelta(days=7)
        end_data = start_date + timedelta(days=7)
        PayrollPeriod.objects.filter(id=2).update(starting_at=start_date.strftime('%Y-%m-%d') + 'T00:00:00Z',
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
        self.assertEqual(response.status_code, 200, response.content.decode())
        self.assertEqual(PayrollPeriod.objects.count(), self.qty + 1)
        self.assertEqual(PayrollPeriodPayment.objects.count(), self.payroll_payment_qty + 2)
        response_json = response.json()
        self.assertEqual(len(response_json), 1)
        obj = response_json[0]
        self.assertIsInstance(obj.get('id'), int, response_json)
        self.assertEqual(obj.get('length'), 7, response_json)
        self.assertEqual(obj.get('length_type'), "DAYS", response_json)
        self.assertDictEqual(obj.get('employer'),
                             {'id': 1, 'picture': '', 'rating': '0.0', 'title': 'Fetes and Events', 'total_ratings': 0},
                             response_json)
        self.assertEqual(obj.get('status'), "OPEN", response_json)
        self.assertIsNotNone(obj.get('starting_at'), response_json)
        self.assertIsNotNone(obj.get('ending_at'), response_json)
        self.assertIsInstance(obj.get('payments'), list, response_json)
        self.assertEqual(len(obj.get('payments')), 2, response_json)

    def test_get_periods(self):
        url = reverse_lazy('api:admin-get-periods')
        self.client.force_login(self.test_user_employee)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 2, response_json)
        for period in response_json:
            self.assertEqual(period.get('length'), 7, response_json)
            self.assertEqual(period.get('length_type'), 'DAYS', response_json)
            self.assertIn(period.get('id'), [1, 2], response_json)
            self.assertDictEqual(period.get('employer'),
                                 {'id': 1, 'title': 'Fetes and Events', 'picture': '',
                                  'rating': '0.0', 'total_ratings': 0},
                                 response_json)
            self.assertEqual(period.get('status'), "OPEN", response_json)
            self.assertIsNotNone(period.get('starting_at'), response_json)
            self.assertIsNotNone(period.get('ending_at'), response_json)

    def test_get_one_period(self):
        url = reverse_lazy('api:admin-get-periods', kwargs={'period_id': 1})
        self.client.force_login(self.test_user_employee)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('id'), 1, response_json)
        self.assertEqual(response_json.get('length'), 7, response_json)
        self.assertEqual(response_json.get('length_type'), 'DAYS', response_json)
        self.assertDictEqual(response_json.get('employer'),
                             {'id': 1, 'picture': '', 'rating': '0.0',
                              'title': 'Fetes and Events', 'total_ratings': 0},
                             response_json
                             )
        self.assertEqual(len(response_json.get('payments')), 1, response_json)

    def test_get_my_periods(self):
        url = reverse_lazy('api:me-get-payroll-period')
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 2, response_json)
        for period in response_json:
            self.assertIn(period.get('id'), [1, 2], response_json)
            self.assertEqual(period.get('status'), "OPEN", response_json)
            self.assertIsNotNone(period.get('starting_at'), response_json)
            self.assertIsNotNone(period.get('ending_at'), response_json)
            self.assertGreaterEqual(period.get('total_payments'), 1, response_json)

    def test_get_my_periods2(self):
        """Test for employer without registered periods"""
        url = reverse_lazy('api:me-get-payroll-period')
        self.client.force_login(self.test_user_employer2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 0, response_json)

    def test_get_my_period(self):
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': 1})
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('id'), 1, response_json)
        self.assertDictEqual(response_json.get('employer'),
                             {'id': 1, 'picture': '', 'rating': '0.0',
                              'title': 'Fetes and Events', 'total_ratings': 0},
                             response_json)
        self.assertEqual(response_json.get('status'), "OPEN", response_json)
        self.assertIsNotNone(response_json.get('starting_at'), response_json)
        self.assertIsNotNone(response_json.get('ending_at'), response_json)
        self.assertGreaterEqual(len(response_json.get('payments')), 1, response_json)

    def test_get_another_employer_period(self):
        """Try to get a PayrollPeriod belong to another employer"""
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': 1})
        self.client.force_login(self.test_user_employer2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404, response.content.decode())

    def test_finalize_period(self):
        employee_payments = EmployeePayment.objects.filter(employer=self.test_user_employer.profile.employer).count()
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': 2})
        self.client.force_login(self.test_user_employer)
        response = self.client.put(url, data={'status': 'FINALIZED'}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('id'), 2, response_json)
        self.assertEqual(response_json.get('employer'), 1, response_json)
        self.assertEqual(response_json.get('status'), 'FINALIZED', response_json)
        self.assertEqual(EmployeePayment.objects.filter(employer=self.test_user_employer.profile.employer).count(),
                         employee_payments + 1)

    def test_fail_finalizing_period(self):
        """Try to finalize a PayrollPeriod which contains a PayrollPayment with PENDING status"""
        employee_payments = EmployeePayment.objects.filter(employer=self.test_user_employer.profile.employer).count()
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': 1})
        self.client.force_login(self.test_user_employer)
        response = self.client.put(url, data={'status': 'FINALIZED'}, content_type='application/json')
        self.assertContains(response, 'There is a Payroll Payment with status PENDING in current period',
                            status_code=400)
        self.assertEqual(EmployeePayment.objects.filter(employer=self.test_user_employer.profile.employer).count(),
                         employee_payments)
