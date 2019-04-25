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

    # def validate(self, validated_data):

    #     print("34534534")
    #     if "latitude" in validated_data:
    #         validated_data["latitude"] = round(validated_data["latitude"], 6)
    #     if "longitude" in validated_data:
    #         validated_data["longitude"] = round(validated_data["longitude"], 6)

    #     ##data = super(ProfileSerializer, self).validate(data)
    #     return data

    # def update(self, instance, validated_data):
    #     if "latitude" in validated_data:
    #         validated_data["latitude"] = round(validated_data["latitude"], 6)
    #     if "longitude" in validated_data:
    #         validated_data["longitude"] = round(validated_data["latitude"], 6)

    #     instance = super(UserSerializer, self).update(instance, validated_data)

    #     return instance
