import pytz
from datetime import datetime, timedelta
from decimal import Decimal
from mixer.backend.django import mixer

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils import timezone

from api.tests.mixins import WithMakePayrollPeriod, WithMakePayrollPeriodPayment, WithMakeUser

User = get_user_model()
EmployeePayment = apps.get_model('api', 'EmployeePayment')
PayrollPeriod = apps.get_model('api', 'PayrollPeriod')
PayrollPeriodPayment = apps.get_model('api', 'PayrollPeriodPayment')


class PayrollPeriodTestSuite(TestCase, WithMakeUser, WithMakePayrollPeriod, WithMakePayrollPeriodPayment):

    def setUp(self):
        self.test_user_employee, self.test_employee, self.test_profile_employee = self._make_user(
            'employee',
            userkwargs={"username": "employee1", "email": "employee1@testdoma.in", "is_active": True},
            employexkwargs={"ratings": 0, "total_ratings": 0}
        )
        self.test_user_employee2, self.test_employee2, self.test_profile_employee2 = self._make_user(
            'employee',
            userkwargs={"username": "employee2", "email": "employee2@testdoma.in", "is_active": True},
            employexkwargs={"ratings": 0, "total_ratings": 0}
        )
        self.test_user_employer, self.test_employer, self.test_profile_employer = self._make_user(
            'employer',
            userkwargs={"username": 'employer1', "email": 'employer@testdoma.in', "is_active": True},
            employexkwargs={"maximum_clockin_delta_minutes": 15, "maximum_clockout_delay_minutes": 15,
                            "rating": 0, "total_ratings": 0}
        )
        self.test_user_employer2, self.test_employer2, self.test_profile_employer2 = self._make_user(
            'employer',
            userkwargs={"username": 'employer2', "email": 'employer2@testdoma.in', "is_active": True},
            employexkwargs={"maximum_clockin_delta_minutes": 15, "maximum_clockout_delay_minutes": 15,
                            "rating": 0, "total_ratings": 0}
        )

        begin_date = timezone.now() - timedelta(days=21)
        begin_date = datetime(begin_date.year, begin_date.month, begin_date.day, 0, 0, 0,
                              tzinfo=pytz.timezone(settings.TIME_ZONE))
        self.test_period = self._make_period(self.test_employer, begin_date)
        self.test_employer.payroll_period_starting_time = begin_date
        self.test_employer.save()
        _, shift, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee,
                                                  period=self.test_period,
                                                  mykwargs={"status": "APPROVED", "regular_hours": 10, "over_time": 8,
                                                            "breaktime_minutes": 15, "hourly_rate": 20, "total_amount": 360})
        _, _, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee,
                                              period=self.test_period,
                                              mykwargs={"status": "APPROVED", "regular_hours": 25, "over_time": 5,
                                                        "breaktime_minutes": 15, "hourly_rate": 15, "total_amount": 450},
                                              relatedkwargs={'shift': shift})
        _, _, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee2,
                                              period=self.test_period,
                                              mykwargs={"status": "APPROVED", "regular_hours": 12, "over_time": 3,
                                                        "breaktime_minutes": 0, "hourly_rate": 20, "total_amount": 300})

        begin_date = begin_date + timedelta(days=7)
        self.test_period2 = self._make_period(self.test_employer, begin_date)
        _, _, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee,
                                              period=self.test_period2, mykwargs={"status": "APPROVED"},
                                              relatedkwargs={'shift': shift})

        begin_date2 = begin_date - timedelta(days=35)
        self.test_period3 = self._make_period(self.test_employer, begin_date2)
        _, _, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee2,
                                              period=self.test_period3, mykwargs={"status": "PENDING"},
                                              relatedkwargs={'shift': shift})

        # update date and time from clockin registries, for usage in PayrollPeriod creation
        clockin_date = begin_date + timedelta(days=9)
        mixer.blend('api.Clockin',
                    started_at=clockin_date.strftime('%Y-%m-%dT20:20:00Z'),
                    ended_at=clockin_date.strftime('%Y-%m-%dT23:45:00Z'),
                    shift=shift,
                    status="APPROVED")
        clockin_date = clockin_date + timedelta(days=1)
        mixer.blend('api.Clockin',
                    started_at=clockin_date.strftime('%Y-%m-%dT20:20:00Z'),
                    ended_at=clockin_date.strftime('%Y-%m-%dT23:45:00Z'),
                    shift=shift,
                    status="APPROVED")
        self.qty = PayrollPeriod.objects.count()
        self.payroll_payment_qty = PayrollPeriodPayment.objects.count()

    def test_period_generation(self):
        """Test creation of a payroll period, with creation of related PayrollPeriodPayment registries"""
        url = reverse_lazy('api:hook-generate_periods')
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        self.assertEqual(PayrollPeriod.objects.count(), self.qty + 1)
        print(PayrollPeriod.objects.count())
        self.assertEqual(PayrollPeriodPayment.objects.count(), self.payroll_payment_qty + 2)
        response_json = response.json()
        self.assertEqual(len(response_json), 1)
        obj = response_json[0]
        self.assertIsInstance(obj.get('id'), int, response_json)
        self.assertEqual(obj.get('length'), 7, response_json)
        self.assertEqual(obj.get('length_type'), "DAYS", response_json)
        self.assertIsInstance(obj.get('employer'), dict, response_json)
        self.assertEqual(obj.get('employer').get('title'), self.test_employer.title, response_json)
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
        self.assertEqual(len(response_json), 3, response_json)
        for period in response_json:
            self.assertEqual(period.get('length'), 7, period)
            self.assertEqual(period.get('length_type'), 'DAYS', period)
            self.assertIsInstance(period.get('employer'), dict, period)
            self.assertIn(period.get('employer').get('id'), [self.test_employer.id, self.test_employer2.id], period)
            self.assertEqual(period.get('status'), "OPEN", period)
            self.assertIsNotNone(period.get('starting_at'), period)
            self.assertIsNotNone(period.get('ending_at'), period)

    def test_get_one_period(self):
        """Test get data about a period, login with employee credentials"""
        url = reverse_lazy('api:admin-get-periods', kwargs={'period_id': self.test_period.id})
        self.client.force_login(self.test_user_employee)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('id'), self.test_period.id, response_json)
        self.assertEqual(response_json.get('length'), self.test_period.length, response_json)
        self.assertEqual(response_json.get('length_type'), self.test_period.length_type, response_json)
        self.assertIsInstance(response_json.get('employer'), dict, response_json)
        self.assertEqual(response_json.get('employer').get('id'), self.test_employer.id, response_json)
        self.assertEqual(response_json.get('employer').get('title'), self.test_employer.title, response_json)
        self.assertEqual(response_json.get('employer').get('picture'), self.test_employer.picture, response_json)
        self.assertIsInstance(response_json.get('payments'), list, response_json)
        self.assertEqual(len(response_json.get('payments')), 3, response_json)

    def test_get_my_periods(self):
        url = reverse_lazy('api:me-get-payroll-period')
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 3, response_json)
        for period in response_json:
            self.assertIn(period.get('id'), [self.test_period.id, self.test_period2.id, self.test_period3.id], period)
            self.assertEqual(period.get('status'), "OPEN", period)
            self.assertIsNotNone(period.get('starting_at'), period)
            self.assertIsNotNone(period.get('ending_at'), period)

    def test_get_my_periods2(self):
        """Test for employer without registered periods"""
        url = reverse_lazy('api:me-get-payroll-period')
        self.client.force_login(self.test_user_employer2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 0, response_json)

    def test_get_my_period(self):
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': self.test_period.id})
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('id'), self.test_period.id, response_json)
        self.assertIsInstance(response_json.get('employer'), dict, response_json)
        self.assertEqual(response_json.get('employer').get('id'), self.test_employer.id, response_json)
        self.assertEqual(response_json.get('employer').get('picture'), self.test_employer.picture, response_json)
        self.assertEqual(response_json.get('employer').get('title'), self.test_employer.title, response_json)
        self.assertEqual(response_json.get('status'), "OPEN", response_json)
        self.assertIsNotNone(response_json.get('starting_at'), response_json)
        self.assertIsNotNone(response_json.get('ending_at'), response_json)
        self.assertIsInstance(response_json.get('payments'), list, response_json)
        self.assertEqual(len(response_json.get('payments')), 3, response_json)

    def test_get_another_employer_period(self):
        """Try to get a PayrollPeriod belong to another employer"""
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': self.test_period.id})
        self.client.force_login(self.test_user_employer2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404, response.content.decode())

    def test_finalize_period(self):
        """Test finalize period, verifying amounts"""
        employee_payments_qty = EmployeePayment.objects.filter(employer=self.test_employer).count()
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': self.test_period.id})
        self.client.force_login(self.test_user_employer)
        response = self.client.put(url, data={'status': 'FINALIZED'}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('id'), self.test_period.id, response_json)
        self.assertEqual(response_json.get('employer'), self.test_employer.id, response_json)
        self.assertEqual(response_json.get('status'), 'FINALIZED', response_json)
        self.assertEqual(EmployeePayment.objects.filter(employer=self.test_employer).count(), employee_payments_qty + 2)
        # verify amounts, with no over_time
        employee_payment = EmployeePayment.objects.get(employer_id=self.test_employer.id,
                                                       employee_id=self.test_employee2.id,
                                                       payroll_period_id=self.test_period.id)
        self.assertEqual(employee_payment.earnings, Decimal('300.00'), employee_payment.earnings)

    def test_finalize_period_overtime(self):
        """Test finalize period, verifying amounts with data that generate over_time"""
        employee_payments_qty = EmployeePayment.objects.filter(employer=self.test_employer).count()
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': self.test_period.id})
        self.client.force_login(self.test_user_employer)
        response = self.client.put(url, data={'status': 'FINALIZED'}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('id'), self.test_period.id, response_json)
        self.assertEqual(response_json.get('employer'), self.test_employer.id, response_json)
        self.assertEqual(response_json.get('status'), 'FINALIZED', response_json)
        self.assertEqual(EmployeePayment.objects.filter(employer=self.test_employer).count(), employee_payments_qty + 2)
        # verify amounts, with over_time
        employee_payment = EmployeePayment.objects.get(employer_id=self.test_employer.id,
                                                       employee_id=self.test_employee.id,
                                                       payroll_period_id=self.test_period.id)
        self.assertEqual(employee_payment.earnings, Decimal('360.00') + Decimal('450.00'),
                         employee_payment.earnings)

    def test_update_status_period(self):
        """Test trying to update status to same value (that period already has)"""
        prev_status = self.test_period.status
        self.test_period.status = 'FINALIZED'
        self.test_period.save()
        employee_payments = EmployeePayment.objects.filter(employer=self.test_user_employer.profile.employer).count()
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': self.test_period.id})
        self.client.force_login(self.test_user_employer)
        response = self.client.put(url, data={'status': 'FINALIZED'}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('id'), self.test_period.id, response_json)
        self.assertEqual(response_json.get('status'), 'FINALIZED', response_json)
        self.assertEqual(EmployeePayment.objects.filter(employer=self.test_user_employer.profile.employer).count(),
                         employee_payments)
        self.test_period.status = prev_status
        self.test_period.save()

    def test_fail_finalizing_period(self):
        """Try to finalize a PayrollPeriod which contains a PayrollPayment with PENDING status"""
        employee_payments = EmployeePayment.objects.filter(employer=self.test_user_employer.profile.employer).count()
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': self.test_period3.id})
        self.client.force_login(self.test_user_employer)
        response = self.client.put(url, data={'status': 'FINALIZED'}, content_type='application/json')
        self.assertContains(response, 'There is a Payroll Payment with status PENDING in current period',
                            status_code=400)
        self.assertEqual(EmployeePayment.objects.filter(employer=self.test_user_employer.profile.employer).count(),
                         employee_payments)

    # def test_fail_finalizing_period2(self):
    #     """Try to finalize a PayrollPeriod which has PAID status"""
    #     # get the period here and set as PAID
    #     period = PayrollPeriod.objects.get(id=self.test_period.id)
    #     prev_status = period.status
    #     period.status = 'PAID'
    #     period.save()
    #     url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': period.id})
    #     self.client.force_login(self.test_user_employer)
    #     response = self.client.put(url, data={'status': 'FINALIZED'}, content_type='application/json')
    #     period.status = prev_status
    #     period.save()
    #     self.assertContains(response, 'This period has a payment done and can not be changed',
    #                         status_code=400)

    def test_finalize_and_open_period(self):
        """Test that a period can be change from OPEN to FINALIZED status and vice versa"""
        employee_payments_qty = EmployeePayment.objects.filter(employer=self.test_employer).count()
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={'period_id': self.test_period2.id})
        self.client.force_login(self.test_user_employer)
        # change from OPEN to FINALIZE
        response = self.client.put(url, data={'status': 'FINALIZED'}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('status'), 'FINALIZED', response_json)
        self.assertEqual(EmployeePayment.objects.filter(employer=self.test_employer).count(), employee_payments_qty + 1)
        # change from FINALIZE to OPEN
        response = self.client.put(url, data={'status': 'OPEN'}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('status'), 'OPEN', response_json)
        self.assertEqual(EmployeePayment.objects.filter(employer=self.test_employer).count(), employee_payments_qty)
