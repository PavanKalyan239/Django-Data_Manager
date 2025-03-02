from django.db import models
from django.utils import timezone
from users.models import CustomUser, Role
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Account(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_accounts')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='updated_accounts')

    def __str__(self):
        return self.name

class AccountMember(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='members', db_index=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='memberships', db_index=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='account_members')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_members')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='updated_members')

    class Meta:
        unique_together = ('account', 'user')
        indexes = [models.Index(fields=['account', 'user'])]

    def __str__(self):
        return f"{self.user.email} - {self.account.name} ({self.role.role_name})"

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

    def __str__(self):
        return f"{self.url} ({self.http_method}) - {self.account.name}"

@receiver(post_delete, sender=Account)
def delete_account_destinations(sender, instance, **kwargs):
    instance.destinations.all().delete()