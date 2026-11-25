"""Tests of codes that were used already and of codes guessed in a row."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client
from django.utils import timezone

from server.apps.accounts.logic.codes import Key
from server.apps.accounts.logic.constants import CODE_SECONDS

_FIELD: Final = 'code'
_SIGN_IN: Final = '/en/sign-in/'
_CODE_PAGE: Final = '/en/second-factor/'


def _code(key: str) -> str:
    """Gives the code of the key for the current step."""
    step = int(timezone.now().timestamp()) // CODE_SECONDS
    return Key(key).code(step)


@pytest.mark.django_db
def test_code_that_was_used_is_refused(pending: Client, connected_key: str) -> None:
    code = _code(connected_key)
    pending.post(_CODE_PAGE, {_FIELD: code})
    pending.post('/en/sign-out/')
    pending.post(
        _SIGN_IN,
        {'username': 'anna@example.test', 'password': 'a long secret'},
    )

    response = pending.post(_CODE_PAGE, {_FIELD: code})

    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('page', 'key'),
    [(_CODE_PAGE, 'connected_key'), ('/en/second-factor/connect/', 'shown_key')],
)
def test_five_wrong_codes_sign_out(
    pending: Client,
    request: pytest.FixtureRequest,
    page: str,
    key: str,
) -> None:
    request.getfixturevalue(key)

    answers = [pending.post(page, {_FIELD: '12345'}) for _ in range(5)]

    assert {answer.status_code for answer in answers[:-1]} == {HTTPStatus.BAD_REQUEST}
    assert answers[-1].status_code == HTTPStatus.FOUND
    assert pending.get(page)['Location'] == _SIGN_IN
