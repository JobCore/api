from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from django.apps import apps
from io import BytesIO
from django.test.client import MULTIPART_CONTENT
import random
from mock import patch
import stripe
import os


stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
EmployeeDocument = apps.get_model('api', 'EmployeeDocument')
Document = apps.get_model('api', 'Document')
@override_settings(STATICFILES_STORAGE=None)
class SubscriptionPaymentTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """ 
    Endpoint tests for subscription charge via stripe
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
                username='employer1@testdoma.in',
                email='employer1@testdoma.in',
                is_active=True,
            ),
        )
    

    # def test_stripe_single_charge(self):
    #     token = stripe.Token.create(
    #             card={
    #                 "number": "4242424242424242",
    #                 "exp_month": 4,
    #                 "exp_year": 2028,
    #                 "cvc": "314",
    #             },
    #         )
    #     customer = stripe.Customer.create(
    #             email='employer1@testdoma.in',
    #         )
    #     data= {
    #         'token': token.id,
    #         'amount': 1,
    #         }
    #     url = reverse_lazy('api:create-payment-intent')
    #     self.client.force_login(self.test_user_employer)
    #     response = self.client.post(url, data=data, content_type="application/json")
    #     self.assertEqual(response.status_code, 200, response.content.decode())
    #     response_json = response.json()
    
    # def test_customer_stripe_id(self):
    #     self.customer = stripe.Customer.create(
    #         email="employer1@testdoma.in",
    #         description="customer for test",
    #     )
    #     self.assertIsNotNone(self.customer.id)

    # def test_creating_a_new_customer(self):
    #     customer = stripe.Customer.create(
    #         email="employer1@testdoma.in",
    #         description="customer for test",
    #     )
    
               