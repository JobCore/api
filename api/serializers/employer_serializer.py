from rest_framework import serializers
from api.models import Employer, Shift,EmployerUsers, Profile, Payrates, SubscriptionPlan, Position, Employee, User
from datetime import datetime
from django.utils import timezone
from api.serializers.badge_serializers import BadgeGetSmallSerializer
# from api.serializers.other_serializer import SubscriptionSerializer
from api.serializers.position_serializer import PositionSmallSerializer

#
# MAIN
#


class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        exclude = ()

class OtherEmployerSerializer(serializers.ModelSerializer):
    profile_id = serializers.ReadOnlyField(source='profile.id')

    class Meta:
        model = EmployerUsers
        fields = ('employer_role', 'profile_id', 'employer')


class OtherProfileSerializer(serializers.ModelSerializer):
    other_employers = OtherEmployerSerializer(source='company_users_employer', many=True)

    class Meta:
        model = Profile
        fields = ('other_employers',)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        exclude = ()
        
class EmployerGetSerializer(serializers.ModelSerializer):
    badges = BadgeGetSmallSerializer(many=True)
    active_subscription = serializers.SerializerMethodField()

    class Meta:
        model = Employer
        fields = ('id','title', 'picture', 'bio', 'website', 'bio', 'response_time', 'rating',
            'total_ratings', 'badges', 'status', 'automatically_accept_from_favlists',
            'payroll_period_starting_time', 'payroll_period_length', 'payroll_period_type',
            'last_payment_period', 'maximum_clockin_delta_minutes', 
            'maximum_clockout_delay_minutes', 'created_at', 'updated_at','active_subscription')

    def get_active_subscription(self, employer):
        _sub = employer.employersubscription_set.filter(status='ACTIVE').first()
        if _sub is not None:
            serializer = SubscriptionSerializer(_sub.subscription, many=False)
            return serializer.data
        else:
            return None



class EmployerPayratePostSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = Payrates
        fields = ('employer', 'employee', 'position', 'hourly_rate') 

    employee = serializers.SerializerMethodField()

    def get_employee(self, data):
        return {
            'first_name': data.employee.user.first_name,
            'last_name': data.employee.user.last_name,
            'picture': data.employee.user.profile.picture,
            'employee': data.employee.id
        }
    def validate(self, data):
        data = super(EmployerPayratePostSerializer, self).validate(data)
        if 'position' in data and (data['position'] == '' or data['position'] == 0):
            raise serializers.ValidationError('Position cannot be empty.')
        if 'hourly_rate' in data and (data['hourly_rate'] == '' or data['hourly_rate'] == 0):
            raise serializers.ValidationError('Hourly rate cannot be empty or equal to 0.')
        if 'employee' in data and (data['employee'] == '' or data['employee'] == 0):
            raise serializers.ValidationError('Please select an employee')

        payrate = Payrates.objects.filter(employer=data["employer"], employee=data["employee"], position=data['position']).first()
        if payrate is not None:
            raise serializers.ValidationError("This payrate already exists.")

        return data
class EmployerPayratePutSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payrates
        fields = ('id','employer', 'employee', 'position', 'hourly_rate') 
    employee = serializers.SerializerMethodField()

    def get_employee(self, data):
        return {
            'first_name': data.employee.user.first_name,
            'last_name': data.employee.user.last_name,
            'picture': data.employee.user.profile.picture,
            'employee': data.employee.id
        }
    def validate(self, data):

        data = super(EmployerPayratePutSerializer, self).validate(data)
        if 'position' in data and (data['position'] == '' or data['position'] == 0):
            raise serializers.ValidationError('Position cannot be empty.')
        if 'hourly_rate' in data and (data['hourly_rate'] == '' or data['hourly_rate'] == 0):
            raise serializers.ValidationError('Hourly rate cannot be empty or equal to 0.')



        return data

class EmployerPayrateGetSmallSerializer(serializers.ModelSerializer):
    employer = EmployerGetSmallSerializer(many=False, read_only=True)
    position = PositionSmallSerializer(many=False, read_only=True)
    employee = serializers.SerializerMethodField()

    def get_employee(self, data):
        return {
            'first_name': data.employee.user.first_name,
            'last_name': data.employee.user.last_name,
            'picture': data.employee.user.profile.picture,
            'employee': data.employee.id
        }

    class Meta:
        model = Payrates
        fields = ('id','employer', 'position', 'hourly_rate', 'employee')

class EmployerSerializer(serializers.ModelSerializer):
    retroactive = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = Employer
        exclude = (
            'rating', 'total_ratings'
            )

    def validate(self, data):

        data = super(EmployerSerializer, self).validate(data)

        if 'title' in data and data['title'] == '':
            raise serializers.ValidationError('Company title cannot by empty')

        if 'bio' in data and data['bio'] == '':
            raise serializers.ValidationError('Company bio cannot by empty')

        return data

    def update(self, employer, validated_data):
  
        employer = super(EmployerSerializer, self).update(employer, validated_data)

        # update shifts settings retroactively
        if 'retroactive' in validated_data and validated_data['retroactive'] == True:
            NOW = datetime.now(tz=timezone.utc)
            Shift.objects.filter(ending_at__gte=NOW, employer__id=employer.id).update(
                maximum_clockin_delta_minutes=validated_data['maximum_clockin_delta_minutes'], 
                maximum_clockout_delay_minutes=validated_data['maximum_clockout_delay_minutes']
            )

        return employer
