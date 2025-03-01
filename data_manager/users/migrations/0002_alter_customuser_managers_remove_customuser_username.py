# users/migrations/0002_populate_roles.py (example filename)
from django.db import migrations

def populate_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.create(id=1, role_name='Admin')
    Role.objects.create(id=2, role_name='Normal user')

class Migration(migrations.Migration):
    dependencies = [('users', '0001_initial')]
    operations = [migrations.RunPython(populate_roles)]