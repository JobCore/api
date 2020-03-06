from django.conf import settings
from django.urls import reverse_lazy
from django.test import TestCase, override_settings
from django.utils import timezone

from dotenv import parse_dotenv, read_dotenv
from mixer.backend.django import mixer
from mock import patch
import os
import plaid

from api.models import BankAccount
from api.tests.mixins import WithMakeUser


class StripeCustomer:
    id = 'cus_GjFH3uK2Pmv7sh'
    name = 'Employer'


class StripeAccount:
    id = 'acct_1GBkMQTyupAYJrfV'
    name = 'Employee'


class StripeBankAccount:
    id = 'ba_1GBkMEIyttAYJpgKJgcpBpa7'
    bank_name = 'STRIPE TEST BANK'


@override_settings(STATICFILES_STORAGE=None)
class BankAccountTestSuite(TestCase, WithMakeUser):
    """
    Endpoint test Plaid
    """

    def setUp(self):
        read_dotenv()
        self.test_user_employee, self.test_employee, self.test_profile_employee = self._make_user(
            'employee',
            userkwargs={'username': 'employee1', 'email': 'employee1@testdoma.in', 'is_active': True},
            profilekwargs={'birth_date': '1990-11-23', 'last_4dig_ssn': '1234'},
        )
        self.test_user_employee2, self.test_employee2, self.test_profile_employee2 = self._make_user(
            'employee',
            userkwargs={'username': 'employee2', 'email': 'employee2@testdoma.in', 'is_active': True},
        )
        self.test_user_employer, self.test_employer, self.test_profile_employer = self._make_user(
            'employer',
            userkwargs={'username': 'employer1', 'email': 'employer@testdoma.in', 'is_active': True},
            employexkwargs={'rating': 0, 'created_at': timezone.now()}
        )
        self.test_user_employer_otro, self.test_employer_otro, self.test_profile_employer_otro = self._make_user(
            'employer',
            userkwargs={'username': 'employer_otro', 'email': 'employer_otro@testdoma.in', 'is_active': True},
            employexkwargs={'rating': 0, 'created_at': timezone.now()}
        )

    @patch('plaid.api.item.PublicToken.exchange', return_value={'access_token': '1234'})
    @patch('plaid.api.auth.Auth.get',
           return_value={
               "accounts": [{"name": "Test Bank Account", "account_id": "123123123"}],
               "numbers": {
                   "ach": [
                       {"account": "123412341234", "account_id": "123123123", "routing": "12341234123",
                        "wire_routing": "21341234213"}
                   ]}})
    @patch('plaid.api.Processor.stripeBankAccountTokenCreate', return_value={'stripe_bank_account_token': '1234'})
    @patch('stripe.Account.create', return_value=StripeAccount())
    @patch('stripe.Account.create_external_account', return_value=StripeBankAccount())
    def test_register_account_employee(self, mocked_plaid_item, mocked_plaid_auth, mocked_stripe_response,
                                       mocked_stripe_account, mocked_stripe_bank_account):
        self.client.force_login(self.test_user_employee)
        data = {
            "public_token": "public-development-397dd0e2-e48d-41c3-b022-9f392cf44bc6",
        }
        url = reverse_lazy('api:api-bank-accounts')
        response = self.client.post(url, data, content_type="application/json")
        accounts_len = BankAccount.objects.all().count()
        self.assertEqual(accounts_len > 0, True, response.content)

    @patch('plaid.api.item.PublicToken.exchange', return_value={'access_token': ''})
    def test_register_account_employee_missing_birth_date(self, mocked_plaid_item):
        self.client.force_login(self.test_user_employee2)
        data = {
            "public_token": "public-development-397dd0e2-e48d-41c3-b022-9f392cf44bc6",
        }
        url = reverse_lazy('api:api-bank-accounts')
        response = self.client.post(url, data, content_type="application/json")
        self.assertContains(response, 'Birth date', status_code=400)

    @patch('plaid.api.item.PublicToken.exchange', return_value={'access_token': ''})
    def test_register_account_employee_missing_last_4dig_ssn(self, mocked_plaid_item):
        self.test_profile_employee2.birth_date = '1990-05-14'
        self.test_profile_employee2.last_4dig_ssn = ''
        self.test_profile_employee2.save()
        self.client.force_login(self.test_user_employee2)
        data = {
            "public_token": "public-development-397dd0e2-e48d-41c3-b022-9f392cf44bc6",
        }
        url = reverse_lazy('api:api-bank-accounts')
        response = self.client.post(url, data, content_type="application/json")
        self.assertContains(response, 'Last 4 digits ssn', status_code=400)

    @patch('plaid.api.item.PublicToken.exchange', return_value={'access_token': '1234'})
    @patch('plaid.api.auth.Auth.get',
           return_value={
               "accounts": [{"name": "Test Bank Account", "account_id": "123123123"}],
               "numbers": {
                   "ach": [
                       {"account": "123412341234", "account_id": "123123123", "routing": "12341234123",
                        "wire_routing": "21341234213"}
                   ]}})
    @patch('plaid.api.Processor.stripeBankAccountTokenCreate', return_value={'stripe_bank_account_token': '1234'})
    @patch('stripe.customer.Customer.create', return_value=StripeCustomer())
    @patch('stripe.Customer.create_source', return_value=StripeBankAccount())
    def test_register_account_employer(self, mocked_plaid_item, mocked_plaid_auth, mocked_stripe_response,
                                       mocked_stripe_customer, mocked_stripe_bank_account):
        self.client.force_login(self.test_user_employer)
        data = {
            "public_token": "public-development-397dd0e2-e48d-41c3-b022-9f392cf44bc6",
        }
        url = reverse_lazy('api:api-bank-accounts')
        response = self.client.post(url, data, content_type="application/json")
        accounts_len = BankAccount.objects.all().count()
        self.assertEqual(accounts_len > 0, True, response.content)

    def test_list_bank_accounts(self):
        BankAccount.objects.create(**{
            "user_id": self.test_profile_employer.id,
            "name": 'Bank of America Checking',
            "account_id": 'ACCOUNT_IDC',
            "account": '12345123451',
            "routing": '123451234561',
            "wire_routing": '123451234567',
        })
        BankAccount.objects.create(**{
            "user_id": self.test_profile_employer.id,
            "name": 'Bank of America Savings',
            "account_id": 'ACCOUNT_IDS',
            "account": '12345123452',
            "routing": '123451234562',
            "wire_routing": '123451234567',
        })

        # create bank account for same employer with another profile
        self.test_profile_employer_otro.employer = self.test_employer
        self.test_profile_employer_otro.save()
        BankAccount.objects.create(**{
            "user_id": self.test_profile_employer_otro.id,
            "name": 'Bank of America Other',
            "account_id": 'ACCOUNT_IDS',
            "account": '12345123453',
            "routing": '123451234563',
            "wire_routing": '123451234567',
        })

        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:api-bank-accounts')
        response = self.client.get(url, content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content.decode())
        json_response = response.json()
        self.assertEqual(len(json_response), 3, json_response)
        for bank_account in json_response:
            self.assertIn(bank_account.get("name"),
                          ["Bank of America Checking", "Bank of America Savings", "Bank of America Other"],
                          bank_account)

    def test_delete_bank_accounts(self):
        account = BankAccount.objects.create(**{
            "user_id": self.test_profile_employer.id,
            "name": 'Bank of America Checking',
            "account_id": 'ACCOUNT_IDC',
            "account": '1234512345',
            "routing": '12345123456',
            "wire_routing": '123451234567',
        })
        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:detail-api-bank-accounts', kwargs={
            'bank_account_id': account.id
        })
        response = self.client.delete(url, content_type="application/json")
        self.assertEqual(response.status_code, 202, response.status_code)
        accounts_len = BankAccount.objects.all().count()
        self.assertEqual(accounts_len, 0, response.content)
