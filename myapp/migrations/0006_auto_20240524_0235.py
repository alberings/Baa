# myapp/migrations/0006_auto_20240524_0235.py
from django.db import migrations, models

def set_default_endpoint(apps, schema_editor):
    Endpoint = apps.get_model('myapp', 'Endpoint')
    Event = apps.get_model('myapp', 'Event')
    default_endpoint = Endpoint.objects.get(id=1)
    Event.objects.filter(endpoint__isnull=True).update(endpoint=default_endpoint)

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_remove_event_user_endpoint_event_endpoint'),  # Replace with your actual latest migration name
    ]

    operations = [
        migrations.RunPython(set_default_endpoint),
    ]
