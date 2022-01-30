from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from graphene_django.rest_framework.mutation import SerializerMutation
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'password',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data) -> User:
        return User.objects.create_user(**validated_data)


class UserMutation(SerializerMutation):
    class Meta:
        serializer_class = UserSerializer
        model_operations = ['create', ]
        lookup_field = 'id'


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
        ]
