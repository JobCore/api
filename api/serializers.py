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
from api.utils import notify
from rest_framework_jwt.settings import api_settings

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER

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
        
        notify.email_validation(user)
        
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
        invite = JobCoreInvite(**validated_data)
        invite.save()
        
        notify.jobcore_invite(invite)
        
        return invite

class ShiftInviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShiftInvite
        exclude = ()
        
    def create(self, validated_data):
        
        # TODO: send email message not working
        invite = ShiftInvite(sender=validated_data['sender'], shift=validated_data['shift'], employee=validated_data['employee'])
        invite.save()
        
        # TODO: send email message not working
        notify.shift_invite(invite)
        
        return invite

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
    allowed_from_list = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Shift
        exclude = ()
        
    def has_sensitive_updates(self,validated_data):
        non_sensitive_fields = ['application_restriction','minimum_allowed_rating','allowed_from_list','required_badges','rating']
        for key in validated_data:
            if key not in non_sensitive_data:
                return True
        
        return False
        
    def validate(self, data):
        shift = self.instance
        if data['status'] != 'DRAFT' and shift.status != 'DRAFT' and self.has_sensitive_updates(data):
            raise serializers.ValidationError('The shift can only be updated as a draft')
            
        return data
    
    # TODO: Validate that only draft shifts can me updated
    def update(self, shift, validated_data):
        
        # delete all accepeted employees
        if validated_data['status'] in ['DRAFT'] or shift.status in ['DRAFT']:
            ShiftInvite.objects.filter(shift=shift).delete()
            shift.employees.clear()
        
        # Sync employees
        if 'allowed_from_list' in validated_data:
            current_favlists = shift.allowed_from_list.all().values_list('id', flat=True)
            new_favlists = validated_data['allowed_from_list']
            for favlist in current_favlists:
                if favlist not in new_favlists:
                    shift.allowed_from_list.remove(favlist)
            for favlist in new_favlists:
                if favlist not in current_favlists:
                    shift.allowed_from_list.add(favlist)
            validated_data.pop('allowed_from_list')
            
        Shift.objects.filter(pk=shift.id).update(**validated_data)
        
        notify.shift_update(user=self.context['request'].user, shift=shift)

        return shift

class ShiftCandidatesSerializer(serializers.ModelSerializer):
    candidates = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Shift
        exclude = ()
        
    def validate(self, data):
        shift = Shift.objects.get(id=self.instance.id)
        if ('status' in data and data['status'] != 'OPEN') and shift.status != 'OPEN':
            raise serializers.ValidationError('This shift is not opened for applicants')
            
        return data

    def update(self, shift, validated_data):
        
        talents_to_notify = { "accepted": [], "rejected": [] }
        # Sync candidates
        if 'candidates' in validated_data:
            current_candidates = shift.candidates.all()
            new_candidates = Employee.objects.filter(id__in=validated_data['candidates'])
            for employee in current_candidates:
                if employee not in new_candidates:
                    ShiftApplication.objects.filter(employee__id=employee.id, shift__id=shift.id).delete()
            for employee in new_candidates:
                if employee not in current_candidates:
                    ShiftApplication.objects.create(employee=employee, shift=shift)
            validated_data.pop('candidates')
        
        
        # Sync employees
        if 'employees' in validated_data:
            current_employees = shift.employees.all()
            new_employees = validated_data['employees']
            for employee in current_employees:
                if employee not in new_employees:
                    talents_to_notify["rejected"].append(employee)
                    shift.employees.remove(employee.id)
            for employee in new_employees:
                if employee not in current_employees:
                    talents_to_notify["accepted"].append(employee)
                    shift.employees.add(employee.id)
            validated_data.pop('employees')
            
        notify.shift_candidate_update(user=self.context['request'].user, shift=shift, talents_to_notify=talents_to_notify)

        return shift
            
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
        fields = ('id','username', 'first_name', 'is_active',
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
    token = serializers.CharField(read_only=True)

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
                    msg = 'Unable to log in with provided credentials.'
                    raise serializers.ValidationError(msg)

            else:
                msg = 'Must include "{username_field}" and "password".'
                msg = msg.format(username_field=self.username_field)
                raise serializers.ValidationError(msg)

        else:
            msg = 'Account with this email/username does not exists'
            raise serializers.ValidationError(msg)
            