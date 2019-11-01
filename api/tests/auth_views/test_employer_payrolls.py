from django.test import TestCase
from django.urls import reverse_lazy
from api.models import PayrollPeriod, PayrollPeriodPayment, PaymentDeduction
from api.tests.mixins import WithMakeUser

from mixer.backend.django import mixer


class ERPayrollTestCase(TestCase, WithMakeUser,):
    """
    Endpoint test for payroll
    """

    def setUp(self):
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

    def test_add_payment_deduction(self):

        self.client.force_login(self.test_user_employer)
        url = reverse_lazy( 'api:me-payment-deduction')

        payload = {
            'name': 'Deduction Name',
            'amount': 10,
        }
        response = self.client.post(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return an error')


    def test_get_deduction(self):
        deduction = mixer.blend('api.PaymentDeduction')
        
        self.client.force_login(self.test_user_employer)

        url = reverse_lazy('api:me-get-single-payment-deduction',
                kwargs={'deduction_id': deduction.id})

        response = self.client.get(url, content_type="application/json")
        
        # Not available for employer
        self.assertEquals(
            response.status_code,
            404,
            'It should return an error')

        self.test_user_employer.profile.employer.deductions.add(deduction)

        response = self.client.get(url, content_type="application/json")
        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

    def test_list_deductions(self):
        deduction1 = mixer.blend('api.paymentdeduction')
        deduction2 = mixer.blend('api.paymentdeduction')
        deduction3 = mixer.blend('api.paymentdeduction')
        self.test_user_employer.profile.employer.deductions.add(deduction1) 
        self.test_user_employer.profile.employer.deductions.add(deduction2) 
        self.client.force_login(self.test_user_employer)

        url = reverse_lazy( 'api:me-payment-deduction')

        response = self.client.get(url, content_type="application/json")
        self.assertEquals(
            response.status_code,
            200,
            'it should return a success response')

        self.assertEquals(
            len(response.json()),
            self.test_user_employer.profile.employer.deductions.all().count(),
            'List all deductions added from employer')

    def test_update_deductions(self):
        deduction = mixer.blend('api.paymentdeduction', amount=10)
        deduction_new = mixer.blend('api.paymentdeduction', amount=15)
        self.test_user_employer.profile.employer.deductions.add(deduction) 
        self.client.force_login(self.test_user_employer)

        url = reverse_lazy('api:me-get-single-payment-deduction',
                kwargs={'deduction_id': deduction.id})


        payload = { 'amount': 20}

        response = self.client.put(url, data=payload, content_type="application/json")
        self.assertEquals(
            response.status_code,
            200,
            'it should return a success response')
        deduction.refresh_from_db()
        self.assertEquals(
                deduction.amount,
                20)

        url = reverse_lazy('api:me-get-single-payment-deduction',
                kwargs={'deduction_id': deduction_new.id})

        response = self.client.put(url, data=payload, content_type="application/json")
        self.assertEquals(
            response.status_code,
            200,
            'it should return a success response')
        deduction_new.refresh_from_db()
        # The amount was updated
        self.assertEquals(
                deduction_new.amount,
                20)

        # Addedto employeee
        self.assertTrue(
                self.test_user_employer.profile.employer.deductions.filter(
                    id=deduction_new.id).exists())
