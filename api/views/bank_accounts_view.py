import os

from api.models import BankAccount
from api.views.general_views import log
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

import plaid
import logging
import stripe

log = logging.getLogger('api.views.bank_accounts_view')
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


class BankAccountAPIView(APIView):
    def post(self, request):
        # verify requirement for stripe process
        if not request.user.profile.employer and not request.user.profile.employee:
            return Response({'details': "User must be an employer or employee"}, status=status.HTTP_400_BAD_REQUEST)
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
            log.error(f"LOG:Error exchanging the Token: {str(e)}")
            raise ValueError(f"Error exchanging the Token: {str(e)}")

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
                    # create account or customer in Stripe and add bank_account
                    if request.user.profile.employer:
                        # get existing stripe_customer_id or create Customer
                        last_bank_account = request.user.profile.bank_accounts.filter(stripe_customer_id__isnull=False).last()
                        if last_bank_account:
                            stripe_customer_id = last_bank_account.stripe_customer_id
                        else:
                            stripe_customer = stripe.Customer.create(email=request.user.email,
                                                                     name=request.user.profile.employer.title)
                            stripe_customer_id = stripe_customer.id
                        stripe_bank_account = stripe.Customer.create_source(stripe_customer_id, source=bank_account_token)
                        stripe_bank_account_id = stripe_bank_account.id
                        stripe_account_id = ''
                    else:
                        tos_accept_date = timezone.now()
                        individual_data = {'first_name': request.user.first_name, 'last_name': request.user.last_name}
                        if request.user.profile.birth_date:
                            individual_data['dob'] = {'year': request.user.profile.birth_date.year,
                                                      'month': request.user.profile.birth_date.month,
                                                      'day': request.user.profile.birth_date.day}
                        stripe_account = stripe.Account.create(type="custom", country="US", email=request.user.email,
                                                               requested_capabilities=["transfers"],
                                                               business_type="individual",
                                                               tos_acceptance={'date': round(tos_accept_date.timestamp()),
                                                                               'ip': '127.0.0.1'},
                                                               individual=individual_data,
                                                               business_profile={'url': 'http://127.0.0.1'})
                        stripe_account_id = stripe_account.id
                        bank_account = stripe.Account.create_external_account(stripe_account_id,
                                                                              external_account=bank_account_token)
                        stripe_bank_account_id = bank_account.id
                        stripe_customer_id = ''
                except Exception as e:
                    return Response({'details': 'Error with Stripe: ' + str(e)},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
                        stripe_customer_id=stripe_customer_id,
                        stripe_account_id=stripe_account_id,
                        stripe_bankaccount_id=stripe_bank_account_id)
                except Exception as e:
                    log.error(f"Error creating the Bank Account: {e}")
                    raise ValueError(f"Error creating the Bank Account: {e}")

        return JsonResponse({"success": "created!"}, safe=False)

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

        return Response({"detail": "OK"}, status=202)
