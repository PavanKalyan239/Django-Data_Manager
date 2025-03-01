# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'user')
        )
        Token.objects.create(user=user)
        return user

class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class InviteUserSerializer(serializers.Serializer):
    """Serializer for inviting users."""
    email = serializers.EmailField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            return value  # Allow existing users
        return value