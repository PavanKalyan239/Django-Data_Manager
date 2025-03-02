from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.core.validators import EmailValidator
from accounts.models import Account, AccountMember
from users.models import Role

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator(message="Invalid email format")])

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }

    def create(self, validated_data):
        request = self.context.get('request')
        requesting_user = request.user if request and request.user.is_authenticated else None
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.created_by = requesting_user or user
        user.updated_by = requesting_user or user
        user.save()
        
        Token.objects.create(user=user)
        
        if not AccountMember.objects.filter(user=user).exists():
            account = Account.objects.create(
                name=f"{user.email}'s Account",
                created_by=user,
                updated_by=user
            )
            AccountMember.objects.create(
                account=account,
                user=user,
                role=Role.objects.get(role_name='Admin'),
                created_by=user,
                updated_by=user
            )
        
        return user

    def update(self, instance, validated_data):
        requesting_user = self.context['request'].user
        instance.email = validated_data.get('email', instance.email)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.updated_by = requesting_user
        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[EmailValidator(message="Invalid email format")])
    password = serializers.CharField(write_only=True)

class InviteUserSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[EmailValidator(message="Invalid email format")])
    account_id = serializers.IntegerField(required=True)

    def validate_account_id(self, value):
        if not Account.objects.filter(id=value).exists():
            raise serializers.ValidationError("Account does not exist")
        return value