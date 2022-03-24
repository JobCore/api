from rest_framework import serializers
from api.models import UserProfile, Payment

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'user', 
            'stripe_customer_id',
            'stripe_sub_id'
        )

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            'id',
            'amount',
            'timestamp'
        )
