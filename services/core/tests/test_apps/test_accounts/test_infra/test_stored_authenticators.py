"""Tests of the authenticator apps kept in the database."""

import uuid
from typing import Final

import pytest
from django.utils import timezone

from server.apps.accounts.infra.authenticators import StoredAuthenticators
from server.apps.accounts.logic.errors import WrongCodeError
from server.apps.accounts.models import User

_KEY: Final = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'


@pytest.mark.django_db
def test_app_of_a_user_is_connected_once() -> None:
    user = User.objects.create_user(username='anna@example.test')
    StoredAuthenticators().connect(user.pk, _KEY, 1)

    with pytest.raises(WrongCodeError):
        StoredAuthenticators().connect(user.pk, _KEY, 2)


@pytest.mark.django_db
def test_code_of_a_user_without_an_app_is_wrong() -> None:
    with pytest.raises(WrongCodeError):
        StoredAuthenticators().use(uuid.uuid7(), '287082', timezone.now())
