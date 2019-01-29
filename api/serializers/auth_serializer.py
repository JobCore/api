import sys
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework import serializers
from api.serializers import employer_serializer
from api.actions import employee_actions
from api.models import User, Employer, Employee, Profile, ShiftInvite, JobCoreInvite, FCMDevice
from django.contrib.auth import authenticate
from api.utils import notifier
from jobcore.settings import STATIC_URL
from rest_framework_jwt.settings import api_settings
import datetime
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
    
        password = attrs.get("password")
        user_obj = User.objects.filter(email=attrs.get("username_or_email")).first() or User.objects.filter(username=attrs.get("username_or_email")).first()
        if user_obj is not None:
            credentials = {
                'username': user_obj.username,
                'password': password
            }
            if all(credentials.values()):
                user = authenticate(**credentials)
                if user:
                    if not user.is_active:
                        msg = _('User account is disabled.')
                        raise serializers.ValidationError(msg)

                    # exp = attrs.get("expiration_days", None)
                    # if exp is not None:
                    #     exp = datetime.datetime.utcnow() + datetime.timedelta(days=int(exp))

                    payload = jwt_payload_handler(user=user)
                    profile = Profile.objects.get(user_id=user.id)
                    
                    device_id = attrs.get("registration_id")
                    if device_id is not None:
                        FCMDevice.objects.filter(registration_id=device_id).delete()

                        device = FCMDevice(user=user, registration_id=device_id)
                        device.save()
                    
                    return {
                        'token': jwt_encode_handler(payload),
                        'user': user
                    };
                else:
                    msg = 'Unable to log in with provided credentials.'
                    raise serializers.ValidationError(msg)

            else:
                msg = 'Must include "{username_field}" and "password".'
                msg = msg.format(username_field=self.username_field)
                raise serializers.ValidationError(msg)

        else:
            msg = 'Account with this email does not exists'
            raise serializers.ValidationError(msg)
            
class UserRegisterSerializer(serializers.ModelSerializer):
    account_type = serializers.CharField(required=True, write_only=True)
    employer = serializers.PrimaryKeyRelatedField(required=False, many=False, write_only=True, queryset=Employer.objects.all())
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'password', 'account_type', 'employer')
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        user = User.objects.filter(email=data["email"])
        if user.exists():
            raise ValidationError("This email already exist.")

        if len(data["email"]) > 150:
            raise ValidationError("You email cannot contain more than 150 characters")

        if len(data["first_name"]) == 0 or len(data["last_name"]) == 0:
            raise ValidationError("Your first and last names must not be empty")

        if data['account_type'] not in ('employer', 'employee'):
            raise ValidationError("Account type can only be employer or employee")
        elif data['account_type'] == 'employer':
            if 'employer' not in data:
                raise ValidationError("You need to specify the user employer id")
            
        return data

    def create(self, validated_data):
        account_type = validated_data['account_type']
        validated_data.pop('account_type', None)
        
        employer = None
        if 'employer' in validated_data:
            employer = validated_data['employer']
            validated_data.pop('employer', None)
            
        # @TODO: Use IP address to get the initial address, latitude and longitud.
            
        user = super(UserRegisterSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        
        try:
                
            if account_type == 'employer':
                Profile.objects.create(user=user, picture='', employer=employer)
                user.profile.save()
            
            elif account_type == 'employee':
                emp = Employee.objects.create(user=user)
                user.employee.save()
                
                # availably all week by default
                employee_actions.create_default_availablity(emp)
                
                # @TODO: if the user is comming from an invite it gets status=ACTIVE, it not it gets the default PENDING_EMAIL_VALIDATION
                profile = Profile.objects.create(user=user, picture='', employee=emp, status='ACTIVE')
                user.profile.save()
            
            notifier.notify_email_validation(user)
        except:
            user.delete()
            print("Error:", sys.exc_info()[0])
            raise
        
        # check for pending invites
        jobcore_invites = JobCoreInvite.objects.all().filter(email=user.email)
        for invite in jobcore_invites:
            notifier.notify_invite_accepted(invite)
            invite = ShiftInvite(sender=invite.sender, shift=invite.shift, employee=user.profile.employee)
            invite.save()
        jobcore_invites.delete()
        
        return user

class ChangePasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    repeat_password = serializers.CharField(required=True)
    
    def validate(self, data):
        payload = jwt_decode_handler(data["token"])
        try:
            user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            raise ValidationError("User does not exist.")
        
        if data['new_password'] != data['repeat_password']:
            raise ValidationError("Passwords don't match")
        
        return data
        
    def create(self, validated_data):
        payload = jwt_decode_handler(validated_data["token"])
        user = User.objects.get(id=payload["user_id"])
        user.set_password(validated_data['new_password'])
        user.save()
        return user