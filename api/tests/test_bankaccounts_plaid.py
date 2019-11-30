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
        self.user = mixer.blend('auth.User')
        self.user.set_password('pass1234')
        self.user.save()
        profilekwargs = {
            'user': self.user,
        }
        profile = mixer.blend('api.Profile', **profilekwargs)
        profile.save()

    def test_register_account(self):
        self.client.force_login(self.user)
        data = {
            "public_token": "public-sandbox-43918555-4610-4b6e-a312-de7e76ea5af8",
        }
        url = reverse_lazy('api:api-bank-accounts')
        response = self.client.post(url, data, content_type="application/json")
        accounts_len = BankAccount.objects.all().count()
        self.assertEqual(accounts_len > 0, True, response.content)
