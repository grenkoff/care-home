import uuid

from django.db import migrations

_ACCOUNT_OPENED = 'accounts.v1.account_opened'


def _opened(event, account, email):
    """Returns the pending fact that the account was opened for the e-mail."""
    fact = uuid.uuid7()
    return event(
        id=fact,
        topic=_ACCOUNT_OPENED,
        payload={'id': str(fact), 'account': str(account), 'email': email},
    )


def _publish(apps, schema_editor):
    """Writes the fact of each account opened before the facts existed."""
    event = apps.get_model('outbox', 'Event')
    accounts = apps.get_model('accounts', 'User').objects.order_by('pk')
    event.objects.bulk_create(
        _opened(event, account, email)
        for account, email in accounts.values_list('pk', 'username')
    )


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0004_authenticator'),
        ('outbox', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(_publish, migrations.RunPython.noop),
    ]
