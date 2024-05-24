# myapp/migrations/0007_set_default_endpoint.py
from django.db import migrations

def set_default_endpoint(apps, schema_editor):
    Endpoint = apps.get_model('myapp', 'Endpoint')
    Event = apps.get_model('myapp', 'Event')
    default_endpoint = Endpoint.objects.get(id=1)
    Event.objects.filter(endpoint__isnull=True).update(endpoint=default_endpoint)

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_auto_20240524_0235'),  # Replace with your actual latest migration name
    ]

    operations = [
        migrations.RunPython(set_default_endpoint),
    ]
