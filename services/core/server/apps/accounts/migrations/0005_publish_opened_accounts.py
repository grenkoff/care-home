from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0004_authenticator'),
        ('outbox', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
