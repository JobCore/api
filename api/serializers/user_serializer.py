from api.models import User, JobCoreInvite, Profile
from rest_framework import serializers

class ProfileGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('picture','id', 'bio', 'employer', 'employee')

class UserGetTinySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name','last_name', 'email')

class UserGetSmallSerializer(serializers.ModelSerializer):
    profile = ProfileGetSmallSerializer(many=False)
    
    class Meta:
        model = User
        fields = ('first_name','last_name', 'email', 'profile')

class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email')

class UserUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        exclude = ('id',)
        extra_kwargs = {
            'id': {'read_only': True},
            'email': {'read_only': True},
            'password': {'read_only': True},
            'profile': {'read_only': True},
        }

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False, write_only=True)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    profile = ProfileGetSmallSerializer(read_only=True)

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