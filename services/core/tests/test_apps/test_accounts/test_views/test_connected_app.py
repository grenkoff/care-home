"""Tests of connecting an authenticator app by its code."""

import logging
from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client
from django.utils import timezone

from server.apps.accounts.logic.codes import Key
from server.apps.accounts.logic.constants import CODE_SECONDS

_PAGE: Final = '/en/second-factor/connect/'
_FIELD: Final = 'code'


def _code(key: str, shift: int = 0) -> str:
    """Gives the code of the key for the current step moved by a shift."""
    step = int(timezone.now().timestamp()) // CODE_SECONDS
    return Key(key).code(step + shift)


@pytest.mark.django_db
def test_valid_code_connects_the_app_and_signs_in(
    pending: Client,
    shown_key: str,
) -> None:
    response = pending.post(_PAGE, {_FIELD: _code(shown_key)}, follow=True)

    assert response.redirect_chain == [('/en/', HTTPStatus.FOUND)]
    assert 'Sign out' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize('shift', [5, -5])
def test_wrong_code_connects_nothing(
    pending: Client,
    shown_key: str,
    shift: int,
) -> None:
    response = pending.post(_PAGE, {_FIELD: _code(shown_key, shift)})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'This code is wrong or no longer valid.' in response.content.decode()
    assert 'Sign out' not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('shown_key')
@pytest.mark.parametrize(_FIELD, ['', '12345', 'abcdef', '١٢٣٤٥٦'])
def test_code_of_six_digits_is_required(pending: Client, code: str) -> None:
    response = pending.post(_PAGE, {_FIELD: code})

    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_key_is_never_logged(
    pending: Client,
    shown_key: str,
    caplog: pytest.LogCaptureFixture,
    capfd: pytest.CaptureFixture[str],
) -> None:
    with caplog.at_level(logging.DEBUG):
        pending.post(_PAGE, {_FIELD: _code(shown_key, 5)})
        pending.post(_PAGE, {_FIELD: _code(shown_key)})

    printed = capfd.readouterr()
    assert shown_key not in caplog.text + printed.out + printed.err
