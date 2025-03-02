# accounts/migrations/0005_auto_20250302_1209.py
from django.db import migrations
import uuid

def populate_app_secret_token(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    for account in Account.objects.all():
        account.app_secret_token = uuid.uuid4()
        account.save()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0004_account_app_secret_token'),
    ]
    operations = [
        migrations.RunPython(populate_app_secret_token),
    ]