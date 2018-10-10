from rest_framework import serializers
from api.models import Profile, User

class UserGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name','last_name', 'email', 'profile')

class ProfileGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('picture','id', 'bio')
        
class ProfileGetSerializer(serializers.ModelSerializer):
    user = UserGetSmallSerializer()

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