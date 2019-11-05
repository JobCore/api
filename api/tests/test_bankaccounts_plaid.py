from django.conf import settings
from django.urls import reverse_lazy
from django.test import TestCase, override_settings

from dotenv import parse_dotenv, read_dotenv
from mixer.backend.django import mixer
from mock import patch
import os 
import plaid

from api.models import BankAccount

class BankAccountTestSuite(TestCase):
    """
    Endpoint test Plaid
    """

    def setUp(self):
        read_dotenv()
        self.plaidclient = plaid.Client(
                client_id=os.environ.get('PLAID_CLIENT_ID'),
                secret=os.environ.get('PLAID_SECRET'),
                public_key=os.environ.get('PLAID_PUBLIC_KEY'),
                environment='sandbox')
        self.public_token = self.plaidclient.Sandbox.public_token.create('ins_109508', ['transactions'])['public_token']
        self.user = mixer.blend('auth.User')
        self.user.set_password('pass1234')
        self.user.save()
        profilekwargs={
            'user': self.user,
        }

        profile = mixer.blend('api.Profile', **profilekwargs)
        profile.save()

    @patch('plaid.api.item.PublicToken.exchange', return_value={'access_token': '1234'})
    @patch('plaid.api.auth.Auth.get',
        return_value={
            "accounts": [
                {"name": "Test Bank Account"}],
            "item":{
                "institution_id": "4321",
                "item_id": "7777"}})
    def test_register_account(self, mocked_request, mocked_auth_request):
        self.client.force_login(self.user)
        url = reverse_lazy('api:register-bank-account')
        response = self.client.post(url, data={'public_token': self.public_token})
        assert(self.user.profile.bank_accounts.exists())

