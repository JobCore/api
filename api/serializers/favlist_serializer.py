from api.models import FavoriteList, Employee
from api.serializers import user_serializer
from rest_framework import serializers


class EmployeeGetSmallSerializer(serializers.ModelSerializer):
    user = user_serializer.UserGetSmallSerializer(many=False)

    class Meta:
        model = Employee
        exclude = ()


class FavoriteListGetSerializer(serializers.ModelSerializer):
    employees = EmployeeGetSmallSerializer(many=True)

    class Meta:
        model = FavoriteList
        exclude = ('employer',)


class FavoriteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteList
        exclude = ()

    def validate(self, data):

        if 'title' in data and data['title'] == '':
            raise serializers.ValidationError('The favorite list needs a title')

        return data

class FavoriteListPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteList
        exclude = ()

    def validate(self, data):

        if 'title' not in data or data['title'] == '':
            raise serializers.ValidationError('The favorite list needs a title')

        return data

class FavoriteListSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteList
        fields = ('id', 'title', 'employer')
