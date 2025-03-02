# destinations/models.py
from django.db import models
from django.utils import timezone
from users.models import CustomUser
from accounts.models import Account
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Destination(models.Model):
    HTTP_METHODS = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    )
    url = models.URLField(max_length=2000, db_index=True)
    http_method = models.CharField(max_length=10, choices=HTTP_METHODS)
    headers = models.JSONField(default=dict, blank=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='destinations', db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_destinations')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='updated_destinations')

    class Meta:
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['account', 'http_method']),
        ]

    def __str__(self):
        return f"{self.url} ({self.http_method}) - {self.account.name}"

class Log(models.Model):
    event_id = models.CharField(max_length=100, unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='logs')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='logs')
    received_timestamp = models.DateTimeField(default=timezone.now)
    processed_timestamp = models.DateTimeField(null=True, blank=True)
    received_data = models.JSONField()
    status = models.CharField(max_length=20, choices=(('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')), default='pending')

    class Meta:
        indexes = [
            models.Index(fields=['event_id']),
            models.Index(fields=['account', 'status']),
        ]

    def __str__(self):
        return f"Event {self.event_id} - {self.status}"

@receiver(post_delete, sender=Account)
def delete_account_destinations(sender, instance, **kwargs):
    instance.destinations.all().delete()