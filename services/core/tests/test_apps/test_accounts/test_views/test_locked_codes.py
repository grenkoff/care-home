"""Tests of the lock on the codes of an account after wrong ones."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client
from django.utils import timezone

from server.apps.accounts.logic.codes import Key
from server.apps.accounts.logic.constants import CODE_SECONDS

_PAGE: Final = '/en/second-factor/'
_FIELD: Final = 'code'


def _code(key: str, shift: int = 0) -> str:
    """Gives the code of the key for the current step moved by a shift."""
    step = int(timezone.now().timestamp()) // CODE_SECONDS
    return Key(key).code(step + shift)


@pytest.mark.django_db
def test_codes_lock_after_five_wrong_ones(
    pending: Client,
    connected_key: str,
) -> None:
    wrong = _code(connected_key, 5)
    [pending.post(_PAGE, {_FIELD: wrong}) for _ in range(5)]
    pending.post(
        '/en/sign-in/',
        {'username': 'anna@example.test', 'password': 'a long secret'},
    )

    response = pending.post(_PAGE, {_FIELD: _code(connected_key)})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'Too many wrong codes. Try again in 15 minutes.' in (
        response.content.decode()
    )
