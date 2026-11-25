"""Tests of the pages of the second factor in Russian."""

import pytest
from django.test import Client


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('key', 'address', 'phrase'),
    [
        ('shown_key', '/ru/second-factor/connect/', 'Подключите приложение'),
        ('connected_key', '/ru/second-factor/', 'шестизначный код'),
    ],
)
def test_pages_speak_russian(
    pending: Client,
    request: pytest.FixtureRequest,
    key: str,
    address: str,
    phrase: str,
) -> None:
    request.getfixturevalue(key)

    assert phrase in pending.get(address).content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('connected_key')
def test_wrong_code_speaks_russian(pending: Client) -> None:
    page = pending.post('/ru/second-factor/', {'code': '12345'}).content.decode()

    assert 'Введите шесть цифр' in page
