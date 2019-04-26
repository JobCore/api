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


class FavoriteListSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteList
        fields = ('id', 'title', 'employer')
