from rest_framework import serializers
from api.models import Profile, User, Employer, Employee, Badge


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ('id', 'title', 'image_url')


class EmployeeGetTinySerializer(serializers.ModelSerializer):
    badges = BadgeSerializer(many=True)

    class Meta:
        model = Employee
        exclude = ()


class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        exclude = ()


class UserGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('picture', 'id', 'bio', 'status')


class ProfileGetSerializer(serializers.ModelSerializer):
    user = UserGetSmallSerializer()
    employer = EmployerGetSmallSerializer()
    employee = EmployeeGetTinySerializer()

    class Meta:
        model = Profile
        exclude = ()


class ProfileSerializer(serializers.ModelSerializer):
    user = UserGetSmallSerializer(many=False, read_only=True)

    class Meta:
        model = Profile
        exclude = ()
        extra_kwargs = {
            'id': {'read_only': True},
            'employer': {'read_only': True},
            'employee': {'read_only': True},
            'status': {'read_only': True}
        }

    def validate_latitude(self, value):
        """
        Check that the latitud does not have more than 8 digits
        """
        return round(value, 6)

    def validate_longitude(self, value):
        """
        Check that the latitud does not have more than 8 digits
        """
        return round(value, 6)

    def validate_birth_date(self, value):
        """Check that birth_date is not null (can't be set as None)"""
        if not value:
            raise serializers.ValidationError("Birth date can't be set as Null")
        return value

    def validate_last_4dig_ssn(self, value):
        """Check that last_4dig_ssn is not null (can't be set as None)"""
        if not value:
            raise serializers.ValidationError("Last 4 digits ssn can't be set as Null")
        return value
