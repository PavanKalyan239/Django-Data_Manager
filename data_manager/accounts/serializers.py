# accounts/serializers.py
from rest_framework import serializers
from .models import Account, AccountMember
from users.models import CustomUser, Role

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'app_secret_token', 'created_at', 'updated_at']  # Added app_secret_token
        extra_kwargs = {
            'id': {'read_only': True},
            'app_secret_token': {'read_only': True},  # Prevent manual edits
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        account = Account.objects.create(name=validated_data['name'], created_by=user, updated_by=user)
        AccountMember.objects.create(account=account, user=user, role=Role.objects.get(role_name='Admin'), created_by=user, updated_by=user)
        return account

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.updated_by = self.context['request'].user
        instance.save()
        return instance

class AccountMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    role_name = serializers.CharField(source='role.role_name', read_only=True)

    class Meta:
        model = AccountMember
        fields = ['id', 'account', 'user', 'role', 'user_email', 'role_name', 'created_at', 'updated_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'account': {'required': False}
        }

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        member = AccountMember.objects.create(**validated_data, created_by=user, updated_by=user)
        return member