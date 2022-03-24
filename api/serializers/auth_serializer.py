from django.contrib.auth import authenticate
import os
from django.db.models import Q
from random import randint
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
import stripe
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework import serializers

from jwt.exceptions import DecodeError
import jwt

from api.serializers import employer_serializer
from api.actions import employee_actions, auth_actions
from api.models import (
    User, Employer, Employee, Profile,
    JobCoreInvite, FCMDevice, UserProfile)
from api.utils import notifier

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER

EMPLOYER_REGISTRATION_DEACTIVATED = os.environ.get('EMPLOYER_REGISTRATION_DEACTIVATED')

class UserLoginSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(required=False)
    employer = employer_serializer.EmployerGetSerializer(required=False)
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password',
                  'token', 'employer', 'employee')
        extra_kwargs = {"password": {"write_only": True}}

class CustomJWTSerializer(JSONWebTokenSerializer):
    username_field = 'username_or_email'
    user = UserLoginSerializer(required=False)
    registration_id = serializers.CharField(write_only=True, required=False)
    exp_days = serializers.IntegerField(write_only=True, required=False)
    employer_id = serializers.IntegerField(write_only=True, required=False)

    def validate(self, attrs):
        lookup = Q(email=attrs.get("username_or_email")) \
                 | Q(username=attrs.get("username_or_email"))

        password = attrs.get("password")
        user_obj = User.objects.filter(lookup).first()
        employer_id = attrs.get("employer_id")
    
            
        if not user_obj:
            msg = 'Account with this credentials does not exists'
            raise serializers.ValidationError(msg)

        if not user_obj.is_active:
            msg = _('User account is disabled. Have you confirmed your email?')
            raise serializers.ValidationError(msg)

        if employer_id:
            employer = Profile.objects.filter(Q(employer=employer_id, user=user_obj.id) | Q(other_employers__id=employer_id, user=user_obj.id))
            if not employer:
                msg = 'Account with this employer id does not exists'
                raise serializers.ValidationError(msg)
                
        credentials = {
            'username': user_obj.username,
            'password': password
        }

        user = authenticate(**credentials)

        if not user:
            msg = 'Unable to log in with provided credentials.'
            raise serializers.ValidationError(msg)

        payload = jwt_payload_handler(user=user)
        device_id = attrs.get("registration_id")

        if device_id is not None:
            with transaction.atomic():
                FCMDevice.objects.filter(registration_id=device_id).delete()
                device = FCMDevice(user=user, registration_id=device_id)
                device.save()
        
        

        return {
            'token': jwt_encode_handler(payload),
            'user': user,
            
        }
    def get_active_subscription(self, employer):
        _sub = employer.employersubscription_set.filter(status='ACTIVE').first()
        print('_sub serializer is non', _sub)

        if _sub is not None:
            serializer = SubscriptionSerializer(_sub.subscription, many=False)
            print('_sub serializer', serializer.data)
            return serializer.data
        else:
            return None

class UserRegisterSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    account_type = serializers.CharField(required=True, write_only=True)
    
    # these three are only added when creating a new company
    business_name = serializers.CharField(required=False, write_only=True)
    business_website = serializers.CharField(required=False, write_only=True)
    about_business = serializers.CharField(required=False, write_only=True)

    employer = serializers.PrimaryKeyRelatedField(required=False, many=False, write_only=True,queryset=Employer.objects.all())
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=50)
    last_name = serializers.CharField(required=True, max_length=50)
    phone_number = serializers.CharField(required=False, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    city = serializers.CharField(required=False, max_length=100)
    profile_city = serializers.CharField(required=False, max_length=100)
    
    # these are added when created an account thru invitation
    employer_role = serializers.CharField(required=False,max_length=20, write_only=True)
    validate_email = serializers.BooleanField(required=False, allow_null=True, write_only=True)

    def validate(self, data):
        user = User.objects.filter(email=data["email"]).first()
        if user is not None:
            profile = Profile.objects.filter(user=user).first()
            if profile is not None:
                raise serializers.ValidationError("This email already exist.")

        if len(data["email"]) > 150:
            raise serializers.ValidationError(
                "You email cannot contain more than 150 characters")

        if len(data["password"]) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if data["password"].lower() == data["password"]:
            raise serializers.ValidationError("Password must contain at least one uppercase letter")

        if len(data["first_name"]) == 0 or len(data["last_name"]) == 0:
            raise serializers.ValidationError(
                "Your first and last names must not be empty")

        if data['account_type'] not in ('employer', 'employee'):
            raise serializers.ValidationError(
                "Account type can only be employer or employee")
        if data['account_type'] == 'employer' and EMPLOYER_REGISTRATION_DEACTIVATED == 'TRUE':
            raise serializers.ValidationError("Company registration is disabled")
        
        if 'validate_email' in data:
            if data['validate_email']: 
                raise serializers.ValidationError("Email is valid")
            else: 
                data.pop('validate_email')

        # validate creation of new employer
        if data['account_type'] == 'employer' and ('employer' not in data or data['employer'] is None):
            if data['business_name'] is None:
                raise serializers.ValidationError("You need to specify the business name or the employer id")
            if data['business_website'] is None:
                raise serializers.ValidationError("You need to specify the business website or the employer id")
            if data['about_business'] is None:
                raise serializers.ValidationError("You need to specify the business description or the employer id")
        return data

    def create(self, validated_data):
        
        account_type = validated_data.pop('account_type', None)
        employer = validated_data.pop('employer', None)
        city = validated_data.pop('city', None)
        business_name = validated_data.pop('business_name', None)
        phone_number = validated_data.pop('phone_number', None)
        business_website = validated_data.pop('business_website', None)
        about_business = validated_data.pop('about_business', None)
        profile_city = validated_data.pop('profile_city', None)
        employer_role = validated_data.pop('employer_role', None)
        
        # @TODO: Use IP address to get the initial address,
        #        latitude and longitud.
        user = User.objects.filter(email=validated_data["email"]).first()
        
        if not user:
            user = User.objects.create(**{**validated_data, "username": validated_data["email"]})

        user.set_password(validated_data['password'])
        user.save()

        # #if there is a previous invite as an employer
        # previous_invite = JobCoreInvite.objects.all().filter(email=user.email, employer__isnull=False).last()
        # if previous_invite is not None and account_type is None:
        #     account_type = 'employer'
        #     employer = previous_invite.employer
        token = self.context.get("token")

        if account_type == 'employer':
            status = 'PENDING_EMAIL_VALIDATION'
            if token is None: 
                employer_role = 'ADMIN'
            if employer is None:
                args = {
                    "title": business_name,
                    "website": business_website,
                    "bio": about_business,
                }
                employer = Employer.objects.create(**args)
            # if the user is coming from an email link
            if token:
                employer_role = employer_role
                try:
                    data = jwt_decode_handler(token)
                except jwt.ExpiredSignatureError:
                    raise serializers.ValidationError(" - Token Expired. Please get a new one.")
                except jwt.InvalidTokenError:
                    raise serializers.ValidationError(" - Invalid Token.")

                if data['user_email'] == user.email:
                    status = 'ACTIVE'
                else: raise serializers.ValidationError(" - Please use the same email where you get this invitation from.") 

            Profile.objects.create(user=user, picture='', employer=employer, status=status, employer_role=employer_role)

            #Update jobcore invitation
            jobcore_invites = JobCoreInvite.objects.all().filter(email=user.email, employer=employer)

            jobcore_invites.update(status='ACCEPTED')
            # notifier.notify_email_validation(user, employer)

        elif account_type == 'employee':
            status = 'PENDING_EMAIL_VALIDATION'

            # if the user is coming from an email link
            token = self.context.get("token")
            if token:
                # example data: {'sender_id': 1, 'invite_id': 7, 'user_email': 'a+employee5@jobcore.co', 'exp': 1560364249, 'orig_iat': 1560363349}
                data = jwt_decode_handler(token)
                if data['user_email'] == user.email:
                    status = 'ACTIVE'

            emp = Employee.objects.filter(user__id=user.id).first()
            if emp is None:
                emp = Employee.objects.create(user=user)
                user.employee.save()

            # availably all week by default
            employee_actions.create_default_availablity(emp)

            # add the talent to all positions by default
            # employee_actions.add_default_positions(emp)

            Profile.objects.create(
                user=user,
                picture='https://res.cloudinary.com/hq02xjols/image/upload/v1560365062/static/default_profile' + str(
                    randint(1, 3)) + '.png', employee=emp, status=status, phone_number=phone_number or '',
                profile_city_id=profile_city, city=city)

            jobcore_invites = JobCoreInvite.objects.all().filter(email=user.email, employer__isnull=True)

            auth_actions.create_shift_invites_from_jobcore_invites(jobcore_invites, user.profile.employee)

            jobcore_invites.update(status='ACCEPTED')

            notifier.notify_employee_email_validation(user)
        # notifier.notify_email_validation(user)
        print('user serializer', user)
        return user

class ChangePasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    repeat_password = serializers.CharField(required=True)

    def validate(self, data):
        try:
            payload = jwt_decode_handler(data["token"])
        except jwt.ExpiredSignatureError:
            raise serializers.ValidationError("Token Expired. Please get a new one.")
        except jwt.InvalidTokenError:
            raise serializers.ValidationError("Invalid Token.")

        try:
            print(payload)
            User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

        if data['new_password'] != data['repeat_password']:
            raise serializers.ValidationError("Passwords don't match")

        return data

    def create(self, validated_data):
        try:
            payload = jwt_decode_handler(validated_data["token"])
        except DecodeError:
            raise serializers.ValidationError("Invalid token")

        user = User.objects.get(id=payload["user_id"])
        user.set_password(validated_data['new_password'])
        user.save()
        return user
