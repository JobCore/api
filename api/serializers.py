import datetime
import json
from oauth2_provider import settings as outh2_settings
from rest_framework import permissions, serializers
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db.models import Q
from oauth2_provider.models import AccessToken
from django.contrib.auth.models import User
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from .models import *
from api.utils.email import send_email_message
from rest_framework_jwt.settings import api_settings

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

# Format Serializers
class ToTimestampField(serializers.Field):
    def to_representation(self, value):
        return value.timestamp() * 1000

class DatetimeFormatField(serializers.Field):
    def to_internal_value(self, value):
        return datetime.datetime.strptime(value, '%Y-%m-%d')

    def to_representation(self, value):
        return "{}-{}-{}T00:00".format(value.year, value.month, value.day)

class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email')

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'password')
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        user = User.objects.filter(email=data["email"])
        if user.exists():
            raise ValidationError("This email already exist.")
        return data

    def create(self, validated_data):
        user = super(UserRegisterSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        Profile.objects.create(user=user)
        user.profile.save()
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        exclude = ()

class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        exclude = ()

class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        exclude = ()

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        exclude = ()

class ProfileGetSerializer(serializers.ModelSerializer):
    user = UserGetSerializer()

    class Meta:
        model = Profile
        exclude = ()

class JobCoreInviteGetSerializer(serializers.ModelSerializer):
    sender = ProfileGetSerializer()

    class Meta:
        model = JobCoreInvite
        exclude = ()

class JobCoreInvitePostSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobCoreInvite
        exclude = ()
        
    def create(self, validated_data):
        # TODO: send email message not working
        send_email_message("invite_to_jobcore", "alejandro@bestmiamiweddings.com", {
            "SENDER": validated_data['sender'].user.first_name + ' ' + validated_data['sender'].user.last_name,
            "COMPANY": "Fetes & Events",
            "POSITION": "Server",
            "DATE": "July 21st"
        })
        return JobCoreInvite(**validated_data)

class ShiftInviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShiftInvite
        exclude = ()
        
    def create(self, validated_data):
        # TODO: send email message not working
        send_email_message("invite_to_shift", "alejandro@bestmiamiweddings.com", {
            "SENDER": validated_data['sender'].user.first_name + ' ' + validated_data['sender'].user.last_name,
            "COMPANY": validated_data['sender'].user.profile.employer.title,
            "POSITION": validated_data['shift'].position.title,
            "DATE": validated_data['shift'].date.strftime('%m/%d/%Y')
        })
        return ShiftInvite(sender=validated_data['sender'], shift=validated_data['shift'], employee=validated_data['employee'])

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ()

class EmployerGetSerializer(serializers.ModelSerializer):
    badges = BadgeSerializer(many=True)

    class Meta:
        model = Employer
        exclude = ()

class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        exclude = ()

class FavoriteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteList
        exclude = ()

class EmployeeGetSerializer(serializers.ModelSerializer):
    profile = ProfileGetSerializer()
    badges = BadgeSerializer(many=True)
    positions = PositionSerializer(many=True)
    favoritelist_set = FavoriteListSerializer(many=True)

    class Meta:
        model = Employee
        exclude = ()

class EmployeeSerializer(serializers.ModelSerializer):
    favoritelist_set = serializers.PrimaryKeyRelatedField(many=True, queryset=FavoriteList.objects.all())
    
    class Meta:
        model = Employee
        exclude = ()

class ShiftSerializer(serializers.ModelSerializer):
    date = DatetimeFormatField(required=False)

    class Meta:
        model = Shift
        exclude = ()

    def is_changing_status(self, shift, new_status=None):
        if self.validated_data['status'] != shift.status:
            if new_status is None:
                return True
            else:
                return (self.validated_data['status'] == new_status)
        else:
            return False

    def can_be_updated(self, shift):
        # It will be or remain a draft
        if self.validated_data['status'] == 'DRAFT':
            return True
        # I was a draft but it will become something else
        elif shift.status == 'DRAFT':
            return True
        else:
            return False
            
    # def update(self, instance, validated_data):
    #     #re-implement the update and notify whomever
    #     return instance
            
class ShiftPostSerializer(serializers.ModelSerializer):
    date = DatetimeFormatField()

    class Meta:
        model = Shift
        exclude = ()
        
class FavoriteListGetSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer()
    employees = EmployeeGetSerializer(many=True)

    class Meta:
        model = FavoriteList
        exclude = ()

class ShiftGetSerializer(serializers.ModelSerializer):
    venue = VenueSerializer(read_only=True)
    position = PositionSerializer(read_only=True)
    candidates = EmployeeGetSerializer(many=True, read_only=True)
    employees = EmployeeGetSerializer(many=True, read_only=True)
    required_badges = BadgeSerializer(many=True, read_only=True)
    allowed_from_list = FavoriteListGetSerializer(many=True, read_only=True)
    date = ToTimestampField(read_only=True)

    class Meta:
        model = Shift
        exclude = ()

class ApplicantGetSerializer(serializers.ModelSerializer):
    employee = EmployeeGetSerializer()
    shift = ShiftGetSerializer()

    class Meta:
        model = ShiftApplication
        exclude = ()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False, write_only=True)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ('id','username', 'first_name',
                  'last_name', 'email', 'password', 'profile')

    def validate(self, data):
        if 'email' in data:
            email = data["email"]
            user = User.objects.filter(email=email)
            if user.exists():
                raise ValidationError("This email is already in use.")
        elif 'username' in data:
            username = data["username"]
            user = User.objects.filter(username=username)
            if user.exists():
                raise ValidationError("This username is already in use.")
        return data

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserLoginSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(required=False)
    employer = EmployerSerializer(required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password',
                  'token', 'employer', 'employee')
        extra_kwargs = {"password": {"write_only": True}}

class CustomJWTSerializer(JSONWebTokenSerializer):
    username_field = 'username_or_email'
    user = UserLoginSerializer(required=False)

    def validate(self, attrs):
    
        password = attrs.get("password")
        user_obj = User.objects.filter(email=attrs.get("username_or_email")).first() or User.objects.filter(username=attrs.get("username_or_email")).first()
        if user_obj is not None:
            credentials = {
                'username':user_obj.username,
                'password': password
            }
            if all(credentials.values()):
                user = authenticate(**credentials)
                if user:
                    if not user.is_active:
                        msg = _('User account is disabled.')
                        raise serializers.ValidationError(msg)

                    payload = jwt_payload_handler(user)
                    profile = Profile.objects.get(user_id=user.id)
                    
                    # try:
                    #     userDic['employee_id'] = profile.employee.id
                    # except Employee.DoesNotExist:
                    #     try:
                    #         userDic["employer_id"] = profile.employer.id
                    #     except Employee.DoesNotExist:
                    #         msg = _('User is not an employer nor employee')
                    #         raise serializers.ValidationError(msg)
                        
                    return {
                        'token': jwt_encode_handler(payload),
                        'user': user
                    };
                else:
                    msg = _('Unable to log in with provided credentials.')
                    raise serializers.ValidationError(msg)

            else:
                msg = _('Must include "{username_field}" and "password".')
                msg = msg.format(username_field=self.username_field)
                raise serializers.ValidationError(msg)

        else:
            msg = _('Account with this email/username does not exists')
            raise serializers.ValidationError(msg)
            