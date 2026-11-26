"""Tests of the accounts that other modules find by e-mail."""

import pytest

from server.apps.accounts.infra.accounts import StoredAccounts
from server.apps.accounts.models import User
from server.apps.accounts.public.accounts import UnknownAccountError


@pytest.mark.django_db
def test_finds_the_account_of_an_email() -> None:
    anna = User.objects.create_user(username='anna@example.test')

    assert StoredAccounts().identified('Anna@Example.TEST') == anna.pk


@pytest.mark.django_db
def test_refuses_an_email_without_an_account() -> None:
    User.objects.create_user(username='anna@example.test')

    with pytest.raises(UnknownAccountError):
        StoredAccounts().identified('boris@example.test')
