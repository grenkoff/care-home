"""Tests of the pages of the second factor in Russian."""

from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from server.apps.accounts.models import Authenticator


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


@pytest.mark.django_db
def test_locked_codes_speak_russian(pending: Client, connected_key: str) -> None:
    Authenticator.objects.filter(key=connected_key).update(
        locked_until=timezone.now() + timedelta(minutes=15),
    )

    page = pending.post('/ru/second-factor/', {'code': '123456'}).content.decode()

    assert 'Слишком много неверных кодов. Попробуйте снова через 15 минут.' in page
