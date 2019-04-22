from django.contrib.auth import authenticate
from django.db.models import Q
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework import serializers

from jwt.exceptions import DecodeError

from api.serializers import employer_serializer
from api.actions import employee_actions, auth_actions
from api.models import (
    User, Employer, Employee, Profile,
    JobCoreInvite, FCMDevice)
from api.utils import notifier

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


class UserLoginSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(required=False)
    employer = employer_serializer.EmployerSerializer(required=False)
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

    def validate(self, attrs):
        lookup = Q(email=attrs.get("username_or_email")) \
            | Q(username=attrs.get("username_or_email"))

        password = attrs.get("password")
        user_obj = User.objects.filter(lookup).first()

        if not user_obj:
            msg = 'Account with this credentials does not exists'
            raise serializers.ValidationError(msg)

        if not user_obj.is_active:
            msg = _('User account is disabled.')
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
            'user': user
        }


class UserRegisterSerializer(serializers.ModelSerializer):
    account_type = serializers.CharField(required=True, write_only=True)

    employer = serializers.PrimaryKeyRelatedField(
        required=False, many=False, write_only=True,
        queryset=Employer.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'password', 'account_type', 'employer')
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        user = User.objects.filter(email=data["email"])
        if user.exists():
            raise serializers.ValidationError("This email already exist.")

        print("user email: "+data["email"])
        if len(data["email"]) > 150:
            raise serializers.ValidationError(
                "You email cannot contain more than 150 characters")

        if len(data["first_name"]) == 0 or len(data["last_name"]) == 0:
            raise serializers.ValidationError(
                "Your first and last names must not be empty")

        if data['account_type'] not in ('employer', 'employee'):
            raise serializers.ValidationError(
                "Account type can only be employer or employee")
        elif data['account_type'] == 'employer':
            if 'employer' not in data:
                raise serializers.ValidationError(
                    "You need to specify the user employer id")

        return data

    def create(self, validated_data):
        account_type = validated_data['account_type']
        validated_data.pop('account_type', None)
        
        employer = None
        if 'employer' in validated_data:
            employer = validated_data['employer']
            validated_data.pop('employer', None)

        # @TODO: Use IP address to get the initial address,
        #        latitude and longitud.

        user = super(UserRegisterSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()

        if account_type == 'employer':
            
            Profile.objects.create(user=user, picture='', employer=employer)
            # user.profile.save()

        elif account_type == 'employee':
            
            emp = Employee.objects.create(user=user)
            user.employee.save()

            # availably all week by default
            employee_actions.create_default_availablity(emp)

            # @TODO: if the user is comming from an invite it gets
            #         status=ACTIVE, it not it gets the default
            #         PENDING_EMAIL_VALIDATION
            # we would have to receive the invitation token here or
            #         something like that.ç

            Profile.objects.create(
                user=user, picture='', employee=emp, status='ACTIVE')
            # user.profile.save()

            # Si te estas registrando como un empleado, debemos ver quien te
            # invito a la plataforma (JobCoreInvite),

            # si la(s) invitacion que te enviaron tienen shift asociados
            # debemos invitarte a esos shifts de una vez te registremos
            # (ShiftInvite).

            jobcore_invites = JobCoreInvite.objects.all().filter(
                email=user.email)

            auth_actions.create_shift_invites_from_jobcore_invites(
                jobcore_invites, user.profile.employee)

        notifier.notify_email_validation(user)

        return user


class ChangePasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    repeat_password = serializers.CharField(required=True)

    def validate(self, data):
        try:
            payload = jwt_decode_handler(data["token"])
        except DecodeError:
            raise serializers.ValidationError("Invalid token")

        try:
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
