# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.core.validators import EmailValidator

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration and updates."""
    email = serializers.EmailField(validators=[EmailValidator(message="Invalid email format")])

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'role', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }

    def create(self, validated_data):
        request = self.context.get('request')
        # Check if user is authenticated; otherwise, set to None
        requesting_user = request.user if request and request.user.is_authenticated else None
        
        # Remove audit fields from validated_data to handle them manually
        validated_data.pop('created_by', None)
        validated_data.pop('updated_by', None)
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'admin')  # Default to admin for registration
        )
        # Set audit fields after creation
        user.created_by = requesting_user or user  # Self-reference if no requesting user
        user.updated_by = requesting_user or user
        user.save()
        
        Token.objects.create(user=user)
        return user

    def update(self, instance, validated_data):
        requesting_user = self.context['request'].user
        instance.email = validated_data.get('email', instance.email)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.role = validated_data.get('role', instance.role)
        instance.updated_by = requesting_user
        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField(validators=[EmailValidator(message="Invalid email format")])
    password = serializers.CharField(write_only=True)

class InviteUserSerializer(serializers.Serializer):
    """Serializer for inviting users."""
    email = serializers.EmailField(validators=[EmailValidator(message="Invalid email format")])