"""Tests of the migration that publishes the accounts opened before the facts."""

import pytest
from django_test_migrations.migrator import Migrator

from server.apps.accounts.public.events import ACCOUNT_OPENED


@pytest.mark.django_db
def test_publishes_every_account_opened_before(migrator: Migrator) -> None:
    old = migrator.apply_initial_migration([
        ('accounts', '0004_authenticator'),
        ('outbox', '0001_initial'),
    ])
    anna = old.apps.get_model('accounts', 'User').objects.create(
        username='anna@example.test',
    )

    new = migrator.apply_tested_migration(
        ('accounts', '0005_publish_opened_accounts'),
    )

    assert list(
        new.apps.get_model('outbox', 'Event').objects.values_list(
            'topic',
            'payload__account',
            'payload__email',
        ),
    ) == [(ACCOUNT_OPENED, str(anna.pk), 'anna@example.test')]
