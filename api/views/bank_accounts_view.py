import os

from api.models import BankAccount
from api.views.general_views import log
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from django.db import transaction

import plaid
import logging

log = logging.getLogger('api.views.bank_accounts_view')


class BankAccountAPIView(APIView):
    def post(self, request):
        plaid_client = plaid.Client(
            client_id=os.environ.get('PLAID_CLIENT_ID'),
            secret=os.environ.get('PLAID_SECRET'),
            public_key=os.environ.get('PLAID_PUBLIC_KEY'),
            environment=os.environ.get('PLAID_ENV'))

        plaid_link_public_token = request.data.get('public_token', None)
        institution_name = request.data.get('institution_name', "")

        if plaid_link_public_token is None:
            raise ValueError(f"'public_token' is required: {str(request.data)}")

        try:
            plaid_request = plaid_client.Item.public_token.exchange(plaid_link_public_token)
        except Exception as e:
            log.error(f"Error exchanging the Token: {e}")
            raise ValueError(f"Error exchanging the Token: {e}")

        access_token = plaid_request['access_token']
        response = plaid_client.Auth.get(access_token)
        accounts_data = {}
        for account in response.get("accounts"):
            accounts_data[account.get("account_id")] = account.get("name")
        ach = response.get('numbers', {}).get("ach", None)

        with transaction.atomic():
            for acc in ach:
                account_id = acc.get("account_id")
                account = acc.get("account", "")
                routing = acc.get("routing", "")
                wire_routing = acc.get("wire_routing", "")

                try:
                    stripe_response = plaid_client.Processor.stripeBankAccountTokenCreate(access_token, account_id)
                    bank_account_token = stripe_response['stripe_bank_account_token']
                except Exception as e:
                    log.error(f"Error creating the Stripe Token: {e}")
                    raise ValueError(f"Error creating the Stripe Tokens: {e}")

                try:
                    BankAccount.objects.create(
                        user=request.user.profile,
                        access_token=access_token,
                        name=accounts_data[account_id],
                        account_id=account_id,
                        account=account,
                        routing=routing,
                        institution_name=institution_name,
                        wire_routing=wire_routing,
                        stripe_token=bank_account_token)
                except Exception as e:
                    log.error(f"Error creating the Bank Account: {e}")
                    raise ValueError(f"Error creating the Bank Account: {e}")

        return Response(status=status.HTTP_201_CREATED)

    def get(self, request):
        accounts = BankAccount.objects.filter(user_id=request.user.profile.id).order_by('id')
        json_accounts = []
        for acc in accounts:
            acc_obj = {
                "name": acc.name,
                "institution_name": acc.institution_name,
                "id": acc.id,
            }
            json_accounts.append(acc_obj)

        return Response(json_accounts, status=status.HTTP_200_OK)


class BankAccountDetailAPIView(APIView):
    def delete(self, request, bank_account_id):
        query_set = BankAccount.objects.filter(user_id=request.user.profile.id, id=bank_account_id)
        account = query_set.first()
        if account is None:
            return Response(status=404)

        plaid_client = plaid.Client(
            client_id=os.environ.get('PLAID_CLIENT_ID'),
            secret=os.environ.get('PLAID_SECRET'),
            public_key=os.environ.get('PLAID_PUBLIC_KEY'),
            environment=os.environ.get('PLAID_ENV'))

        try:
            plaid_client.Item.remove(account.access_token)
        except Exception as e:
            log.info("Access token unsuable")

        try:
            query_set.delete()
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

        return Response(status=202)
