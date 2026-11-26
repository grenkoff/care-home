"""Tests of the migration that publishes the accounts opened before the facts."""

import pytest
from django.utils import timezone
from django_test_migrations.migrator import Migrator

from server.apps.accounts.public.events import ACCOUNT_OPENED


@pytest.mark.django_db
def test_publishes_every_account_opened_by_an_invitation(migrator: Migrator) -> None:
    old = migrator.apply_initial_migration([
        ('accounts', '0004_authenticator'),
        ('outbox', '0001_initial'),
    ])
    users = old.apps.get_model('accounts', 'User').objects
    anna = users.create(username='anna@example.test')
    users.create(username='staff@example.test', is_staff=True)
    old.apps.get_model('accounts', 'Invitation').objects.create(
        email='anna@example.test',
        digest='digest of anna',
        expires_at=timezone.now(),
        accepted_at=timezone.now(),
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
