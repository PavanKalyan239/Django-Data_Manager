# destinations/serializers.py
from rest_framework import serializers
from django.core.validators import URLValidator
from .models import Destination, Log

class DestinationSerializer(serializers.ModelSerializer):
    url = serializers.URLField(validators=[URLValidator(message="Invalid URL format")])
    headers = serializers.JSONField(required=True)
    http_method = serializers.ChoiceField(choices=Destination.HTTP_METHODS)

    class Meta:
        model = Destination
        fields = ['id', 'url', 'http_method', 'headers', 'account', 'created_at', 'updated_at', 'created_by', 'updated_by']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'created_by': {'read_only': True},
            'updated_by': {'read_only': True},
            'account': {'required': False}
        }

    def validate_headers(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("Headers must be a non-empty dictionary")
        return value

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ['event_id', 'account', 'destination', 'received_timestamp', 'processed_timestamp', 'received_data', 'status']
        extra_kwargs = {
            'account': {'read_only': True},
            'destination': {'read_only': True},
            'received_timestamp': {'read_only': True},
            'processed_timestamp': {'read_only': True}
        }