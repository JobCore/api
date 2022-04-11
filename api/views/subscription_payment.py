import json 
import stripe
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie, csrf_protect
from django.http import JsonResponse, HttpResponse
from django.views import View
from rest_framework.views import APIView
from ..models import SubscriptionPlan, UserProfile, Payment
from django.utils.decorators import method_decorator
from rest_framework import permissions, status
from rest_framework.response import Response
from api.serializers import (
    employer_serializer, user_serializer, shift_serializer,
    payment_serializer, venue_serializer, favlist_serializer,
    employee_serializer, clockin_serializer, rating_serializer,
    profile_serializer, other_serializer, documents_serializer, subscription_payment_serializer
)
import logging

logger = logging.getLogger('jobcore:general')
# stripe.api_key = settings.STRIPE_SECRET_KEY


# class SuccessView(TemplateView):
#     template_name = "success.html"


# class CancelView(TemplateView):
#     template_name = "cancel.html"


# class ProductLandingPageView(TemplateView):
#     # template_name = "base_site.html"

#     def get_context_data(self, **kwargs):
#         product = Product.objects.get(name="Test Product")
#         context = super(ProductLandingPageView, self).get_context_data(**kwargs)
#         context.update({
#             "product": product,
#             "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY
#         })
#         return context



# class CreateCheckoutSessionView(View):
#     def post(self, request, *args, **kwargs):
#         product_id = self.kwargs["pk"]
#         product = SubscriptionPlan.objects.get(id=product_id)
#         YOUR_DOMAIN = "http://127.0.0.1:8000"
#         checkout_session = stripe.checkout.Session.create(
#             payment_method_types=['card'],
#             line_items=[
#                 {
#                     'price_data': {
#                         'currency': 'usd',
#                         'unit_amount': product.price,
#                         'product_data': {
#                             'name': product.name,
#                             # 'images': ['https://i.imgur.com/EHyR2nP.png'],
#                         },
#                     },
#                     'quantity': 1,
#                 },
#             ],
#             metadata={
#                 "product_id": product.id
#             },
#             mode='payment',
#             success_url=YOUR_DOMAIN + '/success/',
#             cancel_url=YOUR_DOMAIN + '/cancel/',
#         )
#         return JsonResponse({
#             'id': checkout_session.id
#         })


# @csrf_exempt
# def stripe_webhook(request):
#     payload = request.body
#     sig_header = request.META['HTTP_STRIPE_SIGNATURE']
#     event = None

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
#         )
#     except ValueError as e:
#         # Invalid payload
#         return HttpResponse(status=400)
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         return HttpResponse(status=400)

#     # Handle the checkout.session.completed event
#     if event['type'] == 'checkout.session.completed':
#         session = event['data']['object']

#         customer_email = session["customer_details"]["email"]
#         product_id = session["metadata"]["product_id"]

#         product = Product.objects.get(id=product_id)

#         send_mail(
#             subject="Here is your product",
#             message=f"Thanks for your purchase. Here is the product you ordered. The URL is {product.url}",
#             recipient_list=[customer_email],
#             from_email="matt@test.com"
#         )

#         # TODO - decide whether you want to send the file or the URL
    
#     elif event["type"] == "payment_intent.succeeded":
#         intent = event['data']['object']

#         stripe_customer_id = intent["customer"]
#         stripe_customer = stripe.Customer.retrieve(stripe_customer_id)

#         customer_email = stripe_customer['email']
#         product_id = intent["metadata"]["product_id"]

#         product = Product.objects.get(id=product_id)

#         send_mail(
#             subject="Here is your product",
#             message=f"Thanks for your purchase. Here is the product you ordered. The URL is {product.url}",
#             recipient_list=[customer_email],
#             from_email="matt@test.com"
#         )

#     return HttpResponse(status=200)


class StripeIntentView(APIView):
        @csrf_exempt
        # @csrf_protect
        def post(self, request, *args, **kwargs):
            user = self.request.user
            token = list(self.request.data.items())[0][1]
            userprofile = UserProfile()
            # else:
            customer = stripe.Customer.create(
                email=self.request.user,
            )
            cus = customer.sources.create(source=token)
            if cus is not None:
                logger.info('StripeIntentView:post: customer created')
                logger.debug('StripeIntentView:post: cus: %s' % cus)
            userprofile.stripe_customer_id = customer['id']
            userprofile.user = self.request.user
            userprofile.save()
            all_userprofiles = UserProfile.objects.all()
            all_userprofiles = list(map(lambda userprofile: userprofile, all_userprofiles))
            amount = int(dict(self.request.data)['amount'] * 100)
            
            try:
                # charge the customer because we cannot charge the token more than once
                charge = stripe.Charge.create(
                    amount=amount,  # cents
                    currency="usd",
                    customer=customer['id']
                )
                if charge is not None:
                    logger.info('StripeIntentView:post: charge created')
                    logger.debug('StripeIntentView:post: charge: %s' % charge)
                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = charge['amount']
                payment.save()
                all_payments = Payment.objects.all()
                all_payments = list(map(lambda payment: payment.serialize(), all_payments))
                
                return Response({"message": "Payment received", 'status': 200 })

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                logger.error('StripeIntentView:post: %s' % str(e))
                return Response({"message": f"{err.get('message')}"}, status=status.HTTP_400_BAD_REQUEST)

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                logger.error('StripeIntentView:post: %s' % str(e))
                return Response({"message": "Rate limit error"}, status=status.HTTP_400_BAD_REQUEST)

            except stripe.error.InvalidRequestError as e:
                logger.error('StripeIntentView:post: %s' % str(e))
                # Invalid parameters were supplied to Stripe's API
                return Response({"message": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                logger.error('StripeIntentView:post: %s' % str(e))
                return Response({"message": "Not authenticated"}, status=status.HTTP_400_BAD_REQUEST)

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                logger.error('StripeIntentView:post: %s' % str(e))
                return Response({"message": "Network error"}, status=status.HTTP_400_BAD_REQUEST)

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                logger.error('StripeIntentView:post: %s' % str(e))
                return Response({"message": "Something went wrong. You were not charged. Please try again."}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                # send an email to ourselves
                logger.error('StripeIntentView:post: %s' % str(e))
                return Response({"message": "A serious error occurred. We have been notifed."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Invalid data received"}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(APIView):
    permission_classes = (permissions.AllowAny, )
    
    def get(self, request, format=None):
        return { 'csrf_cookie': csrf_cookie }

