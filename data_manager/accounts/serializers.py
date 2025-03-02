from rest_framework import serializers
from .models import Account, AccountMember, Destination
from users.models import CustomUser, Role
from django.core.validators import URLValidator

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'created_at', 'updated_at']
        extra_kwargs = {'id': {'read_only': True}, 'created_at': {'read_only': True}, 'updated_at': {'read_only': True}}

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
        extra_kwargs = {'id': {'read_only': True}, 'created_at': {'read_only': True}, 'updated_at': {'read_only': True}, 'account': {'required': False}}

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        member = AccountMember.objects.create(**validated_data, created_by=user, updated_by=user)
        return member

class DestinationSerializer(serializers.ModelSerializer):
    url = serializers.URLField(validators=[URLValidator(message="Invalid URL format")])
    headers = serializers.JSONField(required=True)

    class Meta:
        model = Destination
        fields = ['id', 'url', 'http_method', 'headers', 'account', 'created_at', 'updated_at']
        extra_kwargs = {'id': {'read_only': True}, 'created_at': {'read_only': True}, 'updated_at': {'read_only': True}}

    def validate_headers(self, value):
        if not value or not isinstance(value, dict):
            raise serializers.ValidationError("Headers must be a non-empty dictionary")
        return value

    def validate_http_method(self, value):
        if value not in dict(Destination.HTTP_METHODS):
            raise serializers.ValidationError("Invalid HTTP method")
        return value

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        destination = Destination.objects.create(**validated_data, created_by=user, updated_by=user)
        return destination

    def update(self, instance, validated_data):
        instance.url = validated_data.get('url', instance.url)
        instance.http_method = validated_data.get('http_method', instance.http_method)
        instance.headers = validated_data.get('headers', instance.headers)
        instance.updated_by = self.context['request'].user
        instance.save()
        return instance