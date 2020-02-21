import pytz

from datetime import datetime, timedelta
from decimal import Decimal
from mixer.backend.django import mixer

from django.apps import apps
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse_lazy
from django.utils import timezone

from api.tests.mixins import WithMakePayrollPeriod, WithMakePayrollPeriodPayment, WithMakeUser

EmployeePayment = apps.get_model('api', 'EmployeePayment')
PaymentTransaction = apps.get_model('api', 'PaymentTransaction')
PayrollPeriod = apps.get_model('api', 'PayrollPeriod')


@override_settings(STATICFILES_STORAGE=None)
class EmployeePaymentTestSuite(TestCase, WithMakeUser, WithMakePayrollPeriod, WithMakePayrollPeriodPayment):

    def setUp(self):
        self.test_user_employee, self.test_employee, self.test_profile_employee = self._make_user(
            'employee',
            userkwargs={"username": "employee1", "email": "employee1@testdoma.in", "is_active": True},
            employexkwargs={"ratings": 0, "total_ratings": 0}
        )
        self.test_acc_employee = mixer.blend('api.BankAccount', user=self.test_profile_employee)

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
        self.test_acc1_employer = mixer.blend('api.BankAccount', user=self.test_profile_employer)
        self.test_acc2_employer = mixer.blend('api.BankAccount', user=self.test_profile_employer)

        begin_date = timezone.now() - timedelta(days=49)
        begin_date = datetime(begin_date.year, begin_date.month, begin_date.day, 0, 0, 0,
                              tzinfo=pytz.timezone(settings.TIME_ZONE))
        self.test_period = self._make_period(self.test_employer, begin_date)
        _, shift, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee,
                                                  period=self.test_period, mykwargs={"status": "APPROVED"})
        _, _, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee,
                                              period=self.test_period, mykwargs={"status": "APPROVED"},
                                              relatedkwargs={'shift': shift})
        _, _, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee2,
                                              period=self.test_period, mykwargs={"status": "APPROVED"})

        begin_date = begin_date + timedelta(days=7)
        self.test_period2 = self._make_period(self.test_employer, begin_date)
        _, _, _, _ = self._make_periodpayment(employer=self.test_employer, employee=self.test_employee,
                                              period=self.test_period2, mykwargs={"status": "APPROVED"},
                                              relatedkwargs={'shift': shift})

        # for employee payment report and deductions report
        begin_date = begin_date + timedelta(days=7)
        self.test_period3 = self._make_period(self.test_employer, begin_date)
        py_transac = mixer.blend('api.PaymentTransaction',
                                 payment_type=PaymentTransaction.ELECT_TRANSF,
                                 sender_user_id=self.test_user_employer.id,
                                 receiver_user_id=self.test_user_employee.id,
                                 payment_data={'service_name': 'Stripe',
                                               'sender_stripe_token': self.test_acc1_employer.stripe_bankaccount_id,
                                               'receiver_stripe_token': self.test_acc_employee.stripe_bankaccount_id}
                                 )
        self.emp_pay1 = mixer.blend('api.EmployeePayment', employer_id=self.test_employer.id,
                                    employee_id=self.test_employee.id, payroll_period_id=self.test_period3.id,
                                    paid=True, deduction_list=[{"name": "Social Security", "amount": "7.5000"},
                                                               {"name": "Medicare", "amount": "7.5000"}],
                                    payment_transaction_id=py_transac.id, amount=py_transac.amount)
        self.emp_pay2 = mixer.blend('api.EmployeePayment', employer_id=self.test_employer.id,
                                    employee_id=self.test_employee2.id, payroll_period_id=self.test_period3.id,
                                    paid=False, deduction_list=[{"name": "Social Security", "amount": "7.5000"},
                                                                {"name": "Medicare", "amount": "7.5000"}],
                                    payment_transaction_id=None)

    def test_get(self):
        """Test to get a list of employee payments for selected period"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={"period_id": self.test_period.id})
        response = self.client.put(url, {"status": "FINALIZED"}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        url = reverse_lazy('api:me-get-employee-payment-list', kwargs={"period_id": self.test_period.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('payroll_period'), self.test_period.id, response_json)
        self.assertIsNotNone(response_json.get('employer'), response_json)
        self.assertEqual(response_json.get('employer').get('id'), self.test_employer.id, response_json)
        self.assertIsInstance(response_json.get('employer').get('bank_accounts'), list, response_json)
        self.assertEqual(len(response_json.get('employer').get('bank_accounts')), 2, response_json)
        for bank_account in response_json.get('employer').get('bank_accounts'):
            self.assertIn(bank_account.get('id'), [self.test_acc1_employer.id, self.test_acc2_employer.id],
                          response_json)
        self.assertIsNotNone(response_json.get('payments'), response_json)
        self.assertEqual(len(response_json.get('payments')), 2, response_json)
        # check payments data structure
        payment = response_json.get('payments')[0]
        self.assertIsInstance(payment.get('id'), int, payment)
        self.assertEqual(payment.get('payroll_period_id'), self.test_period.id, payment)
        self.assertIsNotNone(payment.get('regular_hours'), payment)
        self.assertIsNotNone(payment.get('over_time'), payment)
        self.assertIsNotNone(payment.get('amount'), payment)
        self.assertIsNotNone(payment.get('earnings'), payment)
        self.assertIsNotNone(payment.get('deductions'), payment)
        self.assertIsInstance(payment.get('deduction_list'), list, payment)
        self.assertGreaterEqual(len(payment.get('deduction_list')), 2, payment)
        self.assertIsInstance(payment.get('employee'), dict, payment)
        self.assertIsInstance(payment.get('employee').get('bank_accounts'), list, payment)
        self.assertEqual(payment.get('paid'), False, payment)

    def test_make_payment_transfer(self):
        """Test make a payment via electronic transference"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={"period_id": self.test_period.id})
        response = self.client.put(url, {"status": "FINALIZED"}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        employee_payment = EmployeePayment.objects.get(payroll_period=self.test_period,
                                                       employer=self.test_employer,
                                                       employee=self.test_employee)
        self.assertFalse(employee_payment.paid)

        payment_transactions_qty = PaymentTransaction.objects.count()
        paid_payroll_payments = self.test_employee.payrollperiodpayment_set.filter(payroll_period=self.test_period,
                                                                                   status="PAID").count()
        approved_payroll_payments = self.test_employee.payrollperiodpayment_set.filter(payroll_period=self.test_period,
                                                                                       status="APPROVED").count()

        url = reverse_lazy('api:me-get-employee-payment', kwargs={"employee_payment_id": employee_payment.id})
        response = self.client.post(url,
                                    {"payment_type": "FAKE",
                                     "payment_data": {"employer_bank_account_id": self.test_acc1_employer.id,
                                                      "employee_bank_account_id": self.test_acc_employee.id}},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        self.assertDictEqual(response.json(), {'message': 'success'}, response.content.decode())
        self.assertEqual(PayrollPeriod.objects.get(id=self.test_period.id).status, "PAID",
                         "Period should be FINALIZED because there is a pending employee payment")
        self.assertEqual(PaymentTransaction.objects.count(), payment_transactions_qty + 1,
                         "Should be exist one PaymentTransaction additional")
        employee_payment.refresh_from_db()
        self.assertTrue(employee_payment.paid)
        self.assertEqual(self.test_employee.payrollperiodpayment_set.filter(payroll_period=self.test_period,
                                                                            status="PAID").count(),
                         paid_payroll_payments + approved_payroll_payments)

    def test_make_payment_missing_payment_type(self):
        """Try to make a payment without provide payment_type info"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={"period_id": self.test_period.id})
        response = self.client.put(url, {"status": "FINALIZED"}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        employee_payment = EmployeePayment.objects.get(payroll_period=self.test_period,
                                                       employer=self.test_employer,
                                                       employee=self.test_employee)
        self.assertFalse(employee_payment.paid)

        url = reverse_lazy('api:me-get-employee-payment', kwargs={"employee_payment_id": employee_payment.id})
        response = self.client.post(url,
                                    {"payment_data": {"employer_bank_account_id": self.test_acc1_employer.id,
                                                      "employee_bank_account_id": self.test_acc_employee.id}},
                                    content_type='application/json')
        self.assertContains(response, 'payment_type', status_code=400, msg_prefix='ERROR_DATA')

    def test_make_payment_missing_payment_data(self):
        """Try to make a payment without provide payment_data info"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={"period_id": self.test_period.id})
        response = self.client.put(url, {"status": "FINALIZED"}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        employee_payment = EmployeePayment.objects.get(payroll_period=self.test_period,
                                                       employer=self.test_employer,
                                                       employee=self.test_employee)
        self.assertFalse(employee_payment.paid)

        url = reverse_lazy('api:me-get-employee-payment', kwargs={"employee_payment_id": employee_payment.id})
        response = self.client.post(url,
                                    {"payment_type": "FAKE"},
                                    content_type='application/json')
        self.assertContains(response, 'payment_data', status_code=400, msg_prefix='ERROR_DATA')

    def test_make_payment_wrong_payment_type(self):
        """Try to make a payment with a wrong payment_type value"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={"period_id": self.test_period.id})
        response = self.client.put(url, {"status": "FINALIZED"}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        employee_payment = EmployeePayment.objects.get(payroll_period=self.test_period,
                                                       employer=self.test_employer,
                                                       employee=self.test_employee)
        self.assertFalse(employee_payment.paid)

        url = reverse_lazy('api:me-get-employee-payment', kwargs={"employee_payment_id": employee_payment.id})
        response = self.client.post(url,
                                    {"payment_type": "WRONGVAL",
                                     "payment_data": {"employer_bank_account_id": self.test_acc1_employer.id,
                                                      "employee_bank_account_id": self.test_acc_employee.id}},
                                    content_type='application/json')
        self.assertContains(response, 'payment_type', status_code=400, msg_prefix='ERROR_DATA')

    def test_make_payment_wrong_payment_data(self):
        """Try to make a payment with a wrong payment_data value"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-single-payroll-period', kwargs={"period_id": self.test_period.id})
        response = self.client.put(url, {"status": "FINALIZED"}, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content.decode())
        employee_payment = EmployeePayment.objects.get(payroll_period=self.test_period,
                                                       employer=self.test_employer,
                                                       employee=self.test_employee)
        self.assertFalse(employee_payment.paid)

        url = reverse_lazy('api:me-get-employee-payment', kwargs={"employee_payment_id": employee_payment.id})
        response = self.client.post(url,
                                    {"payment_type": "FAKE",
                                     "payment_data": {"key1": 1, "key2": 2}},
                                    content_type='application/json')
        self.assertContains(response, 'payment_data', status_code=400, msg_prefix='ERROR_DATA')

    def test_employee_payment_report(self):
        """Get a list of paid employee payments, without provide search parameters"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-employee-payment-report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        self.assertIsInstance(response_json[0].get('employee'), str, response_json)
        self.assertIsNotNone(response_json[0].get('earnings'), response_json)
        self.assertIsNotNone(response_json[0].get('deductions'), response_json)
        self.assertIsNotNone(response_json[0].get('payment_date'), response_json)
        self.assertIsInstance(response_json[0].get('payment_source'), str, response_json)
        self.assertIsInstance(response_json[0].get('payroll_period'), dict, response_json)
        self.assertEqual(response_json[0].get('payroll_period', {}).get('id'), self.test_period3.id, response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('starting_at'), response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('ending_at'), response_json)
        self.assertEqual(Decimal(response_json[0].get('amount')), self.emp_pay1.amount, response_json)

    def test_employee_payment_report_start_date(self):
        """Get a list of paid employee payments, providing start_date parameter"""
        self.client.force_login(self.test_user_employer)
        start_date = timezone.now() - timedelta(days=5)
        url = reverse_lazy('api:me-get-employee-payment-report') + '?start_date=' + start_date.strftime('%Y-%m-%d')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        self.assertIsInstance(response_json[0].get('employee'), str, response_json)
        self.assertIsNotNone(response_json[0].get('earnings'), response_json)
        self.assertIsNotNone(response_json[0].get('deductions'), response_json)
        self.assertIsNotNone(response_json[0].get('payment_date'), response_json)
        self.assertIsInstance(response_json[0].get('payment_source'), str, response_json)
        self.assertIsInstance(response_json[0].get('payroll_period'), dict, response_json)
        self.assertEqual(response_json[0].get('payroll_period', {}).get('id'), self.test_period3.id, response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('starting_at'), response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('ending_at'), response_json)
        self.assertEqual(Decimal(response_json[0].get('amount')), self.emp_pay1.amount, response_json)

    def test_employee_payment_report_start_date2(self):
        """Get a list of paid employee payments, providing start_date parameter; result is empty"""
        self.client.force_login(self.test_user_employer)
        start_date = timezone.now() + timedelta(days=5)
        url = reverse_lazy('api:me-get-employee-payment-report') + '?start_date=' + start_date.strftime('%Y-%m-%d')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 0, response_json)

    def test_employee_payment_report_end_date(self):
        """Get a list of paid employee payments, providing end_date parameter"""
        self.client.force_login(self.test_user_employer)
        end_date = timezone.now()
        url = reverse_lazy('api:me-get-employee-payment-report') + '?end_date=' + end_date.strftime('%Y-%m-%d')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        self.assertIsInstance(response_json[0].get('employee'), str, response_json)
        self.assertIsNotNone(response_json[0].get('earnings'), response_json)
        self.assertIsNotNone(response_json[0].get('deductions'), response_json)
        self.assertIsNotNone(response_json[0].get('payment_date'), response_json)
        self.assertIsInstance(response_json[0].get('payment_source'), str, response_json)
        self.assertIsInstance(response_json[0].get('payroll_period'), dict, response_json)
        self.assertEqual(response_json[0].get('payroll_period', {}).get('id'), self.test_period3.id, response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('starting_at'), response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('ending_at'), response_json)
        self.assertEqual(Decimal(response_json[0].get('amount')), self.emp_pay1.amount, response_json)

    def test_employee_payment_report_end_date2(self):
        """Get a list of paid employee payments, providing end_date parameter; result is empty"""
        self.client.force_login(self.test_user_employer)
        end_date = timezone.now() - timedelta(days=5)
        url = reverse_lazy('api:me-get-employee-payment-report') + '?end_date=' + end_date.strftime('%Y-%m-%d')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 0, response_json)

    def test_employee_payment_report_period(self):
        """Get a list of paid employee payments, providing period_id parameter"""
        self.client.force_login(self.test_user_employer)
        period_id = self.test_period3.id
        url = reverse_lazy('api:me-get-employee-payment-report') + '?period_id=' + str(period_id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        self.assertIsInstance(response_json[0].get('employee'), str, response_json)
        self.assertIsNotNone(response_json[0].get('earnings'), response_json)
        self.assertIsNotNone(response_json[0].get('deductions'), response_json)
        self.assertIsNotNone(response_json[0].get('payment_date'), response_json)
        self.assertIsInstance(response_json[0].get('payment_source'), str, response_json)
        self.assertIsInstance(response_json[0].get('payroll_period'), dict, response_json)
        self.assertEqual(response_json[0].get('payroll_period', {}).get('id'), self.test_period3.id, response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('starting_at'), response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('ending_at'), response_json)
        self.assertEqual(Decimal(response_json[0].get('amount')), self.emp_pay1.amount, response_json)

    def test_employee_payment_report_period2(self):
        """Get a list of paid employee payments, providing period_id parameter; empty and error results"""
        self.client.force_login(self.test_user_employer)

        another_period = self._make_period(self.test_employer, self.test_period3.ending_at)
        url = reverse_lazy('api:me-get-employee-payment-report') + '?period_id=' + str(another_period.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 0, response_json)

        url = reverse_lazy('api:me-get-employee-payment-report') + '?period_id=555'
        response = self.client.get(url)
        self.assertContains(response, 'period_id', status_code=400)

    def test_employee_payment_report_start_date_period(self):
        """Get a list of paid employee payments, providing start_date and period_id parameters"""
        self.client.force_login(self.test_user_employer)
        start_date = timezone.now() + timedelta(days=5)
        period_id = self.test_period3.id
        url = reverse_lazy('api:me-get-employee-payment-report') \
            + '?period_id={}&start_date={}'.format(str(period_id), start_date.strftime('%Y-%m-%d'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        self.assertIsInstance(response_json[0].get('employee'), str, response_json)
        self.assertIsNotNone(response_json[0].get('earnings'), response_json)
        self.assertIsNotNone(response_json[0].get('deductions'), response_json)
        self.assertIsNotNone(response_json[0].get('payment_date'), response_json)
        self.assertIsInstance(response_json[0].get('payment_source'), str, response_json)
        self.assertIsInstance(response_json[0].get('payroll_period'), dict, response_json)
        self.assertEqual(response_json[0].get('payroll_period', {}).get('id'), self.test_period3.id, response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('starting_at'), response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('ending_at'), response_json)
        self.assertEqual(Decimal(response_json[0].get('amount')), self.emp_pay1.amount, response_json)

    def test_employee_payment_report_wrong_start_date(self):
        """Get a list of paid employee payments, providing a wrong start_date"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-employee-payment-report') + '?start_date=24-15-400'
        response = self.client.get(url)
        self.assertContains(response, 'start_date', status_code=400)

    def test_employee_payment_report_null_get_params(self):
        """Get a list of paid employee payments, providing GET parameters with null value"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-employee-payment-report') + '?period_id=null&start_date=null&end_date=null'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        self.assertIsInstance(response_json[0].get('employee'), str, response_json)
        self.assertIsNotNone(response_json[0].get('earnings'), response_json)
        self.assertIsNotNone(response_json[0].get('deductions'), response_json)
        self.assertIsNotNone(response_json[0].get('payment_date'), response_json)
        self.assertIsInstance(response_json[0].get('payment_source'), str, response_json)
        self.assertIsInstance(response_json[0].get('payroll_period'), dict, response_json)
        self.assertEqual(response_json[0].get('payroll_period', {}).get('id'), self.test_period3.id, response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('starting_at'), response_json)
        self.assertIsNotNone(response_json[0].get('payroll_period', {}).get('ending_at'), response_json)
        self.assertEqual(Decimal(response_json[0].get('amount')), self.emp_pay1.amount, response_json)

    def test_employee_payment_deduction_report(self):
        """Get list of deductions related to paid employee payments"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-employee-payment-deduction-report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        item = response_json[0]
        self.assertIsInstance(Decimal(item.get('deduction_amount')), Decimal, item)
        self.assertIsInstance(item.get('deduction_list'), list, item)
        self.assertEqual(len(item.get('deduction_list')), 2, item)
        self.assertIsInstance(item.get('deduction_list')[0].get('name'), str, item)
        self.assertIsNotNone(item.get('deduction_list')[0].get('amount'), item)
        self.assertIsInstance(item.get('employee'), str, item)
        self.assertIsNotNone(item.get('payment_date'), item)
        self.assertIsInstance(item.get('payroll_period'), dict, item)
        self.assertEqual(item.get('payroll_period', {}).get('id'), self.test_period3.id, item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('starting_at'), item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('ending_at'), item)

    def test_employee_payment_deduction_report_start_date(self):
        """Get list of deductions related to paid employee payments, providing start_date parameter"""
        self.client.force_login(self.test_user_employer)
        start_date = timezone.now() - timedelta(days=5)
        url = reverse_lazy('api:me-get-employee-payment-deduction-report') \
            + '?start_date=' + start_date.strftime('%Y-%m-%d')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        item = response_json[0]
        self.assertIsInstance(Decimal(item.get('deduction_amount')), Decimal, item)
        self.assertIsInstance(item.get('deduction_list'), list, item)
        self.assertEqual(len(item.get('deduction_list')), 2, item)
        self.assertIsInstance(item.get('deduction_list')[0].get('name'), str, item)
        self.assertIsNotNone(item.get('deduction_list')[0].get('amount'), item)
        self.assertIsInstance(item.get('employee'), str, item)
        self.assertIsNotNone(item.get('payment_date'), item)
        self.assertIsInstance(item.get('payroll_period'), dict, item)
        self.assertEqual(item.get('payroll_period', {}).get('id'), self.test_period3.id, item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('starting_at'), item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('ending_at'), item)

    def test_employee_payment_deduction_report_start_date2(self):
        """Get list of deductions related to paid employee payments, providing start_date parameter; result is empty"""
        self.client.force_login(self.test_user_employer)
        start_date = timezone.now() + timedelta(days=5)
        url = reverse_lazy('api:me-get-employee-payment-deduction-report') \
            + '?start_date=' + start_date.strftime('%Y-%m-%d')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 0, response_json)

    def test_employee_payment_deduction_report_end_date(self):
        """Get list of deductions related to paid employee payments, providing end_date parameter"""
        self.client.force_login(self.test_user_employer)
        end_date = timezone.now()
        url = reverse_lazy('api:me-get-employee-payment-deduction-report') \
            + '?end_date=' + end_date.strftime('%Y-%m-%d')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        item = response_json[0]
        self.assertIsInstance(Decimal(item.get('deduction_amount')), Decimal, item)
        self.assertIsInstance(item.get('deduction_list'), list, item)
        self.assertEqual(len(item.get('deduction_list')), 2, item)
        self.assertIsInstance(item.get('deduction_list')[0].get('name'), str, item)
        self.assertIsNotNone(item.get('deduction_list')[0].get('amount'), item)
        self.assertIsInstance(item.get('employee'), str, item)
        self.assertIsNotNone(item.get('payment_date'), item)
        self.assertIsInstance(item.get('payroll_period'), dict, item)
        self.assertEqual(item.get('payroll_period', {}).get('id'), self.test_period3.id, item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('starting_at'), item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('ending_at'), item)

    def test_employee_payment_deduction_report_period(self):
        """Get list of deductions related to paid employee payments, providing period_id parameter"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-employee-payment-deduction-report') + '?period_id=' + str(self.test_period3.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        item = response_json[0]
        self.assertIsInstance(Decimal(item.get('deduction_amount')), Decimal, item)
        self.assertIsInstance(item.get('deduction_list'), list, item)
        self.assertEqual(len(item.get('deduction_list')), 2, item)
        self.assertIsInstance(item.get('deduction_list')[0].get('name'), str, item)
        self.assertIsNotNone(item.get('deduction_list')[0].get('amount'), item)
        self.assertIsInstance(item.get('employee'), str, item)
        self.assertIsNotNone(item.get('payment_date'), item)
        self.assertIsInstance(item.get('payroll_period'), dict, item)
        self.assertEqual(item.get('payroll_period', {}).get('id'), self.test_period3.id, item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('starting_at'), item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('ending_at'), item)

    def test_employee_payment_deduction_report_period2(self):
        """Get list of deductions related to paid employee payments, providing period_id parameter; empty and error as result"""
        self.client.force_login(self.test_user_employer)

        another_period = self._make_period(self.test_employer, self.test_period3.ending_at)
        url = reverse_lazy('api:me-get-employee-payment-deduction-report') + '?period_id=' + str(another_period.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 0, response_json)

        url = reverse_lazy('api:me-get-employee-payment-deduction-report') + '?period_id=555'
        response = self.client.get(url)
        self.assertContains(response, 'period_id', status_code=400)

    def test_employee_payment_deduction_report_start_date_period(self):
        """Get list of deductions related to paid employee payments, providing start_date and period_id parameters"""
        self.client.force_login(self.test_user_employer)
        start_date = timezone.now() + timedelta(days=5)
        url = reverse_lazy('api:me-get-employee-payment-deduction-report') \
            + '?period_id={}&start_date={}'.format(self.test_period3.id, start_date.strftime('%Y-%m-%d'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        item = response_json[0]
        self.assertIsInstance(Decimal(item.get('deduction_amount')), Decimal, item)
        self.assertIsInstance(item.get('deduction_list'), list, item)
        self.assertEqual(len(item.get('deduction_list')), 2, item)
        self.assertIsInstance(item.get('deduction_list')[0].get('name'), str, item)
        self.assertIsNotNone(item.get('deduction_list')[0].get('amount'), item)
        self.assertIsInstance(item.get('employee'), str, item)
        self.assertIsNotNone(item.get('payment_date'), item)
        self.assertIsInstance(item.get('payroll_period'), dict, item)
        self.assertEqual(item.get('payroll_period', {}).get('id'), self.test_period3.id, item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('starting_at'), item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('ending_at'), item)

    def test_employee_payment_deduction_report_null_parameters(self):
        """Get list of deductions related to paid employee payments, providing GET parameters with null value"""
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-get-employee-payment-deduction-report') \
            + '?start_date=null&start-date=null&end_date=null'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(len(response_json), 1, response_json)
        item = response_json[0]
        self.assertIsInstance(Decimal(item.get('deduction_amount')), Decimal, item)
        self.assertIsInstance(item.get('deduction_list'), list, item)
        self.assertEqual(len(item.get('deduction_list')), 2, item)
        self.assertIsInstance(item.get('deduction_list')[0].get('name'), str, item)
        self.assertIsNotNone(item.get('deduction_list')[0].get('amount'), item)
        self.assertIsInstance(item.get('employee'), str, item)
        self.assertIsNotNone(item.get('payment_date'), item)
        self.assertIsInstance(item.get('payroll_period'), dict, item)
        self.assertEqual(item.get('payroll_period', {}).get('id'), self.test_period3.id, item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('starting_at'), item)
        self.assertIsNotNone(item.get('payroll_period', {}).get('ending_at'), item)
